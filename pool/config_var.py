# antoine@ginies.org
# GPL3

# Main name of the stuff to control
# As this will be used for WIFI name dont use space!
# No more than 13 characters or you won't see it on the ssd1306
DOOR = "Piscine"

# Name of the button
nom_bp1 = "Ouverture"
nom_bp2 = "Fermeture"
time_adjust = 2
nom_open_b = "Ajustement Ouverture "
nom_close_b = "Ajustement Fermeture "

# on ESP32-S3 you must sold the RGB pin on the board!
# INTERNAL LED (PIN 48)
I_LED_PIN = 48

# ESP32-S3 CPU freq
CPU_FREQ=240

# Timing top open or close the curtain in seconds
time_to_close = 156
time_to_open = 168

# CHOOSE AP OR EXISTING WIFI
# E_WIFI is True you will use a existing Wifi
# E_WIFI is False you will create a Wifi Access Point
E_WIFI = True # False
# WIFI CLIENT credentials
WIFI_SSID = "WIFISSID"
WIFI_PASSWORD = "WIFIPASSWORD"

# WIFI AP
AP_SSID = "W_Piscine"
AP_PASSWORD = '12345678'
AP_HIDDEN_SSID = False # True
AP_CHANNEL = 6
AP_IP = ('192.168.66.1', '255.255.255.0', '192.168.66.1', '192.168.66.1')

#### PIN CONFIG
# LED EXTERNAL
LED_PIN = 12

# OLED PIN
OLED_SCL_PIN = 7
OLED_SDA_PIN = 18

# DOOR MAGNET
DOOR_SENSOR_PIN = 10

# RELAY for BP1 and BP2
RELAY1_PIN = 14
RELAY2_PIN = 17

# Time in second for LED
time_ok = 0.1
time_err = 0.3

# PIN CODE TO CLOSE
PIN_CODE = 1234
