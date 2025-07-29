# antoine@ginies.org
# GPL3
import socket
import network
import utime
from machine import Pin, SoftI2C
import ssd1306 # the small oled screen
import esp32 # get MCU temp
from neopixel import NeoPixel

# Main name of the stuff to control
# As this will be used for WIFI name dont use space!
# No more than 13 characters or you won't see it on the ssd1306
DOOR = "Portail"

# CHOOSE AP OR EXISTING WIFI
# E_WIFI is True you will use a existing Wifi
# E_WIFI is False you will create a Wifi Access Point
E_WIFI = True # False

# WIFI AP
AP_SSID = "WIFI_" + DOOR
AP_PASSWORD = "APPASSWORD"
AP_IP = ('192.168.66.1', '255.255.255.0', '192.168.66.1', '192.168.66.1')
HIDDEN_SSID = False # True

# WIFI CLIENT
# credentials
WIFI_SSID = "YOURSSID"
WIFI_PASSWORD = "YOURSSIDPASSWORD"

# INTERNAL LED (PIN 48)
# on ESP32-S3 you must sold the RGB pin on the board!
I_LED_PIN = 48
I_led = Pin(I_LED_PIN, Pin.OUT)
np = NeoPixel(I_led, 1)
# One color per function to find the root cause
green = (0, 255 , 0) # OLED display
red = (255, 0, 0) # error?
blue = (0, 0, 255) # setup Wifi access point
violet = (154, 14, 234) # socket bind to address
pink = (255, 192, 203) # relay (web button to control motor)
white = (255, 255, 255) # connect to existing Wifi
led_off = (0, 0, 0)
# Time in second
time_ok = 0.1
time_err = 0.3

# LED EXTERNAL
LED_PIN = 18
led = Pin(LED_PIN, Pin.OUT)

# DOOR MAGNET
DOOR_SENSOR_PIN = 10
door_sensor = Pin(DOOR_SENSOR_PIN, Pin.IN, Pin.PULL_UP)
door_state = door_sensor.value()
prev_door_state = door_state

# RELAY for BP1 and BP2
# Be sure to put max power to the pin to control the relay
last_ctrl_relay_time = 0
RELAY1_PIN = 15
relay1 = Pin(RELAY1_PIN, Pin.OUT, drive=Pin.DRIVE_3)
relay1.off()
RELAY2_PIN = 16
relay2 = Pin(RELAY2_PIN, Pin.OUT, drive=Pin.DRIVE_3)
relay2.off()

# ESP32 Pin assignment OLED
i2c = SoftI2C(scl=Pin(36), sda=Pin(21))
oled_width = 128
oled_height = 64

def internal_led_blink(color1, color2, NB, timing):
    """ rules is: blink 3 times for OK, 5 times for Error/NOK"""
    for _ in (range(0, NB)):  
        np[0] = color1
        np.write()
        utime.sleep(timing)
        np[0] = color2
        np.write()
        utime.sleep(timing)
        internal_led_off()

def french_flag():
    times = 0.8
    internal_led_blink(blue, white, 1, times)
    np[0] = red; np.write(); utime.sleep(times)
    internal_led_off()

def internal_led_color(color):
    """ easy way to change the color led """
    internal_led_color_always(color)
    utime.sleep(0.1)
    internal_led_off()

def internal_led_color_always(color):
    """ Always show the color """
    np[0] = color
    np.write()

def internal_led_off():
    """ Led is off """
    np[0] = led_off
    np.write()

def check_and_display_error():
    """ In case of error display quickly the error color """
    if ERR_SOCKET is True:
        internal_led_blink(violet, led_off, 1, 0.1)
    if ERR_OLED is True:
        internal_led_blink(green, led_off, 1, 0.1)
    if ERR_WIFI is True:
        internal_led_blink(blue, led_off, 1, 0.1)
    if ERR_CON_WIFI is True:
        internal_led_blink(white, led_off, 1, 0.1)
    if ERR_CTRL_RELAY is True:
        internal_led_blink(pink, led_off, 1, 0.1)

def initialize_oled():
    """ Attempt to initialize the SSD1306 display """
    try:
        oled_d = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)
        print("Ecran OLED Ok")
        internal_led_blink(green, led_off, 3, time_ok)
        oled_d.fill(0)
        return oled_d
    except OSError as err:
        print(f"Ecran OLED NOK: {err}")
        internal_led_blink(green, led_off, 5, time_err)
        ERR_OLED = True

