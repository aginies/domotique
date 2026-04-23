# antoine@ginies.org
# GPL3

import time
import os
import gc
import asyncio
import _thread
import ujson
import sys
import ubinascii
import esp32
from machine import Pin, reset, WDT

import domo_utils as d_u
import esp32_led as e_l
import oled_ssd1306 as o_s
import config_var as c_v
import domo_wifi as d_w
import web_config as w_c
import web_files_management as w_f_m
import web_log as w_l
import domo_socket_server as d_s_s
import domo_microdot as d_m
import web_upload as w_u
import solar_monitor as s_m
import web_command as w_cmd
import mqtt_client as m_c
import paths
from domo_microdot import ws_app
from microdot import Microdot, send_file, Response

connected_ips = set()

PROTECTED_ROUTES = {
    '/web_config', '/save_config', '/file_management', 
    '/RESET_device', '/delete', '/UPLOAD_server', 
    '/upload_file', '/boost'
}

@ws_app.before_request
def auth_and_log(request):
    # Log client IP
    client_ip = request.client_addr[0]
    if client_ip not in connected_ips:
        d_u.print_and_store_log(f"Client connected from {client_ip}")
        connected_ips.add(client_ip)
    
    # Basic Auth
    web_user = getattr(c_v, 'WEB_USER', "")
    web_password = getattr(c_v, 'WEB_PASSWORD', "")
    
    if web_user and request.path in PROTECTED_ROUTES:
        auth = request.headers.get('Authorization')
        authorized = False
        if auth and auth.startswith('Basic '):
            try:
                decoded = ubinascii.a2b_base64(auth[6:]).decode('utf-8')
                user, password = decoded.split(':')
                if user == web_user and password == web_password:
                    authorized = True
            except Exception:
                pass
        
        if not authorized:
            return Response(
                "Unauthorized", 
                status_code=401, 
                headers={"WWW-Authenticate": 'Basic realm="Restricted"'}
            )

@ws_app.route('/')
def index(request):
    return w_cmd.create_html_response()

@ws_app.route('/status', methods=['GET'])
def status(request):
    import utime
    data = {
        "grid_power": s_m.current_grid_power,
        # Derive from current duty so the status always reflects the live duty
        # cycle, not the burst_control_loop's last cached value (up to 0.5s stale).
        "equipment_power": round(s_m._current_duty * float(getattr(c_v, 'EQUIPMENT_MAX_POWER', 2000)), 1),
        "equipment_active": s_m.equipment_active,
        "force_mode": s_m.force_mode_active,
        "boost_active": utime.time() < s_m.boost_end_time,
        "safe_state": s_m.safe_state,
        "emergency_mode": s_m.emergency_mode,
        "shelly_error": s_m.last_shelly_error,
        "water_temp": s_m.current_water_temp,
        "ssr_temp": s_m.current_ssr_temp,
        "fan_active": s_m.fan_active,
        "fan_percent": s_m.fan_percent,
        "night_mode": s_m.night_mode,
        "rtc_time": "{:02d}:{:02d}:{:02d}".format(*d_u.show_rtc_time()),
        "total_import": s_m._total_import_Wh,
        "total_redirect": s_m._total_redirect_Wh,
        "total_export": s_m._total_export_Wh,
        "grid_source": s_m.grid_source,
        "mqtt_enabled": getattr(c_v, 'E_MQTT', False),
        "shelly_mqtt_enabled": getattr(c_v, 'E_SHELLY_MQTT', False),
        "mqtt_status": m_c.is_connected[0] if getattr(c_v, 'E_MQTT', False) is True else "disabled",
        "shelly_link": getattr(c_v, 'FAKE_SHELLY', False) or (s_m.last_shelly_error is None and (utime.time() - s_m._last_good_poll) < 30),
        "esp_temp": esp32.mcu_temperature(),
        "free_ram": gc.mem_free(),
        "uptime": utime.ticks_ms() // 1000,
        "rssi": -100
    }
    try:
        import network
        sta_if = network.WLAN(network.STA_IF)
        if sta_if.isconnected():
            data["rssi"] = sta_if.status('rssi')
    except:
        pass
    return ujson.dumps(data), 200, {"Content-Type": "application/json"}

