# Main name of the stuff to control
# As this will be used for WIFI name dont use space!
# No more than 13 characters or you won't see it on the ssd1306
DOOR = "Piscine"

# Name of the button
nom_bp1 = "Ouverture"
nom_bp2 = "Fermeture"

# on ESP32-S3 you must sold the RGB pin on the board!
# INTERNAL LED (PIN 48)
I_LED_PIN = 48

# Timing top open or close the curtain in seconds
time_to_close = 13
time_to_open = 10

# CHOOSE AP OR EXISTING WIFI
# E_WIFI is True you will use a existing Wifi
# E_WIFI is False you will create a Wifi Access Point
E_WIFI = True # False
# WIFI CLIENT credentials
WIFI_SSID = "SSSID"
WIFI_PASSWORD = "WIFIPASSWORD"

# WIFI AP
AP_SSID = "W_Piscine"
AP_PASSWORD = 'JESAISPAS!'
AP_HIDDEN_SSID = False # True
AP_CHANNEL = 6
AP_IP = ('192.168.66.1', '255.255.255.0', '192.168.66.1', '192.168.66.1')

#### PIN CONFIG
# LED EXTERNAL
LED_PIN = 18

# DOOR MAGNET
DOOR_SENSOR_PIN = 10

# RELAY for BP1 and BP2
RELAY1_PIN = 15
RELAY2_PIN = 16

# Time in second for LED
time_ok = 0.1
time_err = 0.3