def oled_show_text_line(text, line):
    """ Show a text on a specific line """
    if oled_d:
        oled_d.text(text, 0, line)
        oled_d.text('guibo.com', 0, 50)
        oled_d.show()
        utime.sleep(0.5)

def oled_constant_show():
    """ Data always displayed """
    if oled_d:
        mcu_t = esp32.mcu_temperature()
        temp_mcu = "Temp ESP32: " + str(mcu_t) + "C"
        oled_d.fill(0)
        SSID = AP_SSID
        if E_WIFI is True:
            if ERR_CON_WIFI is False:
                SSID = WIFI_SSID
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

def deactivate_active_interfaces():
    """ Désactiver les interfaces réseau actives """
    sta_if = network.WLAN(network.STA_IF)
    if sta_if.active():
        sta_if.active(False)
    ap_if = network.WLAN(network.AP_IF)
    if ap_if.active():
        ap_if.active(False)

def connect_to_wifi():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.active():
        sta_if.active(True)
    
    max_attempts = 5
    attempt = 0
    try:
        sta_if.connect(WIFI_SSID, WIFI_PASSWORD)
    except OSError as err:
        print(err)

    while not sta_if.isconnected() and attempt < max_attempts:
        attempt += 1
        info = "Tentative Wifi "+str(attempt)+"/"+str(max_attempts)
        print(info)
        if oled_d:
            oled_d.fill(0)
            oled_show_text_line(info, 10)
        utime.sleep(2)
    if oled_d:
        oled_d.fill(1)
        oled_d.fill(0)
    if sta_if.isconnected():
        print("Connecte au WiFi OK")
        print("Config Réseau:", sta_if.ifconfig())
        internal_led_blink(white, led_off, 3, time_ok)
        return {'success': True, 'ip_address': sta_if.ifconfig()[0]}
    else:
        print("Connecte au WiFi NOK!")
        internal_led_blink(white, led_off, 5, time_err)
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
        ap.ifconfig(AP_IP)
        ap.config(essid=AP_SSID,
                  authmode=network.AUTH_WPA_WPA2_PSK,
                  password=AP_PASSWORD,
                  hidden=HIDDEN_SSID,
                  channel=6)
        max_attempts = 5
        attempt = 0
        while not ap.active() and attempt < max_attempts:
            attempt += 1
            info = "Trying AP Wifi "+str(attempt)+"/"+str(max_attempts)
            print(info)
            oled_d.fill(0)
            oled_show_text_line(info, 10)
            utime.sleep(2)

        print(f"Point d\'accès WIFI créé: {AP_SSID}")
        print("avec l'adresse IP:", ap.ifconfig()[0])
        #oled_show_text_line("AP Wifi Ok", 0)
        internal_led_blink(blue, led_off, 3, time_ok)
        return ap
    except OSError as err:
        #oled_show_text_line("AP Wifi NOK", 0)
        internal_led_blink(blue, led_off, 5, time_err)

def ctrl_relay(which_one):
    """ relay 1 or 2 """
    try:
        internal_led_blink(pink, led_off, 3, time_ok)
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
        internal_led_blink(pink, led_off, 5, time_err)
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
        html = create_html_response()
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
 
