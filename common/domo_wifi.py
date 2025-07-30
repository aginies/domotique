# antoine@ginies.org
# GPL3

""" WIFI network """

import network
import utime
import oled_ssd1306 as o_s
import esp32_led as e_l
import config_var as c_v

def deactivate_active_interfaces():
    """ Désactiver les interfaces réseau actives """
    sta_if = network.WLAN(network.STA_IF)
    if sta_if.active():
        sta_if.active(False)
    ap_if = network.WLAN(network.AP_IF)
    if ap_if.active():
        ap_if.active(False)

def connect_to_wifi():
    """ Connecte a un réseau Wifi Existant"""
    deactivate_active_interfaces()
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.active():
        sta_if.active(True)
    
    max_attempts = 5
    attempt = 0
    try:
        sta_if.connect(c_v.WIFI_SSID, c_v.WIFI_PASSWORD)
    except OSError as err:
        print(err)
    while not sta_if.isconnected() and attempt < max_attempts:
        attempt += 1
        info = "Connect Wifi "+str(attempt)+"/"+str(max_attempts)
        print(info)
        if o_s.oled_d:
            o_s.oled_d.fill(0)
            o_s.oled_show_text_line(info, 10)
        utime.sleep(2)
    if o_s.oled_d:
        o_s.oled_d.fill(1)
        o_s.oled_d.fill(0)
    if sta_if.isconnected():
        print("Connecte au WiFi OK")
        print("Config Réseau:", sta_if.ifconfig())
        e_l.internal_led_blink(e_l.white, e_l.led_off, 3, c_v.time_ok)
        return {'success': True, 'ip_address': sta_if.ifconfig()[0]}
    else:
        print("Connecte au WiFi NOK!")
        e_l.internal_led_blink(e_l.white, e_l.led_off, 5, c_v.time_err)
        ERR_WIFI = True
        print("Wifi AP Forcé")
        return {'success': False, 'ERR_WIFI': ERR_WIFI}
    
def setup_access_point():
    """ Configurer le point d'accès """
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
            print(info)
            o_s.oled_d.fill(0)
            o_s.oled_show_text_line(info, 10)
            utime.sleep(2)

        print('Point d\'accès WIFI créé avec l\'adresse IP:', ap.ifconfig()[0])
        #o_s.oled_show_text_line("AP Wifi Ok", 0)
        e_l.internal_led_blink(e_l.blue, e_l.led_off, 3, c_v.time_ok)
        return ap
    except OSError as err:
        #o_s.oled_show_text_line("AP Wifi NOK", 0)
        e_l.internal_led_blink(e_l.blue, e_l.led_off, 5, c_v.time_err)
