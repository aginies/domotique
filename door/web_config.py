# antoine@ginies.org
# GPL3

import config_var

with open('/VERSION', 'r') as file:
   version = file.read().strip()

# Load existing configuration
config = {
    "DOOR": config_var.DOOR,
    "nom_bp1": config_var.nom_bp1,
    "E_WIFI": config_var.E_WIFI,
    "WIFI_SSID": config_var.WIFI_SSID,
    "WIFI_PASSWORD": config_var.WIFI_PASSWORD,
    "AP_SSID": config_var.AP_SSID,
    "AP_PASSWORD": config_var.AP_PASSWORD,
    "AP_HIDDEN_SSID": config_var.AP_HIDDEN_SSID,
    "AP_CHANNEL": config_var.AP_CHANNEL,
    "AP_IP": config_var.AP_IP,
    "I_LED_PIN": config_var.I_LED_PIN,
    "LED_PIN": config_var.LED_PIN,
    "DOOR_SENSOR_PIN": config_var.DOOR_SENSOR_PIN,
    "RELAY1_PIN": config_var.RELAY1_PIN,
    "RELAY2_PIN": config_var.RELAY2_PIN,
    "time_ok": config_var.time_ok,
    "time_err": config_var.time_err,
    "OLED_SCL_PIN": config_var.OLED_SCL_PIN,
    "OLED_SDA_PIN": config_var.OLED_SDA_PIN,
    "CPU_FREQ": config_var.CPU_FREQ,
    "VERSION": version,
    "CARD_KEY": config_var.CARD_KEY,
    "AUTHORIZED_CARDS": config_var.AUTHORIZED_CARDS,
}

def serve_config_page(IP_ADDR, WS_PORT):
    selected_options = {
        'selected_20': 'selected' if config_var.CPU_FREQ == 20 else '',
        'selected_40': 'selected' if config_var.CPU_FREQ == 40 else '',
        'selected_80': 'selected' if config_var.CPU_FREQ == 80 else '',
        'selected_160': 'selected' if config_var.CPU_FREQ == 160 else '',
        'selected_240': 'selected' if config_var.CPU_FREQ == 240 else '',
    }
    net_config = {
        'IP_ADDR': IP_ADDR,
        'WS_PORT': WS_PORT,
    }
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Configuration {DOOR}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #e8f4f8;
            color: #333;
        }}
        h1, h2 {{
            color: #2c3e50;
        }}
        .form-container {{
            background-color: #ffffff;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            max-width: 600px;
            margin: 20px auto;
        }}
        .button-group {{
            display: flex;
            justify-content: space-between;
            gap: 10px;
            margin-top: 20px;
        }}
        .form-group {{
            margin-bottom: 20px;
        }}
        label {{
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #2c3e50;
        }}
        input[type="text"],
        input[type="password"],
        input[type="number"] {{
            width: 100%;
            padding: 12px;
            border: 1px solid #ccc;
            border-radius: 8px;
            box-sizing: border-box;
            font-size: 16px;
            background-color: #f9f9f9;
        }}
        input[type="submit"] {{
            background-color: #3498db;
            color: white;
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: background-color 0.3s;
        }}
        input[type="submit"]:hover {{
            background-color: #2980b9;
        }}
        .section {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
        }}
        select {{
            width: 100%;
            padding: 12px;
            border: 1px solid #ccc;
            border-radius: 8px;
            box-sizing: border-box;
            font-size: 16px;
            background-color: #f9f9f9;
        }}
        .cancel-button {{
            background-color: #95a5a6;
            color: white;
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            text-decoration: none; /* Removes underline from the link */
            display: inline-block;
            transition: background-color 0.3s;
        }}
        .cancel-button:hover {{
            background-color: #7f8c8d;      
        }}
        .reset-button {{
            background-color: #e74c3c;
            color: white;
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            text-decoration: none;
            display: inline-block;
            transition: background-color 0.3s;
        }}
        .reset-button:hover {{
            background-color: #c0392b;
        }}
    </style>