def create_html_response():
    """ Créer la réponse HTML """
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contrôle</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            color: #333;
        }}
        .container {{
            text-align: center;
            background: white;
            padding: 20px 40px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }}
        h1 {{
            color: #444;
            margin-bottom: 30px;
        }}
        .button {{
            display: inline-block;
            margin: 10px;
            padding: 24px 40px;
            font-size: 20px;
            color: white;
            background-color: #007BFF;
            border: none;
            border-radius: 5px;
            text-decoration: none;
            cursor: pointer;
            transition: background-color 0.3s;
        }}
        .button:hover {{
            background-color: #0056b3;
        }}
        .button:disabled {{
            background-color: grey;
            cursor: not-allowed;
        }}
        .button.clicked {{
            background-color: red;
        }}
        .status {{
            margin: 20px auto;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background-color: 'green';
        }}
        .footer {{
            position: fixed;
            bottom: 10px;
            width: 100%;
            text-align: center;
            color: #fff;
            background-color: rgba(0, 0, 0, 0.5);
            padding: 10px;
        }}
        #timestamp {{
            margin-top: 20px;
            font-size: 16px;
            color: #555;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Contrôle """ + DOOR + """</h1>
        <p>Toujours <b>contrôler</b> visuellement le <b>""" + DOOR + """</b></p>
        <button id="BP1" class="button">BP1</button>
        <div id="timestamp"></div>
        <div id="user-agent"></div>
    <script>
        document.getElementById('BP1').addEventListener('click', function() {
            fetch('/BP1_ACTIF', { method: 'POST' })
                .then(response => response.text())
                .then(data => console.log(data));
             setTimeout(() => {{
                button.classList.remove('clicked');
            }}, 1000);
            const userAgent = navigator.userAgent;
            document.getElementById('user-agent').textContent = 'User Agent: ' + navigator.userAgent;
            const now = new Date();
            const timestamp = now.toLocaleString();
            document.getElementById('timestamp').textContent = 'Dernier clic: ' + timestamp;
        });
    </script>
   <!--     <a href="/BP1_ACTIF"><button class="button">BP1</button></a>
    <a href="/BP2_ACTIF">
        <button class="button" disabled>BP2</button></a>
        -->
    </div>
    <div class="footer">
        <p>antoine@ginies.org</p>
    </div>
</body>
</html>"""
    return html

def start_WIFI_ap():
    ap = setup_access_point()
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

    oled_d = initialize_oled()
    # Start up info
    info_start = "Door Control"
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

    if E_WIFI is False:
        ap, ERR_WIFI = start_WIFI_ap()
        IP_ADDR = AP_IP[0]
    else:
        result_con_wifi = connect_to_wifi()
        if result_con_wifi['success']:
            IP_ADDR = result_con_wifi['ip_address']
        else:
            # Failed to connect to External Wifi
            # STarting the Wifi AP
            ERR_CON_WIFI = True
            ap, ERR_WIFI = start_WIFI_ap()
            if ap:
                oled_show_text_line("AP Wifi Ok", 0)
                IP_ADDR = AP_IP[0]
            else:
                oled_show_text_line("AP Wifi NOK!", 0)
    # Read the initial state of the door sensor
    door_state = door_sensor.value()
    print(f"Information sur {DOOR}:")
    if door_state == 0:
        statusd = "Status: OUVERT"
        led.value(1)
    elif door_state == 1:
        statusd = "Status: FERME"
        led.value(0)

    print(statusd)        
    oled_show_text_line(statusd, 10)

    #if ap:
    if IP_ADDR and IP_ADDR != '0.0.0.0':
        addr = socket.getaddrinfo(IP_ADDR, 80)[0][-1]
        sock = socket.socket()
        try:
            sock.bind(addr)
            oled_show_text_line("Socket Ok", 20)
            sock.listen(1)
            # Ne bloque pas le while :)
            sock.setblocking(False)
            oled_show_text_line("Listening Ok", 30)
            print('Listening on', addr)
            internal_led_blink(violet, led_off, 3, time_ok)
        except OSError as err:
            print(err)
            oled_show_text_line("Socket :80 NOK!", 20)
            internal_led_blink(violet, led_off, 5, time_err)
            ERR_SOCKET = True
    else:
        print('Problème Avec le WIFI')
        oled_show_text_line("WIFI AP NOK!", 30)
        ERR_WIFI = True
        internal_led_blink(blue, led_off, 5, time_err)

    # We are ready
    error_vars = [ERR_SOCKET, ERR_OLED, ERR_WIFI, ERR_CTRL_RELAY, ERR_CON_WIFI]
    #ERR_CON_WIFI = True
    if all(not error for error in error_vars):
        print("Système OK, pas d'erreur")
        french_flag()
    else:
        print("Au moins une erreur...")
    while True:
        prev_door_state = door_state
        door_state = door_sensor.value()
        check_and_display_error()

        if prev_door_state == 0 and door_state == 1:
            led.value(0)
            internal_led_color(red)
            statusd = "Status: FERME"
            print(statusd)

        elif prev_door_state == 1 and door_state == 0:
            led.value(1)
            internal_led_color(green)
            statusd = "Status: OUVERT"
            print(statusd)

        oled_constant_show()

        if sock:
            handle_client_connection(sock, AP_IP[0])

        utime.sleep(0.1)
        
if __name__ == "__main__":
    main()