@ws_app.route('/history', methods=['GET'])
def history(request):
    return ujson.dumps(s_m.power_history), 200, {"Content-Type": "application/json"}

@ws_app.route('/boost', methods=['POST'])
def boost(request):
    minutes = request.args.get('min')
    try:
        minutes = int(minutes) if minutes else None
    except ValueError:
        minutes = None
    s_m.start_boost(minutes)
    return Response(status_code=303, headers={"Location": "/"})

@ws_app.route('/cancel_boost', methods=['POST'])
def cancel_boost(request):
    s_m.cancel_boost()
    return Response(status_code=303, headers={"Location": "/"})

@ws_app.route('/test_fan', methods=['POST'])
def test_fan(request):
    import ujson
    try:
        # Check for speed in query parameters or form data
        speed = request.args.get('speed')
        if not speed:
            body = request.body.decode('utf-8')
            data = ujson.loads(body)
            speed = data.get('speed')
        
        success = s_m.test_fan_speed(int(speed))
        return ujson.dumps({"success": success}), 200, {"Content-Type": "application/json"}
    except Exception as e:
        return ujson.dumps({"success": False, "error": str(e)}), 400, {"Content-Type": "application/json"}

@ws_app.route('/web_config', methods=['GET', 'POST'])
def web_config(request):
    if 'config_var' in sys.modules:
        del sys.modules['config_var']
    import config_var as c_v
    reboot_needed = request.args.get('reboot_needed') == '1'
    return w_c.serve_config_page(IP_ADDR, WS_PORT, reboot_needed), 200, {"Content-Type": "text/html"}

@ws_app.route('/save_config', methods=['GET', 'POST'])
def save_config(request):
    return Response(
        status_code=307,
        headers={"Location": f"http://{IP_ADDR}:{WS_PORT}/save_config"}
    )

@ws_app.route('/log.txt')
def log_file(request):
    try:
        with open(paths.LOG_FILE, 'r') as f:
            return f.read(), 200, {"Content-Type": "text/plain"}
    except OSError:
        return "Log file not found.", 404, {"Content-Type": "text/plain"}

@ws_app.route('/livelog')
def livelog(request):
    return w_l.create_log_page(), 200, {"Content-Type": "text/html"}

@ws_app.route('/chart.min.js')
def chart_js(request):
    try:
        with open('chart.min.js', 'rb') as f:
            return f.read(), 200, {"Content-Type": "application/javascript"}
    except OSError:
        return "Not found.", 404

@ws_app.route('/stats')
def stats_page(request):
    try:
        with open('web_stats.html', 'r') as f:
            return f.read(), 200, {"Content-Type": "text/html"}
    except OSError:
        return "Statistics page not found.", 404

@ws_app.route('/get_stats')
def get_stats(request):
    try:
        with open('stats.json', 'r') as f:
            return f.read(), 200, {"Content-Type": "application/json"}
    except OSError:
        return "{}", 200, {"Content-Type": "application/json"}

@ws_app.route('/get_log_action')
def get_log_action(request):
    d_u.flush_logs() # Ensure we see the latest
    response, status_code, headers = w_l.serve_log_file(10, ["SOLAR", "MQTT", "Shelly"])
    return response, status_code, headers

@ws_app.route('/get_log_upload')
def get_log_upload(request):
    d_u.flush_logs()
    response, status_code, headers = w_l.serve_log_file(20, ["UPLOAD", "UPDATE"])
    return response, status_code, headers

