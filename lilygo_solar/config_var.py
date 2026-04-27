# lilygo_solar/config_var.py
# Configuration for Lilygo Remote Monitor

NAME = "LilygoSolar"

# on ESP32-S3 you must sold the RGB pin on the board!
I_LED_PIN = 48
CPU_FREQ = 160

# Wi-Fi Settings
E_WIFI = True
WIFI_SSID = ""
WIFI_PASSWORD = ""

# AP Settings
AP_SSID = "W_LilygoSolar"
AP_PASSWORD = "12345678"
AP_HIDDEN_SSID = False
AP_CHANNEL = 6
AP_IP = ('192.168.66.11', '255.255.255.0', '192.168.66.11', '192.168.66.11')

# MQTT Settings
MQTT_IP = "10.0.1.101"

MQTT_PORT = 1883
MQTT_USER = ""
MQTT_PASSWORD = ""
MQTT_TOPIC_SUB = "GuiboSolar/status_json"

# TZ Offset: 3600 for CET (Winter), 7200 for CEST (Summer)
TZ_OFFSET = 3600
