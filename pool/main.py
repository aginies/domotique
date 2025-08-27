# antoine@ginies.org
# GPL3
import socket
import utime
import os
import ujson
import _thread
from machine import Pin
import esp32 # get MCU temp
import gc
import ure as re

# Internal lib
import web_command as w_cmd
import domo_utils as d_u
import esp32_led as e_l
import oled_ssd1306 as o_s
import config_var as c_v
import domo_wifi as d_w
import web_config as w_c
import save_config as s_c
import web_files_management as w_f_m

lock = _thread.allocate_lock()
shared_counter = 0

# LIST OF CONNECTED CLIENTS
connected_ips = set()

# LED EXTERNAL
led = Pin(c_v.LED_PIN, Pin.OUT)

# DOOR MAGNET
door_sensor = Pin(c_v.DOOR_SENSOR_PIN, Pin.IN, Pin.PULL_UP)
door_state = door_sensor.value()
prev_door_state = door_state

# RELAY for BP1 and BP2
# Be sure to put max power to the pin to control the relay
last_ctrl_relay_time = 0
relay1 = Pin(c_v.RELAY1_PIN, Pin.OUT, drive=Pin.DRIVE_3)
relay1.off()
relay2 = Pin(c_v.RELAY2_PIN, Pin.OUT, drive=Pin.DRIVE_3)
relay2.off()

# At start we can only Open the Pool
# remove all previous ERROR
TO_REMOVE = ["/BP1", "/EMERGENCY_STOP", "/IN_PROGRESS"]
for doit in TO_REMOVE:
    try:
        os.remove(doit)
    except OSError:
        pass
with open('/BP2', 'w') as file:
    file.write('BP2 INIT FILE')

def check_and_display_error():
    """ In case of error display quickly the error color """
    if ERR_SOCKET is True:
        e_l.internal_led_blink(e_l.violet, e_l.led_off, 1, 0.1)
    if ERR_OLED is True:
        e_l.internal_led_blink(e_l.green, e_l.led_off, 1, 0.1)
    if ERR_WIFI is True:
        e_l.internal_led_blink(e_l.blue, e_l.led_off, 1, 0.1)
    if ERR_CON_WIFI is True:
        e_l.internal_led_blink(e_l.white, e_l.led_off, 1, 0.1)
    if ERR_CTRL_RELAY is True:
        e_l.internal_led_blink(e_l.pink, e_l.led_off, 1, 0.1)

def oled_constant_show():
    """ Data always displayed """
    if oled_d:
        mcu_t = esp32.mcu_temperature()
        temp_mcu = "Temp ESP32: " + str(mcu_t) + "C"
        oled_d.fill(0)
        SSID = c_v.AP_SSID
        if c_v.E_WIFI is True:
            if ERR_CON_WIFI is False:
                SSID = c_v.WIFI_SSID
        if ERR_SOCKET is False and ERR_WIFI is False:
            oled_d.text("Wifi SSID:", 0, 0)
            oled_d.text(SSID, 0, 10)
            oled_d.text("Wifi IP AP:", 0, 20)
            INFO_W = IP_ADDR +":"+ str(PORT)
            oled_d.text(INFO_W, 0, 30)
        else:
            oled_d.text(" ! Attention !", 0, 0)
            oled_d.text(" Wifi Pas OK", 0, 10)
            oled_d.text(" ! ** !", 0, 20)
            oled_d.text("Mode degrade!", 0, 30)
        oled_d.text(temp_mcu, 0, 40)
        if d_u.file_exists('/IN_PROGRESS'):
            if d_u.file_exists('/BP1'):
                oled_d.text("En Ouverture", 0, 50)
            elif d_u.file_exists('/BP2'):
                oled_d.text("En Fermeture", 0, 50)
            else:
                oled_d.text("En Fonctionement", 0, 50)
        if d_u.file_exists('/EMERGENCY_STOP'):
            oled_d.text("", 0, 50)
            oled_d.text("REBOOT NEEDED!", 0, 50)
        oled_d.show()

