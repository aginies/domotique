# WiFi scanner and setup page
import network
import ujson
import domo_utils as d_u
import save_config
import config_var as c_v

def get_wifi_setup_page():
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    networks = sta_if.scan()
    
    # Sort and remove duplicates (keep strongest signal)
    unique_nets = {}
    for n in networks:
        ssid = n[0].decode('utf-8')
        rssi = n[3]
        if ssid not in unique_nets or rssi > unique_nets[ssid]:
            unique_nets[ssid] = rssi
            
    sorted_nets = sorted(unique_nets.items(), key=lambda x: x[1], reverse=True)

    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Configuration WiFi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #1a1a2e; color: #eee; padding: 20px; }
        .box { background: #16213e; padding: 20px; border-radius: 8px; max-width: 400px; margin: auto; }
        h1 { color: #f0c040; font-size: 1.5em; text-align: center; }
        .net { padding: 10px; border-bottom: 1px solid #333; cursor: pointer; }
        .net:hover { background: #0f3460; }
        input { width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box; background: #0d0d1a; color: #eee; border: 1px solid #444; border-radius: 4px; }
        button { width: 100%; padding: 12px; background: #f0c040; border: none; font-weight: bold; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="box">
        <h1>Connecter au WiFi</h1>
        <div id="list">
"""
    for ssid, rssi in sorted_nets:
        if ssid:
            html += f'<div class="net" onclick="pick(\'{ssid}\')">{ssid} ({rssi} dBm)</div>'
            
    html += """
        </div>
        <form action="/wifi_setup" method="POST">
            <input type="text" id="ssid" name="WIFI_SSID" placeholder="SSID" required>
            <input type="password" name="WIFI_PASSWORD" placeholder="Mot de passe">
            <input type="hidden" name="E_WIFI" value="True">
            <button type="submit">Enregistrer et Redémarrer</button>
        </form>
    </div>
    <script>
        function pick(s) { document.getElementById('ssid').value = s; }
    </script>
</body>
</html>"""
    return html

def save_wifi_config(form_data):
    d_u.print_and_store_log("WIFI SETUP: Saving new credentials...")
    # Update local config_var for immediate access (though we reboot anyway)
    c_v.WIFI_SSID = form_data.get('WIFI_SSID', '')
    c_v.WIFI_PASSWORD = form_data.get('WIFI_PASSWORD', '')
    c_v.E_WIFI = True
    
    # Save to file
    new_vars = {
        'WIFI_SSID': c_v.WIFI_SSID,
        'WIFI_PASSWORD': c_v.WIFI_PASSWORD,
        'E_WIFI': True
    }
    save_config.save_config_to_file(new_vars)
