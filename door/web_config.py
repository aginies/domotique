# antoine@ginies.org
# GPL3

import config_var

# Load existing configuration
config = {
    "DOOR": config_var.DOOR,
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
    "OLED_SDA_PIN": config_var.OLED_SDA_PIN
}

def serve_config_page():
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
        .container {{
            background-color: #ffffff;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            max-width: 600px;
            margin: 20px auto;
        }}
        .group {{
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
    </style>
</head>
<body>
    <div class="container">
        <h1>Configuration pour la {DOOR}</h1>
        <form id="configF" action="/save_config" method="post">
            <div class="group">
                <label for="DOOR">Nom Général</label>
                <input type="text" id="DOOR" name="DOOR" value="{DOOR}">
            </div>
            <div class="section">
                <h2>WIFI</h2>
                <div class="group">
                    <label for="E_WIFI">Utiliser un réseau existant (True ou False):</label>
                    <input type="text" id="E_WIFI" name="E_WIFI" value="{E_WIFI}">
                </div>
                <div class="group">
                    <label for="WIFI_SSID">WiFi SSID:</label>
                    <input type="text" id="WIFI_SSID" name="WIFI_SSID" value="{WIFI_SSID}">
                </div>
                <div class="group">
                    <label for="WIFI_PASSWORD">WiFi Password:</label>
                    <input type="password" id="WIFI_PASSWORD" name="WIFI_PASSWORD" value="{WIFI_PASSWORD}">
                </div>
                <div class="group">
                    <label for="AP_SSID">AP SSID:</label>
                    <input type="text" id="AP_SSID" name="AP_SSID" value="{AP_SSID}">
                </div>
                <div class="group">
                    <label for="AP_PASSWORD">AP Password:</label>
                    <input type="password" id="AP_PASSWORD" name="AP_PASSWORD" value="{AP_PASSWORD}">
                </div>
                <div class="group">
                    <label for="AP_CHANNEL">AP Channel:</label>
                    <input type="number" id="AP_CHANNEL" name="AP_CHANNEL" value="{AP_CHANNEL}">
                </div>
            </div>

            <div class="section">
                <h2>Advanced</h2>
                <div class="group">
                    <label for="I_LED_PIN">Internal LED Pin:</label>
                    <input type="number" id="I_LED_PIN" name="I_LED_PIN" value="{I_LED_PIN}">
                </div>
                <div class="group">
                    <label for="LED_PIN">External LED Pin:</label>
                    <input type="number" id="LED_PIN" name="LED_PIN" value="{LED_PIN}">
                </div>
                <div class="group">
                    <label for="DOOR_SENSOR_PIN">Door Sensor Pin:</label>
                    <input type="number" id="DOOR_SENSOR_PIN" name="DOOR_SENSOR_PIN" value="{DOOR_SENSOR_PIN}">
                </div>
                <div class="group">
                    <label for="RELAY1_PIN">Relay 1 Pin:</label>
                    <input type="number" id="RELAY1_PIN" name="RELAY1_PIN" value="{RELAY1_PIN}">
                </div>
                <div class="group">
                    <label for="RELAY2_PIN">Relay 2 Pin:</label>
                    <input type="number" id="RELAY2_PIN" name="RELAY2_PIN" value="{RELAY2_PIN}">
                </div>
                <div class="group">
                    <label for="time_ok">LED OK Time (seconds):</label>
                    <input type="number" step="0.1" id="time_ok" name="time_ok" value="{time_ok}">
                </div>
                <div class="group">
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
        <input type="submit" value="Save Configuration">
    </form> 
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const configF = document.getElementById('configF');
            if (configF) {{
                console.log("in configF");
                configF.addEventListener('submit', function(event) {{
                    // Prevent the default form submission immediately
                    event.preventDefault();
                    console.log("post preventDefault");
                    const confirmation = confirm("Êtes-vous sûr de vouloir sauvegarder la configuration ? Redémarrage obligatoire du dispositif.");
                    // setTimeout(() => {{ console.log(" 2 seconds."); }}, 2000);                    
                    if (confirmation) {{
                        console.log("Configuration save confirmed. Submitting form...");
                        this.submit();
                    }} else {{
                        console.log("Configuration save cancelled.");
                    }}
                }});
            }}
        }});
    </script>
</body>
</html>""".format(**config)
    return html