def ctrl_relay(which_one, duration, adjust):
    """ relay 1 or 2, now non-blocking """
    lock.acquire()

    if which_one == 1:
        relay = relay1
        active_file = '/BP1'
        inactive_file = '/BP2'
    else:
        relay = relay2
        active_file = '/BP2'
        inactive_file = '/BP1'

    with open('/IN_PROGRESS', 'w') as file:
        file.write('This file was created by clicking BP1 or BP2.')
    try:
        # internal_led_blink(pink, led_off, 3, c_v.time_ok) # Keep if non-blocking
        relay.on()
        d_u.print_and_store_log(f"Relay {which_one} ON for {duration} seconds.")
        start_time = utime.time()
        while utime.time() - start_time < duration:
            if check_stop_relay():
                d_u.print_and_store_log(f"Stop requested for Relay {which_one} (duration left: {duration - (utime.time() - start_time):.1f}s).")
                relay.off()
                break
            utime.sleep_ms(50)

        if relay.value() == 1:
            relay.off()

        if not check_stop_relay():
            if not adjust:
                d_u.print_and_store_log("Full action in progress")
                d_u.print_and_store_log(f"Creating {active_file}")
                with open(active_file, 'w') as file:
                    file.write(f'This file was created by clicking BP{which_one}.')
                try:
                    os.remove(inactive_file)
                except OSError:
                    pass
                try:
                    os.remove("/EMERGENCY_STOP")
                except OSError:
                    pass
            else:
                d_u.print_and_store_log("Adjustement in progress")
        else:
            # If stopped by emergency, ensure files are cleared
            try:
                os.remove("/BP1")
            except OSError:
                pass
            try:
                os.remove("/BP2")
            except OSError:
                pass
        try:
            os.remove("/IN_PROGRESS")
        except OSError:
            pass
        lock.release()
        gc.collect()

    except Exception as err:
        d_u.print_and_store_log(f"Error in ctrl_relay({which_one}): {err}")
        relay1.off()
        relay2.off()
        # internal_led_blink(pink, led_off, 5, c_v.time_err)
        ERR_CTRL_RELAY = True

def check_stop_relay():
    d_u.file_exists("/EMERGENCY_STOP")

def ctrl_relay_off():
    """ Force all relay Off! """
    d_u.print_and_store_log("Relays forced OFF, stop_relay_action set to True.")
    relay1.off()
    relay2.off()

def handle_client_connection(sock):
    """ At client connection send html stuff """
    try:
        cl, addr = sock.accept()
        client_ip = addr[0]
        if client_ip not in connected_ips:
            d_u.print_and_store_log(f"Client connecté depuis {addr}")
            connected_ips.add(client_ip)
        request = cl.recv(4192)
        #print(request)
        handle_request(cl, request)
    except OSError as err:
        if err.args[0] == errno.EAGAIN:
            pass
        else:
            d_u.print_and_store_log(f"Error handling client connection: {err}")
        try:
            if 'cl' in locals() and cl:
                cl.close()
        except NameError:
            pass # cl might not be defined if accept() failed
        pass

def thread_do_job_crtl_relay(B_text, relay_nb, duration):
    """ Do the thread job for the realy """
    global last_ctrl_relay_time
    current_time = utime.time()
    response_content = ""
    adjust = True

    if current_time - last_ctrl_relay_time > duration:
        if oled_d is not None: oled_d.poweron()
        d_u.print_and_store_log(f"{B_text} activé")
        last_ctrl_relay_time = current_time
        if B_text != "OPEN_B" and B_text != "CLOSE_B":
            adjust = False
            d_u.print_and_store_log(f"Will Create /{B_text} file")
        else:
            adjust = True
            d_u.print_and_store_log(f"Will Not Create any files")
        if B_text == "BP1":
            try:
                os.remove("/BP2")
            except OSError:
                pass # BP2 might not exist
        elif B_text == "BP2":
            try:
                os.remove("/BP1")
            except OSError:
                pass # BP1 might not exist

        _thread.start_new_thread(ctrl_relay, (relay_nb, duration, adjust))
        response_content = B_text + " activated"
    else:
        d_u.print_and_store_log(f"{B_text} Duplicate request seen...")
        response_content = "Duplicate request " + B_text
    content_type = "text/plain"

