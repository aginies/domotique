# antoine@ginies.org
# GPL3
import socket
import utime
import os
import ujson
from machine import Pin, reset
import esp32 # get MCU temp
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
import web_log as w_l
import crtl_relay as c_r

# LIST OF CONNECTED CLIENTS
connected_ips = set()

# LED EXTERNAL
led = Pin(c_v.LED_PIN, Pin.OUT)

# DOOR MAGNET
door_sensor = Pin(c_v.DOOR_SENSOR_PIN, Pin.IN, Pin.PULL_UP)
door_state = door_sensor.value()
prev_door_state = door_state

# SEtting OFF RELAY for BP1 and BP2
c_r.relay1.off()
c_r.relay2.off()

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
            oled_d.text(" ! Warning !", 0, 0)
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
                oled_d.text("", 0, 50)
        if d_u.file_exists('/EMERGENCY_STOP'):
            oled_d.text("", 0, 50)
            oled_d.text("REBOOT NEEDED!", 0, 50)
        oled_d.show()

def handle_client_connection(sock):
    """ At client connection send html stuff """
    try:
        cl, addr = sock.accept()
        client_ip = addr[0]
        if client_ip not in connected_ips:
            d_u.print_and_store_log(f"Client connected from {addr}")
            connected_ips.add(client_ip)
        # disable Nagle algo
        #cl.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        request = cl.recv(8192)
        #print(request)
        handle_request(cl, sock, request)
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

def redirect_to_slash(cl):
    """ Redirect to / """
    redirect_url = "/"
    response_headers = [
        "HTTP/1.1 303 See Other",
        f"Location: {redirect_url}",
        "Connection: close",
        "",
    ]
    response = "\r\n".join(response_headers)
    cl.sendall(response.encode())
    cl.close()

def handle_request(cl, sock, request):
    """ Handle incoming HTTP requests """

    response_content = ""
    status_code = "200 OK"
    content_type = "text/html"

    if b'/BP1_ACTIF' in request:
        c_r.thread_do_job_crtl_relay("BP1", 1, c_v.time_to_open)

    elif b'/OPEN_B_ACTIF' in request:
        c_r.thread_do_job_crtl_relay("OPEN_B", 1, c_v.time_adjust)

    elif b'/CLOSE_B_ACTIF' in request:
        c_r.thread_do_job_crtl_relay("CLOSE_B", 2, c_v.time_adjust)

    elif b'/BP2_ACTIF' in request:
        c_r.thread_do_job_crtl_relay("BP2", 2, c_v.time_to_close)

    elif request.startswith('GET /EMERGENCY_STOP'):
        if oled_d is not None: oled_d.poweron()
        d_u.print_and_store_log("Emergency Stop actived!")
        with open('/EMERGENCY_STOP', 'w') as file:
            file.write('Emergency stop is active and requires reboot.')
        d_u.print_and_store_log("Created /EMERGENCY_STOP file.")
        c_r.ctrl_relay_off()
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

    elif request.startswith('GET /UPLOAD_file'):
        d_u.print_and_store_log("UPLOAD_file displayed")
        response_content = w_f_m.serve_file_management_page()
    elif request.startswith('POST /UPLOAD_file'):
        d_u.print_and_store_log("UPLOAD_file file in progress")
        response_from_file_m = w_f_m.handle_upload(cl, sock, request)
        cl.sendall(response_from_file_m.encode('utf-8'))
        utime.sleep(1)

    elif request.startswith('GET /file_management'):
        d_u.print_and_store_log("Show File management web page")
        response_content = w_f_m.serve_file_management_page()

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
        response_content = w_l.create_log_page()
        content_type = "text/html"
        status_code = "200 OK"
    
    elif b'/get_log' in request:
        response = w_f_m.serve_log_file()
        cl.sendall(response.encode('utf-8'))

    elif b'/RESET_device' in request:
        d_u.print_and_store_log("Reset button pressed")
        reset()

    elif b'/view' in request and request.startswith(b'GET'):
        d_u.print_and_store_log("Entering view file")
        request_str = request.decode('utf-8')
        file_to_view = request_str.split('file=', 1)[1].split(' ')[0]
        try:
            if file_to_view == "config_var.py":
                # Dont show config_var with all code access
                response_content = "File not Allowed!"
                content_type = "text/plain"
                status_code = "404 Not Found"
            elif d_u.file_exists("/"+file_to_view):
                response_content = w_f_m.create_view_file_page("/"+file_to_view)
                content_type = "text/html"
                status_code = "200 OK"
            else:
                response_content = "File not found"
                content_type = "text/plain"
                status_code = "404 Not Found"
        except IndexError:
            response_content = "Bad request: file parameter missing"
            content_type = "text/plain"
            status_code = "400 Bad Request"

    elif b'/file_management' in request:
        response_content = w_f_m.serve_file_management_page()

    elif b'/revert_mode' in request:
        d_u.print_and_store_log("Entering Revert mode")
        if d_u.file_exists('/BP1'):
            d_u.print_and_store_log("Revert mode creating BP2")
            os.remove("/BP1")
            with open('/BP2', 'w') as file:
                file.write('Create BP2 after revert')
        elif d_u.file_exists('/BP2'):
            d_u.print_and_store_log("Revert mode creating BP1")
            os.remove("/BP2")
            with open('/BP1', 'w') as file:
                file.write('Create BP1 after revert')
        redirect_to_slash(cl)
        return
    elif request.startswith('GET /delete'):
        request_str = request.decode('utf-8')
        file_to_delete_encoded = request_str.split('file=', 1)[1].split(' ')[0]
        file_to_delete = d_u.urldecode(file_to_delete_encoded)
        d_u.print_and_store_log(f"File {file_to_delete}")
        try:
            os.remove(file_to_delete)
            d_u.print_and_store_log(f"File {file_to_delete} deleted successfully.")
            response_content = "File deleted. <a href='/file_management'>Return to File Manager</a>"
        except OSError as e:
            response_content = f"Error deleting file: {e}"
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
    d_u.check_and_delete_if_too_big("/log.txt", 20)
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
                break
            except OSError as err:
                d_u.print_and_store_log(f"Failed to bind to port {port}: {err}")
                o_s.oled_show_text_line("", 20)
                o_s.oled_show_text_line(f"Socket :{port} NOK!", 20)
                e_l.internal_led_blink(e_l.violet, e_l.led_off, 5, c_v.time_err)
                ERR_SOCKET = True
        else:
            d_u.print_and_store_log('Trouble with WIFI')
            o_s.oled_show_text_line("WIFI AP NOK!", 40)
            ERR_WIFI = True
            internal_led_blink(e_l.blue, e_l.led_off, 5, c_v.time_err)

    if oled_d is None:
        ERR_OLED = True
    error_vars = {
        'Openning Socket': ERR_SOCKET,
        'OLED Screen': ERR_OLED,
        'Wifi': ERR_WIFI,
        'Relay Control': ERR_CTRL_RELAY,
        'Wifi Connection': ERR_CON_WIFI
    }
    if not any(error_vars.values()):
        d_u.print_and_store_log("System OK")
        e_l.french_flag()
    else:
        error_messages = [f"Error: {var_name}" for var_name, var_value in error_vars.items() if var_value]
        d_u.print_and_store_log(", ".join(error_messages))

    # We are ready
    check_and_display_error()
    while True:
        prev_door_state = door_state
        door_state = door_sensor.value()
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