</head>
<body>
    <div class="form-container">
        <h1>Configuration pour {DOOR} ({VERSION})</h1>
        <form id="configForm" action="/save_config" method="POST">
            <div class="form-group">
                <label for="DOOR">Nom Général</label>
                <input type="text" id="DOOR" name="DOOR" value="{DOOR}">
            </div>
            <div class="section">
                <h2>Boutton</h2>
                <div class="form-group">
                    <label for="nom_bp1">Nom du Boutton 1:</label>
                    <input type="text" id="nom_bp1" name="nom_bp1" value="{nom_bp1}">
                </div>
            </div>
            <div class="section">
                <h2>Card management</h2>
                <div class="form-group">
                    <label for="CARD_KEY">Card Key:</label>
                    <input type="text" id="CARD_KEY" name="CARD_KEY" value="{CARD_KEY}">
                </div>
                <div class="form-group">
                    <label for="AUTHORIZED_CARDS">Authorized Cards:</label>
                    <input type="text" id="AUTHORIZED_CARDS" name="AUTHORIZED_CARDS" value="{AUTHORIZED_CARDS}">
                </div>
            </div>
            <div class="section">
                <h2>WIFI</h2>
                <div class="form-group">
                    <label for="E_WIFI">Utiliser un réseau existant (True ou False):</label>
                    <input type="text" id="E_WIFI" name="E_WIFI" value="{E_WIFI}">
                </div>
                <div class="form-group">
                    <label for="WIFI_SSID">WiFi SSID:</label>
                    <input type="text" id="WIFI_SSID" name="WIFI_SSID" value="{WIFI_SSID}">
                </div>
                <div class="form-group">
                    <label for="WIFI_PASSWORD">WiFi Password:</label>
                    <input type="password" id="WIFI_PASSWORD" name="WIFI_PASSWORD" value="{WIFI_PASSWORD}">
                </div>
                <div class="form-group">
                    <label for="AP_SSID">AP SSID:</label>
                    <input type="text" id="AP_SSID" name="AP_SSID" value="{AP_SSID}">
                </div>
                <div class="form-group">
                    <label for="AP_PASSWORD">AP Password:</label>
                    <input type="password" id="AP_PASSWORD" name="AP_PASSWORD" value="{AP_PASSWORD}">
                </div>
                <div class="form-group">
                    <label for="AP_CHANNEL">AP Channel:</label>
                    <input type="number" id="AP_CHANNEL" name="AP_CHANNEL" value="{AP_CHANNEL}">
                </div>
            </div>

            <div class="section">
                <h2>Advanced</h2>
                <div class="form-group">
                    <label for="CPU_FREQ">CPU frequency of the ESP32:</label>
                    <select id="CPU_FREQ" name="CPU_FREQ">
                        <option value="20" {selected_20}>20 MHz</option>
                        <option value="40" {selected_40}>40 MHz</option>
                        <option value="80" {selected_80}>80 MHz</option>
                        <option value="160" {selected_160}>160 MHz</option>
                        <option value="240" {selected_240}>240 MHz</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="I_LED_PIN">Internal LED Pin:</label>
                    <input type="number" id="I_LED_PIN" name="I_LED_PIN" value="{I_LED_PIN}">
                </div>
                <div class="form-group">
                    <label for="LED_PIN">External LED Pin:</label>
                    <input type="number" id="LED_PIN" name="LED_PIN" value="{LED_PIN}">
                </div>
                <div class="form-group">
                    <label for="DOOR_SENSOR_PIN">Door Sensor Pin:</label>
                    <input type="number" id="DOOR_SENSOR_PIN" name="DOOR_SENSOR_PIN" value="{DOOR_SENSOR_PIN}">
                </div>
                <div class="form-group">
                    <label for="RELAY1_PIN">Relay 1 Pin:</label>
                    <input type="number" id="RELAY1_PIN" name="RELAY1_PIN" value="{RELAY1_PIN}">
                </div>
                <div class="form-group">
                    <label for="RELAY2_PIN">Relay 2 Pin:</label>
                    <input type="number" id="RELAY2_PIN" name="RELAY2_PIN" value="{RELAY2_PIN}">
                </div>
                <div class="form-group">
                    <label for="time_ok">LED OK Time (seconds):</label>
                    <input type="number" step="0.1" id="time_ok" name="time_ok" value="{time_ok}">
                </div>
                <div class="form-group">
                    <label for="time_err">LED Error Time (seconds):</label>
                    <input type="number" step="0.1" id="time_err" name="time_err" value="{time_err}">
                </div>
                <div class="form-group">
                    <label for="OLED_SCL_PIN">OLED SCL Pin:</label>
                    <input type="number" step="1" id="OLED_SCL_PIN" name="OLED_SCL_PIN" value="{OLED_SCL_PIN}">
                </div>
                <div class="form-group">
                    <label for="OLED_SDA_PIN">OLED SDA Pin:</label>
                    <input type="number" step="1" id="OLED_SDA_PIN" name="OLED_SDA_PIN" value="{OLED_SDA_PIN}">
                </div>
            </div>
        <div class="button-group">
            <form id="configForm" action="/save_config" method="POST" enctype="multipart/form-data">
                <input type="submit" value="Save">
            </form>
            <a href="/" class="cancel-button">Cancel</a>
            <a href="/RESET_device" target="_blank" class="button reset-button" onclick="return confirm('Are you sure you want to reset the device? This will cause
 a reboot.')">Reset Device</a>
        </div>
        <form>
    </div>
    <script>
        const configForm = document.getElementById('configForm');
        const configServerUrl = 'http://{IP_ADDR}:{WS_PORT}';
        configForm.addEventListener('change', () => {{
            configForm.action = configServerUrl + '/save_config';
            console.log('Form action set to:', configForm.action);
        }};
    </script>
</body>
</html>""".format(**config, **net_config, **selected_options)
    return html