def handle_request(cl, request):
    """ Handle incoming HTTP requests """

    response_content = ""
    status_code = "200 OK"
    content_type = "text/html"
    full_request = request

    if b'/BP1_ACTIF' in request:
        thread_do_job_crtl_relay("BP1", 1, c_v.time_to_open)

    elif b'/OPEN_B_ACTIF' in request:
        thread_do_job_crtl_relay("OPEN_B", 1, c_v.time_adjust)

    elif b'/CLOSE_B_ACTIF' in request:
        thread_do_job_crtl_relay("CLOSE_B", 2, c_v.time_adjust)

    elif b'/BP2_ACTIF' in request:
        thread_do_job_crtl_relay("BP2", 2, c_v.time_to_close)

    elif b'/EMERGENCY_STOP' in request:
        if oled_d is not None: oled_d.poweron()
        d_u.print_and_store_log("Emergency Stop activé!")
        with open('/EMERGENCY_STOP', 'w') as file:
            file.write('Emergency stop is active and requires reboot.')
        d_u.print_and_store_log("Created /EMERGENCY_STOP file.")
        ctrl_relay_off()
        # Remove both /BP1 and /BP2 files to reflect that no operation is active.
        # This ensures the /status endpoint returns False for both active flags.
        try:
            LIST_F = ["BP1", "BP2"]
            for TODO in LIST_F:
                with open('/'+TODO, 'w') as file:
                    file.write('FORCE ALL BUTTON OFF!')    
            d_u.print_and_store_log("Force all Buttons OFF")
        except OSError:
            pass
        response_content = "Emergency Stop activated"
        content_type = "text/plain"

    elif b'/status' in request:
        bp1_active = d_u.file_exists('/BP1')
        bp2_active = d_u.file_exists('/BP2')
        emergency_stop = d_u.file_exists('/EMERGENCY_STOP')
        in_progress = d_u.file_exists('/IN_PROGRESS')
        status_data = {
            "BP1_active": bp1_active,
            "BP2_active": bp2_active,
            "Emergency_stop": emergency_stop,
            "In_progress": in_progress
            }
        response_content = ujson.dumps(status_data)
        content_type = "application/json"
    elif request.startswith('GET /SAVE_config'):
        response_content = w_c.serve_config_page()
    elif request.startswith('POST /SAVE_config'):
        response_from_save_config = s_c.save_configuration(request)
        # Check if the returned value is a redirect response
        if response_from_save_config.startswith("HTTP/1.1 30"):
            cl.sendall(response_from_save_config.encode('utf-8'))
            cl.close()
            return
        else:
            response_content = response_from_save_config
    elif b'/log.txt' in request:
        try:
            with open('/log.txt', 'r') as file:
                response_content = file.read()
            content_type = "text/plain"
            status_code = "200 OK"
        except FileNotFoundError:
            response_content = "Log file not found."
            content_type = "text/plain"
            status_code = "404 Not Found"
    elif b'/livelog' in request and request.startswith(b'GET'):
        response_content = w_cmd.create_log_page()
        content_type = "text/html"
        status_code = "200 OK"
    elif b'/file_management' in request:
        response_content = w_f_m.serve_file_management_page()
    elif request.startswith('GET /delete'):
        request_str = request.decode('utf-8')
        file_to_delete = request_str.split('file=', 1)[1].split(' ')[0]
        try:
            os.remove(file_to_delete)
            d_u.print_and_store_log(f"File {file_to_delete} deleted successfully.")
            response_content = "File deleted. <a href='/file_management'>Return to File Manager</a>"
        except OSError as e:
            response_content = f"Error deleting file: {e}"
    elif request.startswith('/upload'):
        try:
            d_u.print_and_store_log("Starting file upload process.")
            headers_end = full_request.find(b'\r\n\r\n')
            if headers_end == -1:
                raise ValueError("Headers end not found.")
            headers = full_request[:headers_end]
            boundary_match = re.search(b'boundary=([^\r\n]+)', headers)
            if not boundary_match:
                raise ValueError("Boundary not found in headers.")
            boundary = boundary_match.group(1)

            filename_match = re.search(b'filename="([^"]+)"', headers)
            if not filename_match:
                raise ValueError("Filename not found in headers.")
            filename = filename_match.group(1).decode('utf-8')

            d_u.print_and_store_log(f"Found boundary: {boundary.decode()} and filename: {filename}")
            body_start_index = headers_end + 4
            first_chunk = full_request[body_start_index:]
            with open("/" + filename, 'wb') as f:
                f.write(first_chunk)
                while True:
                    chunk = cl.recv(1024)
                    if not chunk:
                        break # Connection closed or timeout
                    if b'--' + boundary + b'--' in chunk:
                        end_index = chunk.find(b'--' + boundary + b'--')
                        f.write(chunk[:end_index - 2]) # -2 to remove trailing CRLF
                        break
                    else:
                        f.write(chunk)

            d_u.print_and_store_log(f"File {filename} uploaded successfully to the root directory.")
            response_content = f"File {filename} uploaded. <a href='/file_management'>Return to File Manager</a>".encode('utf-8')

        except Exception as e:
            d_u.print_and_store_log(f"Error uploading file: {e}")
            response_content = f"Error uploading file: {e}".encode('utf-8')
            status_code = b"500 Internal Server Error"
    else:
        response_content = w_cmd.create_html_response()
        content_type = "text/html"

    response = (
        f"HTTP/1.1 {status_code}\r\n"
        f"Content-Type: {content_type}\r\n"
        "Connection: close\r\n"
        "\r\n"
        f"{response_content}"
    )
    cl.sendall(response.encode())
    cl.close()

