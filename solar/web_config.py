# antoine@ginies.org
# GPL3

import config_var
import paths

try:
    with open(paths.VERSION_FILE, 'r') as file:
        version = file.read().strip()
except OSError:
    version = "unknown"

def get_config():
    import sys
    if 'config_var' in sys.modules:
        del sys.modules['config_var']
    import config_var
    return {
        "NAME": config_var.NAME,
        "E_WIFI": config_var.E_WIFI,
        "WIFI_SSID": config_var.WIFI_SSID,
        "WIFI_PASSWORD": config_var.WIFI_PASSWORD,
        "AP_SSID": config_var.AP_SSID,
        "AP_PASSWORD": config_var.AP_PASSWORD,
        "AP_HIDDEN_SSID": config_var.AP_HIDDEN_SSID,
        "AP_CHANNEL": config_var.AP_CHANNEL,
        "AP_IP": config_var.AP_IP,
        "I_LED_PIN": config_var.I_LED_PIN,
        "SSR_PIN": config_var.SSR_PIN,
        "RELAY_PIN": config_var.RELAY_PIN,
        "OLED_SCL_PIN": config_var.OLED_SCL_PIN,
        "OLED_SDA_PIN": config_var.OLED_SDA_PIN,
        "CPU_FREQ": config_var.CPU_FREQ,
        "time_ok": config_var.time_ok,
        "time_err": config_var.time_err,
        "SHELLY_EM_IP": config_var.SHELLY_EM_IP,
        "E_SHELLY_MQTT": config_var.E_SHELLY_MQTT,
        "SHELLY_MQTT_TOPIC": config_var.SHELLY_MQTT_TOPIC,
        "POLL_INTERVAL": config_var.POLL_INTERVAL,
        "EQUIPMENT_NAME": config_var.EQUIPMENT_NAME,
        "EQUIPMENT_MAX_POWER": config_var.EQUIPMENT_MAX_POWER,
        "DEADBAND_W": getattr(config_var, 'DEADBAND_W', 30),
        "RAMP_DOWN_NUDGE": getattr(config_var, 'RAMP_DOWN_NUDGE', 0.01),
        "TRANSIENT_RESET_THRESHOLD": getattr(config_var, 'TRANSIENT_RESET_THRESHOLD', 200),
        "EXPORT_SETPOINT": config_var.EXPORT_SETPOINT,
        "PID_KP": config_var.PID_KP,
        "PID_KI": config_var.PID_KI,
        "BURST_PERIOD": config_var.BURST_PERIOD,
        "MIN_POWER_THRESHOLD": config_var.MIN_POWER_THRESHOLD,
        "MIN_OFF_TIME": config_var.MIN_OFF_TIME,
        "E_DS18B20": config_var.E_DS18B20,
        "DS18B20_PIN": config_var.DS18B20_PIN,
        "EQUIPMENT_MAX_TEMP": config_var.EQUIPMENT_MAX_TEMP,
        "EQUIPMENT_TARGET_TEMP": config_var.EQUIPMENT_TARGET_TEMP,
        "E_SSR_TEMP": getattr(config_var, 'E_SSR_TEMP', False),
        "SSR_MAX_TEMP": getattr(config_var, 'SSR_MAX_TEMP', 75.0),
        "SHELLY_TIMEOUT": config_var.SHELLY_TIMEOUT,
        "FORCE_EQUIPMENT": config_var.FORCE_EQUIPMENT,
        "E_FORCE_WINDOW": config_var.E_FORCE_WINDOW,
        "FORCE_START": config_var.FORCE_START,
        "FORCE_END": config_var.FORCE_END,
        "NIGHT_START": getattr(config_var, 'NIGHT_START', "22:00"),
        "NIGHT_END": getattr(config_var, 'NIGHT_END', "05:50"),
        "NIGHT_POLL_INTERVAL": getattr(config_var, 'NIGHT_POLL_INTERVAL', 15),
        "E_MQTT": config_var.E_MQTT,
        "MQTT_IP": config_var.MQTT_IP,
        "MQTT_PORT": config_var.MQTT_PORT,
        "MQTT_USER": config_var.MQTT_USER,
        "MQTT_PASSWORD": config_var.MQTT_PASSWORD,
        "MQTT_NAME": config_var.MQTT_NAME,
        "MQTT_RETAIN": config_var.MQTT_RETAIN,
        "MQTT_KEEPALIVE": config_var.MQTT_KEEPALIVE,
        "MQTT_DISCOVERY_PREFIX": getattr(config_var, 'MQTT_DISCOVERY_PREFIX', 'homeassistant'),
        "WIFI_STATIC_IP": getattr(config_var, 'WIFI_STATIC_IP', ""),
        "WIFI_SUBNET": getattr(config_var, 'WIFI_SUBNET', ""),
        "WIFI_GATEWAY": getattr(config_var, 'WIFI_GATEWAY', ""),
        "WIFI_DNS": getattr(config_var, 'WIFI_DNS', ""),
        "E_JSY": config_var.E_JSY,
        "JSY_UART_ID": config_var.JSY_UART_ID,
        "JSY_TX": config_var.JSY_TX,
        "JSY_RX": config_var.JSY_RX,
        "E_FAN": getattr(config_var, 'E_FAN', False),
        "FAN_PIN": getattr(config_var, 'FAN_PIN', 5),
        "FAN_TEMP_OFFSET": getattr(config_var, 'FAN_TEMP_OFFSET', 10),
        "FAKE_SHELLY": getattr(config_var, 'FAKE_SHELLY', False),
        "VERSION": version,
    }