@ws_app.route('/get_solar_data')
def get_solar_data(request):
    # Combine buffer and file
    s_m._flush_solar_data() 
    try:
        with open("solar_data.txt", "r") as f:
            return f.read(), 200, {"Content-Type": "text/plain"}
    except OSError:
        return "No data recorded yet.", 200, {"Content-Type": "text/plain"}

@ws_app.route('/RESET_device')
def reset_device(request):
    d_u.print_and_store_log("SERVER: Manual reset requested - flushing all buffers")
    s_m._save_stats_to_file()
    s_m._flush_solar_data()
    d_u.flush_logs()
    _thread.start_new_thread(d_u.perform_reset, ())
    return "<html><h1>Reset!</h1><h2>Fermez cette page</h2></html>", 200, {"Content-Type": "text/html"}

@ws_app.route('/file_management')
def file_management(request):
    return w_f_m.serve_file_management_page(), 200, {"Content-Type": "text/html"}

@ws_app.route('/wifi_setup', methods=['GET', 'POST'])
def wifi_setup(request):
    import wifi_setup as w_s
    if request.method == 'POST':
        w_s.save_wifi_config(request.form)
        _thread.start_new_thread(d_u.perform_reset, ())
        return "<html><h1>Config saved!</h1><h2>Rebooting...</h2></html>", 200, {"Content-Type": "text/html"}
    return w_s.get_wifi_setup_page(), 200, {"Content-Type": "text/html"}

# Captive Portal detection routes (Android, Apple, Windows)
@ws_app.route('/generate_204')
@ws_app.route('/hotspot-detect.html')
@ws_app.route('/canonical.html')
@ws_app.route('/success.txt')
@ws_app.route('/ncsi.txt')
def captive_redirect(request):
    return Response(status_code=302, headers={"Location": "/wifi_setup"})

@ws_app.route('/view')
def view_file(request):
    file_to_view = request.args.get('file')
    if not file_to_view:
        return "Missing file parameter", 400, {"Content-Type": "text/plain"}
    file_to_view = d_u.sanitize_filename(file_to_view)
    if file_to_view == "config_var.py":
        return "File not Allowed!", 404, {"Content-Type": "text/plain"}
    elif d_u.file_exists("/" + file_to_view):
        return w_f_m.create_view_file_page("/" + file_to_view), 200, {"Content-Type": "text/html"}
    else:
        return "File not found", 404, {"Content-Type": "text/plain"}

PROTECTED_FILES = {"config_var.py", "main.py", "boot.py", "VERSION"}

@ws_app.route('/delete')
def delete_file(request):
    file_to_delete = request.args.get('file')
    if not file_to_delete:
        return "Missing file parameter", 400, {"Content-Type": "text/plain"}
    file_to_delete = d_u.sanitize_filename(file_to_delete)
    if file_to_delete in PROTECTED_FILES:
        return "File not Allowed!", 403, {"Content-Type": "text/plain"}
    target = "/" + file_to_delete
    try:
        os.remove(target)
        d_u.print_and_store_log(f"File {target} deleted.")
        return Response(status_code=303, headers={"Location": "/file_management"})
    except OSError as e:
        return f"Error deleting file: {e}", 400, {"Content-Type": "text/plain"}

@ws_app.route('/UPLOAD_server', methods=['GET', 'POST'])
def upload_server(request):
    return w_u.serve_file_upload_page(IP_ADDR, WS_PORT), 200, {"Content-Type": "text/html"}

@ws_app.route('/upload_file', methods=['GET', 'POST'])
def upload_file(request):
    return Response(
        status_code=307,
        headers={"Location": f"http://{IP_ADDR}:{WS_PORT}/upload"}
    )

