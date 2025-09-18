# antoine@ginies.org
# GPL3

""" WIFI network """

import network
import utime
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
    """ Connect to an existing network """
    deactivate_active_interfaces()
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.active():
        sta_if.active(True)
    
    max_attempts = 5
    attempt = 0
    try:
        sta_if.connect(c_v.WIFI_SSID, c_v.WIFI_PASSWORD)
    except OSError as err:
        d_u.print_and_store_log(err)
    while not sta_if.isconnected() and attempt < max_attempts:
        attempt += 1
        info = "Connect Wifi "+str(attempt)+"/"+str(max_attempts)
        d_u.print_and_store_log(info)
        if o_s.oled_d:
            o_s.oled_d.fill(0)
            o_s.oled_show_text_line(info, 10)
        utime.sleep(3)
    if o_s.oled_d:
        o_s.oled_d.fill(1)
        o_s.oled_d.fill(0)
    if sta_if.isconnected():
        d_u.print_and_store_log(f"Connection to WiFi {c_v.WIFI_SSID} OK")
        d_u.print_and_store_log(f"Network Config: {sta_if.ifconfig()}")
        e_l.internal_led_blink(e_l.white, e_l.led_off, 3, c_v.time_ok)
        return {'success': True, 'ip_address': sta_if.ifconfig()[0]}
    else:
        d_u.print_and_store_log("Connection to WiFi NOK!")
        e_l.internal_led_blink(e_l.white, e_l.led_off, 5, c_v.time_err)
        ERR_WIFI = True
        d_u.print_and_store_log("Forcing AP Wifi")
        return {'success': False, 'ERR_WIFI': ERR_WIFI}
    
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
        max_attempts = 5
        attempt = 0
        while not ap.active() and attempt < max_attempts:
            attempt += 1
            info = "Trying AP Wifi "+str(attempt)+"/"+str(max_attempts)
            d_u.print_and_store_log(info)
            o_s.oled_d.fill(0)
            o_s.oled_show_text_line(info, 10)
            utime.sleep(2)

        d_u.print_and_store_log(f'WIFI Access Point: {c_v.AP_SSID}, IP adress: {ap.ifconfig()[0]}')
        e_l.internal_led_blink(e_l.blue, e_l.led_off, 3, c_v.time_ok)
        return ap
    except OSError as err:
        e_l.internal_led_blink(e_l.blue, e_l.led_off, 5, c_v.time_err)
