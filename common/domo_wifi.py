# antoine@ginies.org
# GPL3

""" WIFI network """

import network
import utime
import asyncio
import oled_ssd1306 as o_s
import esp32_led as e_l
import config_var as c_v
import domo_utils as d_u

def deactivate_active_interfaces():
    """ Disable network interface """
    sta_if = network.WLAN(network.STA_IF)
    if sta_if.active():
        sta_if.active(False)
    ap_if = network.WLAN(network.AP_IF)
    if ap_if.active():
        ap_if.active(False)

def connect_to_wifi():
    """ Connect to an existing network - reverted to stable version """
    deactivate_active_interfaces()
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.active():
        sta_if.active(True)
    
    d_u.print_and_store_log(f"Connecting to WiFi SSID: {c_v.WIFI_SSID}...")
    try:
        sta_if.connect(c_v.WIFI_SSID, c_v.WIFI_PASSWORD)
    except OSError as err:
        d_u.print_and_store_log(f"WiFi Connect Error: {err}")
        return {'success': False, 'ERR_WIFI': True}

    max_attempts = 10
    attempt = 0
    while not sta_if.isconnected() and attempt < max_attempts:
        attempt += 1
        info = f"Connect Wifi {attempt}/{max_attempts}"
        d_u.print_and_store_log(info)
        if o_s.oled_d:
            o_s.oled_show_text_line(info, 10)
        utime.sleep(3)

    if o_s.oled_d:
        o_s.oled_d.fill(1)
        o_s.oled_d.show()
        utime.sleep(0.1)
        o_s.oled_d.fill(0)
        o_s.oled_d.show()

    if sta_if.isconnected():
        # Disable power management after connection for stability
        try:
            sta_if.config(pm=network.WLAN.PM_NONE)
        except Exception:
            pass
            
        config = sta_if.ifconfig()
        d_u.print_and_store_log(f"Connected to {c_v.WIFI_SSID}!")
        d_u.print_and_store_log(f"IP: {config[0]}, Gateway: {config[2]}")
        e_l.internal_led_blink(e_l.white, e_l.led_off, 3, c_v.time_ok)
        return {'success': True, 'ip_address': config[0]}
    else:
        d_u.print_and_store_log("WiFi Connection Failed!")
        e_l.internal_led_blink(e_l.white, e_l.led_off, 5, c_v.time_err)
        d_u.print_and_store_log("Falling back to Access Point mode")
        return {'success': False, 'ERR_WIFI': True}
    
def setup_access_point():
    """ AP configuration """
    deactivate_active_interfaces()
    try:
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        # Configurer le point d'accès
        ap.ifconfig(c_v.AP_IP)
        ap.config(essid=c_v.AP_SSID,
                  authmode=network.AUTH_WPA_WPA2_PSK,
                  password=c_v.AP_PASSWORD,
                  hidden=c_v.AP_HIDDEN_SSID,
                  channel=c_v.AP_CHANNEL)
        
        d_u.print_and_store_log(f"Starting Access Point: {c_v.AP_SSID}")
        
        max_attempts = 5
        attempt = 0
        while not ap.active() and attempt < max_attempts:
            attempt += 1
            info = f"Starting AP {attempt}/{max_attempts}"
            d_u.print_and_store_log(info)
            if o_s.oled_d:
                o_s.oled_show_text_line(info, 10)
            utime.sleep(1)

        if ap.active():
            d_u.print_and_store_log(f'WIFI Access Point active! IP: {ap.ifconfig()[0]}')
            e_l.internal_led_blink(e_l.blue, e_l.led_off, 3, c_v.time_ok)
        return ap
    except OSError as err:
        d_u.print_and_store_log(f"AP Setup Error: {err}")
        e_l.internal_led_blink(e_l.blue, e_l.led_off, 5, c_v.time_err)
        return None

async def wifi_watchdog(check_interval_s=30, error_vars=None):
    """ Periodically verify STA connectivity and reconnect with exponential backoff. """
    if not c_v.E_WIFI:
        return
    sta_if = network.WLAN(network.STA_IF)
    backoff = check_interval_s
    while True:
        await asyncio.sleep(backoff)
        try:
            if sta_if.isconnected():
                backoff = check_interval_s
                continue
            d_u.print_and_store_log("WIFI watchdog: connection dropped, reconnecting")
            if error_vars is not None:
                error_vars['Wifi Connection'] = True
            try:
                sta_if.active(True)
                sta_if.connect(c_v.WIFI_SSID, c_v.WIFI_PASSWORD)
            except OSError as err:
                d_u.print_and_store_log(f"WIFI watchdog: connect error: {err}")
            for _ in range(10):
                await asyncio.sleep(1)
                if sta_if.isconnected():
                    break
            if sta_if.isconnected():
                d_u.print_and_store_log(f"WIFI watchdog: reconnected, IP {sta_if.ifconfig()[0]}")
                if error_vars is not None:
                    error_vars['Wifi Connection'] = False
                backoff = check_interval_s
            else:
                d_u.print_and_store_log("WIFI watchdog: still disconnected, backing off")
                backoff = min(backoff * 2, 300)
        except Exception as err:
            d_u.print_and_store_log(f"WIFI watchdog error: {err}")