def serve_config_page(IP_ADDR, WS_PORT, reboot_needed=False):
    config = get_config()
    selected_options = {
        'selected_20':  'selected' if config_var.CPU_FREQ == 20  else '',
        'selected_40':  'selected' if config_var.CPU_FREQ == 40  else '',
        'selected_80':  'selected' if config_var.CPU_FREQ == 80  else '',
        'selected_160': 'selected' if config_var.CPU_FREQ == 160 else '',
        'selected_240': 'selected' if config_var.CPU_FREQ == 240 else '',
    }
    wifi_config = {
        'external_wifi_yes': 'selected' if config_var.E_WIFI is True  else '',
        'external_wifi_no':  'selected' if config_var.E_WIFI is False else '',
        'force_equipment_yes': 'selected' if config_var.FORCE_EQUIPMENT is True   else '',
        'force_equipment_no':  'selected' if config_var.FORCE_EQUIPMENT is False  else '',
        'force_window_yes':    'selected' if getattr(config_var, 'E_FORCE_WINDOW', False) is True  else '',
        'force_window_no':     'selected' if getattr(config_var, 'E_FORCE_WINDOW', False) is False else '',
        'ds18b20_yes':       'selected' if config_var.E_DS18B20 is True   else '',
        'ds18b20_no':        'selected' if config_var.E_DS18B20 is False  else '',
        'ssr_temp_yes':      'selected' if getattr(config_var, 'E_SSR_TEMP', False) is True  else '',
        'ssr_temp_no':       'selected' if getattr(config_var, 'E_SSR_TEMP', False) is False else '',
        'jsy_yes':           'selected' if getattr(config_var, 'E_JSY', False) is True  else '',
        'jsy_no':            'selected' if getattr(config_var, 'E_JSY', False) is False else '',
        'mqtt_yes':          'selected' if config_var.E_MQTT is True  else '',
        'mqtt_no':           'selected' if config_var.E_MQTT is False else '',
        'shelly_mqtt_yes':   'selected' if getattr(config_var, 'E_SHELLY_MQTT', False) is True  else '',
        'shelly_mqtt_no':    'selected' if getattr(config_var, 'E_SHELLY_MQTT', False) is False else '',
        'mqtt_retain_yes':   'selected' if config_var.MQTT_RETAIN is True  else '',
        'mqtt_retain_no':    'selected' if config_var.MQTT_RETAIN is False else '',
        'fan_yes':           'selected' if getattr(config_var, 'E_FAN', False) is True  else '',
        'fan_no':            'selected' if getattr(config_var, 'E_FAN', False) is False else '',
        'fake_shelly_yes':   'selected' if getattr(config_var, 'FAKE_SHELLY', False) is True  else '',
        'fake_shelly_no':    'selected' if getattr(config_var, 'FAKE_SHELLY', False) is False else '',
        'IP_ADDR': IP_ADDR,
        'WS_PORT': WS_PORT,
        'reboot_banner': '<div class="reboot-banner">Configuration sauvegardée. Redémarrage nécessaire pour appliquer les changements.</div>' if reboot_needed else '',
    }

    try:
        with open('web_config.html', 'r') as f:
            tmpl = f.read()
        return tmpl.format(**config, **selected_options, **wifi_config)
    except OSError:
        return "Error: web_config.html not found."
