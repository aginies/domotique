# lilygo_solar/config_var.py
# Configuration for Lilygo Remote Monitor
# WARNING: This file is in .gitignore. The .bck file contains sample credentials.
# Replace the empty strings below with your own before deploying.

NAME = "LilygoSolar"

# on ESP32-S3 you must sold the RGB pin on the board!
I_LED_PIN = 48
CPU_FREQ = 160

# Wi-Fi Settings
E_WIFI = True
WIFI_SSID = "guibohome"
WIFI_PASSWORD = "ploplesmoules"

# AP Settings
AP_SSID = "W_LilygoSolar"
AP_PASSWORD = "12345678"
AP_HIDDEN_SSID = False
AP_CHANNEL = 6
AP_IP = ("192.168.66.11", "255.255.255.0", "192.168.66.1", "192.168.66.1")

# MQTT Settings
MQTT_IP = "10.0.1.101"

MQTT_PORT = 1883
MQTT_USER = "aginies"
MQTT_PASSWORD = "guiboaginies"
MQTT_TOPIC_SUB = "GuiboSolar/status_json"

# TZ Offset: 3600 for CET (Winter), 7200 for CEST (Summer)
TZ_OFFSET = 3600