def start_WIFI_ap():
    ap = d_w.setup_access_point()
    if ap:
        ERR_WIFI = False
    else:
        ERR_WIFI = True
    return ap, ERR_WIFI

def main():
    """ The Main one ! """
    global door_state
    global statusd
    sock = None
    global oled_d
    global IP_ADDR
    global PORT
    ap = None
    hour = 12
    # ERR_* are used to display LED color in case of...
    global ERR_SOCKET, ERR_WIFI, ERR_CTRL_RELAY, ERR_CON_WIFI, ERR_OLED
    ERR_SOCKET = False
    ERR_OLED = False
    ERR_WIFI = False
    ERR_CTRL_RELAY = False
    ERR_CON_WIFI = False
    # Start up info
    info_start = "#############--- Guibo Control ---############# "
    d_u.check_and_delete_if_too_big("/log.txt", 2)
    d_u.print_and_store_log(info_start)
    d_u.set_freq(c_v.CPU_FREQ)
    oled_d = o_s.initialize_oled()
    if oled_d:
        oled_d.text(info_start, 0, 0)
        info_control = "Version 1.0"
        oled_d.text(info_control, 0, 10)
        oled_d.text('https://github.c', 0, 20)
        oled_d.text('om/aginies/domot', 0, 30)
        oled_d.text('ique', 0, 40)
        oled_d.text('ag@ginies.org', 0, 50)
        oled_d.show()
        utime.sleep(1)
    if oled_d:
        oled_d.fill(0)

    if c_v.E_WIFI is False:
        ap, ERR_WIFI = start_WIFI_ap()
        IP_ADDR = c_v.AP_IP[0]
    else:
        result_con_wifi = d_w.connect_to_wifi()
        if result_con_wifi['success']:
            IP_ADDR = result_con_wifi['ip_address']
            d_u.set_time_with_ntp()
            d_u.print_and_store_log(d_u.show_rtc_date())
            hour, minute, second = d_u.show_rtc_time()
            d_u.print_and_store_log(f"{hour}:{minute}:{second}")
        else:
            # Failed to connect to External Wifi
            # Starting the Wifi AP
            ERR_CON_WIFI = True
            ap, ERR_WIFI = start_WIFI_ap()
            if ap:
                o_s.oled_show_text_line("AP Wifi Ok", 0)
                IP_ADDR = c_v.AP_IP[0]
            else:
                o_s.oled_show_text_line("AP Wifi NOK!", 0)
    # Read the initial state of the door sensor
    door_state = door_sensor.value()
    d_u.print_and_store_log(f"Information sur {c_v.DOOR}:")
    if door_state == 0:
        statusd = "Status: OUVERT"
        led.value(1)
    elif door_state == 1:
        statusd = "Status: FERME"
        led.value(0)

    d_u.print_and_store_log(statusd)
    o_s.oled_show_text_line(statusd, 10)

    ports_to_try = [80, 81]  # List of ports to try in order
    for port in ports_to_try:
        o_s.oled_show_text_line("", 20)
        if IP_ADDR and IP_ADDR != '0.0.0.0':
            addr = socket.getaddrinfo(IP_ADDR, port)[0][-1]
            sock = socket.socket()
            try:
                sock.bind(addr)
                o_s.oled_show_text_line(f"Socket Ok: {port}", 20)
                sock.listen(5)
                sock.setblocking(False)
                o_s.oled_show_text_line("Listening Ok", 30)
                d_u.print_and_store_log(f'Listening on {addr}')
                e_l.internal_led_blink(e_l.violet, e_l.led_off, 3, c_v.time_ok)
                PORT = port
                ERR_SOCKET = False
                break  # Exit the loop if binding is successful
            except OSError as err:
                d_u.print_and_store_log(f"Failed to bind to port {port}: {err}")
                o_s.oled_show_text_line("", 20)
                o_s.oled_show_text_line(f"Socket :{port} NOK!", 20)
                e_l.internal_led_blink(e_l.violet, e_l.led_off, 5, c_v.time_err)
                ERR_SOCKET = True
        else:
            d_u.print_and_store_log('Problème Avec le WIFI')
            o_s.oled_show_text_line("WIFI AP NOK!", 40)
            ERR_WIFI = True
            internal_led_blink(e_l.blue, e_l.led_off, 5, c_v.time_err)

    if oled_d is None:
        ERR_OLED = True
    error_vars = {
        'Ouverture Socket': ERR_SOCKET,
        'Ecran OLED': ERR_OLED,
        'Wifi': ERR_WIFI,
        'Controle du relay': ERR_CTRL_RELAY,
        'Connection Wifi': ERR_CON_WIFI
    }
    if not any(error_vars.values()):
        d_u.print_and_store_log("Système OK")
        e_l.french_flag()
    else:
        error_messages = [f"Erreur: {var_name}" for var_name, var_value in error_vars.items() if var_value]
        d_u.print_and_store_log(", ".join(error_messages))

    # We are ready
    while True:
        prev_door_state = door_state
        door_state = door_sensor.value()
        check_and_display_error()
        if prev_door_state == 0 and door_state == 1:
            led.value(0)
            e_l.internal_led_color(e_l.red)
            statusd = "Status: FERME"
            d_u.print_and_store_log(statusd)

        elif prev_door_state == 1 and door_state == 0:
            led.value(1)
            e_l.internal_led_color(e_l.green)
            statusd = "Status: OUVERT"
            d_u.print_and_store_log(statusd)

        hour %= 24
        if 6 <= hour < 23:
            oled_constant_show()
        else:
            if oled_d is not None: oled_d.poweroff()

        if sock:
            handle_client_connection(sock)

        utime.sleep(0.1)

if __name__ == "__main__":
    main()
