# antoine@ginies.org
# GPL3
import socket
import network
import utime
from machine import Pin, SoftI2C
import esp32 # get MCU temp

import web_command as w_cmd
import esp32_led as e_l
import oled_ssd1306 as o_s
import config_var as c_v
import domo_wifi as d_w

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
            oled_d.text(IP_ADDR, 0, 30)
        else:
            oled_d.text(" ! Attention !", 0, 0)
            oled_d.text(" Wifi Pas OK", 0, 10)
            oled_d.text(" ! ** !", 0, 20)
            oled_d.text("Mode degrade!", 0, 30)
        oled_d.text(temp_mcu, 0, 40)
        oled_d.text(statusd, 0, 50)
        oled_d.show()

def ctrl_relay(which_one):
    """ relay 1 or 2 """
    try:
        e_l.internal_led_blink(e_l.pink, e_l.led_off, 3, c_v.time_ok)
        if which_one == 1:
            relay1.on()
            utime.sleep(0.2)
            relay1.off()
        else:
            relay2.on()
            utime.sleep(0.2)
            relay2.off()
    except OSError as err:
        print(err)
        relay1.value(0)
        relay2.value(0)
        e_l.internal_led_blink(e_l.pink, e_l.led_off, 5, time_err)
        ERR_CTRL_RELAY = True
        return None

def handle_client_connection(sock, new_ip):
    """ At client connection send html stuff """
    try:
        cl, addr = sock.accept()
        print('Client connecte depuis', addr)
        request = cl.recv(1024)
        #print(request)
        handle_request(request)
        html = w_cmd.create_html_response()
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html\r\n"
            "Connection: close\r\n"
            "\r\n"
            f"{html}")
        cl.sendall(response.encode())
        cl.close()
    except OSError:
        pass

def handle_request(request):
    """ Gérer les requêtes HTTP entrantes """
    global last_ctrl_relay_time
    current_time = utime.time()
    if b'/BP1_ACTIF' in request:
        if current_time - last_ctrl_relay_time > 3:
            print("BP1 activé")
            ctrl_relay(1)
            last_ctrl_relay_time = current_time
        else:
            print("BP1 Duplicate request seen...")
    elif b'/BP2_ACTIF' in request:
        if current_time - last_ctrl_relay_time > 3:
            print("BP2 activé")
            ctrl_relay(1)
            last_ctrl_relay_time = current_time
        else:
            print("BP2 Duplicate request seen...")
        ctrl_relay(2)

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
    ap = None
    # ERR_* are used to display LED color in case of...
    global ERR_SOCKET, ERR_OLED, ERR_WIFI, ERR_CTRL_RELAY, ERR_CON_WIFI
    ERR_SOCKET = False
    ERR_OLED = False
    ERR_WIFI = False
    ERR_CTRL_RELAY = False
    ERR_CON_WIFI = False

    oled_d = o_s.initialize_oled()
    # Start up info
    info_start = "Guibo Control"
    print(info_start)
    if oled_d:
        oled_d.text(info_start, 0, 0)
        info_control = "Version 1.0" 
        oled_d.text(info_control, 0, 10)
        oled_d.text('https://github.c', 0, 20)
        oled_d.text('om/aginies/domot', 0, 30)
        oled_d.text('ique', 0, 40)
        oled_d.text('ag@ginies.org', 0, 50)
        oled_d.show()
        utime.sleep(2)
    if oled_d:
        oled_d.fill(0)

    if c_v.E_WIFI is False:
        ap, ERR_WIFI = start_WIFI_ap()
        IP_ADDR = c_v.AP_IP[0]
    else:
        result_con_wifi = d_w.connect_to_wifi()
        if result_con_wifi['success']:
            IP_ADDR = result_con_wifi['ip_address']
        else:
            # Failed to connect to External Wifi
            # STarting the Wifi AP
            ERR_CON_WIFI = True
            ap, ERR_WIFI = start_WIFI_ap()
            if ap:
                o_s.oled_show_text_line("AP Wifi Ok", 0)
                IP_ADDR = c_v.AP_IP[0]
            else:
                o_s.oled_show_text_line("AP Wifi NOK!", 0)
    # Read the initial state of the door sensor
    door_state = door_sensor.value()
    print(f"Information sur {c_v.DOOR}:")
    if door_state == 0:
        statusd = "Status: OUVERT"
        led.value(1)
    elif door_state == 1:
        statusd = "Status: FERME"
        led.value(0)

    print(statusd)        
    o_s.oled_show_text_line(statusd, 10)

    #if ap:
    if IP_ADDR and IP_ADDR != '0.0.0.0':
        addr = socket.getaddrinfo(IP_ADDR, 80)[0][-1]
        sock = socket.socket()
        try:
            sock.bind(addr)
            o_s.oled_show_text_line("Socket Ok", 20)
            sock.listen(1)
            # Ne bloque pas le while :)
            sock.setblocking(False)
            o_s.oled_show_text_line("Listening Ok", 30)
            print('Listening on', addr)
            e_l.internal_led_blink(e_l.violet, e_l.led_off, 3, c_v.time_ok)
        except OSError as err:
            print(err)
            o_s.oled_show_text_line("Socket :80 NOK!", 20)
            e_l.internal_led_blink(e_l.violet, e_l.led_off, 5, c_v.time_err)
            ERR_SOCKET = True
    else:
        print('Problème Avec le WIFI')
        o_s.oled_show_text_line("WIFI AP NOK!", 30)
        ERR_WIFI = True
        e_l.internal_led_blink(e_l.blue, e_l.led_off, 5, time_err)

    # We are ready
    error_vars = [ERR_SOCKET, ERR_OLED, ERR_WIFI, ERR_CTRL_RELAY, ERR_CON_WIFI]
    if all(not error for error in error_vars):
        print("Système OK, pas d'erreur")
        e_l.french_flag()
    else:
        print("Au moins une erreur...")
    while True:
        prev_door_state = door_state
        door_state = door_sensor.value()
        check_and_display_error()

        if prev_door_state == 0 and door_state == 1:
            led.value(0)
            e_l.internal_led_color(e_l.red)
            statusd = "Status: FERME"
            print(statusd)

        elif prev_door_state == 1 and door_state == 0:
            led.value(1)
            e_l.internal_led_color(e_l.green)
            statusd = "Status: OUVERT"
            print(statusd)

        oled_constant_show()

        if sock:
            handle_client_connection(sock, c_v.AP_IP[0])

        utime.sleep(0.1)
        
if __name__ == "__main__":
    main()