async def async_oled_show(IP_ADDR, PORT, error_vars):
    """ Async task for OLED updates (prevents I2C thread collisions) """
    while True:
        try:
            if o_s.oled_d:
                o_s.oled_d.fill(0)
                
                # 1. Puissance Réseau
                grid_w = s_m.current_grid_power
                o_s.oled_d.text(f"Reseau: {grid_w:.0f}W", 0, 0)
                
                # 2. Puissance Redirigée
                eq_w = s_m.equipment_power
                o_s.oled_d.text(f"Redir:  {eq_w:.0f}W", 0, 10)
                
                # 3. Temp ESP32
                esp_t = esp32.mcu_temperature()
                o_s.oled_d.text(f"ESP T:   {esp_t:.1f}C", 0, 20)
                
                # 4. Temp Sonde (Eau ou SSR)
                if s_m.current_water_temp is not None:
                    water_t = s_m.current_water_temp
                    o_s.oled_d.text(f"Eau T:   {water_t:.1f}C", 0, 30)
                elif s_m.current_ssr_temp is not None:
                    ssr_t = s_m.current_ssr_temp
                    o_s.oled_d.text(f"SSR T:   {ssr_t:.1f}C", 0, 30)
                else:
                    o_s.oled_d.text("Temp:    N/A", 0, 30)
                
                # 5. Mode Force
                force_txt = "ON" if s_m.force_mode_active else "OFF"
                o_s.oled_d.text(f"Force:   {force_txt}", 0, 40)
                
                # IP Info
                o_s.oled_d.text(f"IP: {IP_ADDR}", 0, 54)
                
                o_s.oled_d.show()
        except Exception as err:
            # Silently handle OLED errors (likely I2C timeout)
            pass
        await asyncio.sleep(1)

async def async_led_status():
    """ 
    Dynamic status LED on NeoPixel:
    - Blinking RED: Error (Safe state or Overheat)
    - Solid ORANGE: Boost active
    - Solid RED: Idle (No surplus)
    - Pulsing WHITE-to-GREEN: Diverting power
    """
    orange = (255, 165, 0)
    white = (255, 255, 255)
    green = (0, 255, 0)
    red = (255, 0, 0)

    while True:
        try:
            # 1. Error check
            max_esp_temp = getattr(c_v, 'MAX_ESP32_TEMP', 70.0)
            esp_overheat = esp32.mcu_temperature() >= max_esp_temp
            if s_m.safe_state or esp_overheat:
                e_l.internal_led_color_always(red)
                await asyncio.sleep(0.5)
                e_l.internal_led_off()
                await asyncio.sleep(0.5)
                continue

            # 2. Boost check
            if time.time() < s_m.boost_end_time:
                e_l.internal_led_color_always(orange)
                await asyncio.sleep(1)
                continue

            # 3. Surplus vs Idle
            if s_m.equipment_power <= 0:
                e_l.internal_led_color_always(red)
                await asyncio.sleep(1)
            else:
                # Pulsing proportional to power
                fraction = min(1.0, s_m.equipment_power / c_v.EQUIPMENT_MAX_POWER)
                # Mix White to Green based on intensity
                base_color = e_l.interpolate_color(white, green, fraction)
                
                # Fast pulse loop (approx 2 seconds)
                # Up
                for b in range(10, 101, 10):
                    p_c = e_l.interpolate_color((0,0,0), base_color, b/100.0)
                    e_l.internal_led_color_always(p_c)
                    await asyncio.sleep(0.1)
                # Down
                for b in range(100, 9, -10):
                    p_c = e_l.interpolate_color((0,0,0), base_color, b/100.0)
                    e_l.internal_led_color_always(p_c)
                    await asyncio.sleep(0.1)

        except Exception as err:
            d_u.print_and_store_log(f"LED status error: {err}")
            await asyncio.sleep(1)

async def watchdog_and_log_task(wdt):
    """ Feeds WDT every 5s and cleans logs every 2 hours """
    log_check_counter = 0
    while True:
        wdt.feed()
        log_check_counter += 5
        # 7200 seconds = 2 hours
        if log_check_counter >= 7200:
            log_check_counter = 0
            d_u.print_and_store_log("Performing scheduled log cleanup and MQTT restart...")
            # Check size and rotate/cleanup if exceeds 40KB
            d_u._rotate_log_if_needed(paths.LOG_FILE, 40 * 1024)
            m_c.restart()
            gc.collect()
        
        # Regular cleanup every 5s
        gc.collect()
        await asyncio.sleep(5)

