""" 
 antoine@ginies.org
 GPL3
"""
import time
import os
import asyncio
import _thread
import ujson
from machine import Pin, reset
import ure as re

# Internal lib
import web_command as w_cmd
import domo_utils as d_u
import esp32_led as e_l
import oled_ssd1306 as o_s
import config_var as c_v
import domo_wifi as d_w
import web_config as w_c
import web_files_management as w_f_m
import web_log as w_l
import crtl_relay as c_r
import domo_socket_server as d_s_s
import domo_microdot as d_m
import web_upload as w_u
from domo_microdot import ws_app
from microdot import Microdot, send_file, Response

# LIST OF CONNECTED CLIENTS
connected_ips = set()

# LED EXTERNAL
led = Pin(c_v.LED_PIN, Pin.OUT)

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

def oled_special_show():
    """ Data always displayed """
    if oled_d:
        while True:
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
            time.sleep(1)

def start_WIFI_ap():
    ap = d_w.setup_access_point()
    if ap:
        ERR_WIFI = False
    else:
        ERR_WIFI = True
    return ap, ERR_WIFI

@ws_app.before_request
def log_client_ip(request):
    client_ip = request.client_addr[0]
    if client_ip not in connected_ips:
        d_u.print_and_store_log(f"@ws_app Client connected from {client_ip}")
        connected_ips.add(client_ip)

@ws_app.route('/')
def index(request):
    return w_cmd.create_html_response(), 200, {"Content-Type": "text/html"}

@ws_app.route('/BP1_ACTIF', methods=['POST'])
def bp1_actif(request):
    d_u.print_and_store_log(f"ACTION: {c_v.nom_bp1} Complete")
    c_r.thread_do_job_crtl_relay("BP1", 1, c_v.time_to_open)
    return "", 200

@ws_app.route('/OPEN_B_ACTIF', methods=['POST'])
def open_b_actif(request):
    d_u.print_and_store_log(f"ACTION: {c_v.nom_open_b}{c_v.time_adjust}sec")
    c_r.thread_do_job_crtl_relay("OPEN_B", 1, c_v.time_adjust)
    return "", 200

@ws_app.route('/CLOSE_B_ACTIF', methods=['POST'])
def close_b_actif(request):
    d_u.print_and_store_log(f"ACTION: {c_v.nom_close_b}{c_v.time_adjust}sec")
    c_r.thread_do_job_crtl_relay("CLOSE_B", 2, c_v.time_adjust)
    return "", 200

@ws_app.route('/BP2_ACTIF', methods=['POST'])
def bp2_actif(request):
    d_u.print_and_store_log(f"ACTION: {c_v.nom_bp2} Complete")
    c_r.thread_do_job_crtl_relay("BP2", 2, c_v.time_to_close)
    return "", 200

@ws_app.route('/EMERGENCY_STOP', methods=['POST'])
def emergency_stop(request):
    d_u.print_and_store_log("ACTION: Emergency Stop activated!")
    if oled_d is not None:
        oled_d.poweron()
    with open('/EMERGENCY_STOP', 'w') as file:
        file.write('Emergency stop is active and requires reboot.')
    d_u.print_and_store_log("Created /EMERGENCY_STOP file.")
    c_r.ctrl_relay_off()
    for todo in ["BP1", "BP2"]:
        try:
            os.remove(todo)
        except OSError:
            pass
    d_u.print_and_store_log("Force all Buttons OFF")
    return "Emergency Stop activated", 200, {"Content-Type": "text/plain"}

@ws_app.route('/status', methods=['GET'])
def status(request):
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
    return ujson.dumps(status_data), 200, {"Content-Type": "application/json"}

@ws_app.route('/file_management')
def file_management(request):
    d_u.print_and_store_log("Show File management web page")
    return w_f_m.serve_file_management_page(), 200, {"Content-Type": "text/html"}

@ws_app.route('/web_config', methods=['GET', 'POST'])
def web_config(request):
    response = w_c.serve_config_page(IP_ADDR, WS_PORT)
    return response, 200, {"Content-Type": "text/html"}

