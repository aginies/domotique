# antoine@ginies.org
# GPL3

# Main name of the stuff to control
# As this will be used for WIFI name dont use space!
# No more than 13 characters or you won't see it on the ssd1306
DOOR = "Portail"

# on ESP32-S3 you must sold the RGB pin on the board!
# INTERNAL LED (PIN 48)
I_LED_PIN = 48

# CHOOSE AP OR EXISTING WIFI
# E_WIFI is True you will use a existing Wifi
# E_WIFI is False you will create a Wifi Access Point
E_WIFI = True # False
# WIFI CLIENT credentials
WIFI_SSID = "WIFISSID"
WIFI_PASSWORD = "WIFIPASSWORD"

# WIFI AP
AP_SSID = "W_Portail"
AP_PASSWORD = '12345678'
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

#RC 552 RFID
SCK_PIN = 18
MOSI_PIN = 11
MISO_PIN = 12
RST_PIN = 4
CS_PIN = 5

AUTHORIZED_CARDS = [
    [0x08, 0x24, 0x07, 0x95],
    [0xF5, 0x31, 0x8A, 0x04],
    ]

# NEED TO WRITE IT ON THE CARD
CARD_KEY = [0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC]

# Time in second for LED
time_ok = 0.05
time_err = 0.015

# OLED PIN
OLED_SCL_PIN = 15
OLED_SDA_PIN = 21