async def _start_all(ip, port, error_vars, wifi_watchdog_enabled, wdt):
    # Start Fake Shelly if enabled
    if getattr(c_v, 'FAKE_SHELLY', False):
        import fake_shelly
        await fake_shelly.start_fake_shelly()

    asyncio.create_task(s_m.monitor_loop())
    asyncio.create_task(s_m.burst_control_loop())
    asyncio.create_task(s_m.history_loop())
    asyncio.create_task(async_oled_show(ip, port, error_vars))
    asyncio.create_task(async_led_status())
    asyncio.create_task(watchdog_and_log_task(wdt))
    
    # Start Captive Portal DNS if in AP mode
    if not c_v.E_WIFI:
        import domo_dns
        asyncio.create_task(domo_dns.run_dns(ip))
        
    await d_m.start_microdot_ws(ip, port, error_vars, wifi_watchdog_enabled)

def main():
    global IP_ADDR, WS_PORT, oled_d
    PORT = 80
    WS_PORT = 8080
    oled_d = None

    global ERR_SOCKET, ERR_WIFI, ERR_CON_WIFI, ERR_OLED
    ERR_SOCKET = False
    ERR_OLED = False
    ERR_WIFI = False
    ERR_CON_WIFI = False

    info_start = "#############--- Solaire Control ---#############"
    d_u.check_and_delete_if_too_big(paths.LOG_FILE, 20)
    d_u.print_and_store_log(info_start)
    d_u.set_freq(c_v.CPU_FREQ)

    oled_d = o_s.initialize_oled()
    if oled_d is None:
        ERR_OLED = True
    else:
        o_s.show_info_on_oled(info_start)
        oled_d.fill(0)

    s_m.init_ssr_relay()

    if c_v.E_WIFI is False:
        ap = d_w.setup_access_point()
        ERR_WIFI = ap is None
        IP_ADDR = c_v.AP_IP[0]
    else:
        result = d_w.connect_to_wifi()
        if result['success']:
            IP_ADDR = result['ip_address']
            d_u.set_time_with_ntp()
        else:
            ERR_CON_WIFI = True
            ap = d_w.setup_access_point()
            ERR_WIFI = ap is None
            IP_ADDR = c_v.AP_IP[0]

    _thread.start_new_thread(d_s_s.start_socket_server, (IP_ADDR, WS_PORT))

    error_vars = {
        'Openning Socket': ERR_SOCKET,
        'OLED Screen': ERR_OLED,
        'Wifi': ERR_WIFI,
        'Wifi Connection': ERR_CON_WIFI,
    }

    if not any(error_vars.values()):
        d_u.print_and_store_log("System OK")
    else:
        msgs = [k for k, v in error_vars.items() if v]
        d_u.print_and_store_log("Errors: " + ", ".join(msgs))

    if IP_ADDR and IP_ADDR != '0.0.0.0':
        try:
            # Initialize Watchdog (60 seconds) just before starting tasks
            wdt = WDT(timeout=60000)
            wifi_watchdog_enabled = c_v.E_WIFI and not ERR_CON_WIFI
            time.sleep(2)
            asyncio.run(_start_all(IP_ADDR, PORT, error_vars, wifi_watchdog_enabled, wdt))
        except Exception as err:
            d_u.print_and_store_log(f"Server error: {err}")
            time.sleep(5)
            reset()
        finally:
            asyncio.new_event_loop()
            reset()
    else:
        d_u.print_and_store_log('Trouble with WIFI')
        ERR_WIFI = True
        e_l.internal_led_blink(e_l.blue, e_l.led_off, 5, c_v.time_err)

if __name__ == "__main__":
    main()