@ws_app.route('/save_config', methods=['GET', 'POST'])
def save_config(request):
    return Response(
        status_code=307,
        headers={"Location": f"http://{IP_ADDR}:{WS_PORT}/save_config"}
    )

@ws_app.route('/log.txt')
def log_file(request):
    try:
        with open('/log.txt', 'r') as file:
            return file.read(), 200, {"Content-Type": "text/plain"}
    except FileNotFoundError:
        return "Log file not found.", 404, {"Content-Type": "text/plain"}

@ws_app.route('/livelog')
def livelog(request):
    return w_l.create_log_page(), 200, {"Content-Type": "text/html"}

@ws_app.route('/get_log_action')
def get_log_action(request):
    response, status_code, headers = w_l.serve_log_file(4, "ACTION")
    return response, status_code, headers

@ws_app.route('/get_log_upload')
def get_log_upload(request):
    response, status_code, headers = w_l.serve_log_file(10, "UPLOAD")
    return response, status_code, headers

@ws_app.route('/RESET_device')
def reset_device(request):
    d_u.print_and_store_log("Reset button pressed")
    reset()

@ws_app.route('/view')
def view_file(request):
    file_to_view = request.args.get('file')
    if file_to_view == "config_var.py":
        return "File not Allowed!", 404, {"Content-Type": "text/plain"}
    elif d_u.file_exists("/" + file_to_view):
        return w_f_m.create_view_file_page("/" + file_to_view), 200, {"Content-Type": "text/html"}
    else:
        return "File not found", 404, {"Content-Type": "text/plain"}

@ws_app.route('/revert_mode')
def revert_mode(request):
    d_u.print_and_store_log("ACTION: Entering Revert mode")
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
            
    return Response(status_code=303, headers={"Location": "/"})

@ws_app.route('/delete')
def delete_file(request):
    file_to_delete = request.args.get('file')
    d_u.print_and_store_log(f"File {file_to_delete}")
    try:
        os.remove(file_to_delete)
        d_u.print_and_store_log(f"File {file_to_delete} deleted successfully.")
        return Response(status_code=303, headers={"Location": "/file_management"})
    except OSError as e:
        return f"Error deleting file: {e}", 400, {"Content-Type": "text/plain"}

@ws_app.route('/UPLOAD_server', methods=['GET', 'POST'])
def upload_server(request):
    response = w_u.serve_file_upload_page(IP_ADDR, WS_PORT)
    return response, 200, {"Content-Type": "text/html"}

@ws_app.route('/upload_file', methods=['GET', 'POST'])
def upload_file(request):
    return Response(
        status_code=307,
        headers={"Location": f"http://{IP_ADDR}:{WS_PORT}/upload"}
    )

def main():
    """ The Main one ! """
    global oled_d
    global IP_ADDR
    global PORT
    PORT = 80
    global WS_PORT
    WS_PORT = 8080
    ap = None
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
    if oled_d is None:
        ERR_OLED = True
    else:
        o_s.show_info_on_oled(info_start)
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

    _thread.start_new_thread(d_s_s.start_socket_server, (IP_ADDR, WS_PORT))
    _thread.start_new_thread(o_s.oled_constant_show, (IP_ADDR, PORT))
    _thread.start_new_thread(oled_special_show, ())

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

    o_s.oled_show_text_line("", 20)
    if IP_ADDR and IP_ADDR != '0.0.0.0':
        try:
            asyncio.run(d_m.start_microdot_ws(IP_ADDR, PORT))
        except Exception as err:
            d_u.print_and_store_log(f"Server error: {err}")
            ERR_SOCKET = True
        finally:
            asyncio.new_event_loop()
    else:
        d_u.print_and_store_log('Trouble with WIFI')
        o_s.oled_show_text_line("WIFI AP NOK!", 40)
        ERR_WIFI = True
        e_l.internal_led_blink(e_l.blue, e_l.led_off, 5, c_v.time_err)

if __name__ == "__main__":
    main()
