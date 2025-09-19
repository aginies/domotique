# antoine@ginies.org
# GPL3

import time
import domo_utils as d_u

def serve_rfid_page(IP_ADDR, WS_PORT):
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RFID Log</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f4f4f9;
            color: #333;
        }}
        .container {{
            max-width: 800px;
            margin: auto;
            background-color: #fff;
            padding: 20px 40px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }}
        h1, h2 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        .log-display {{
            background-color: #ecf0f1;
            border: 1px solid #bdc3c7;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', Courier, monospace;
            white-space: pre-wrap;
            word-wrap: break-word;
            height: 300px;
            overflow-y: scroll;
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
    <div class="container">
        <h1>Adding RFID card</h1>
        <h2>Reset device after adding cards</h2>
        <div class="container">
            <h2>RFID log</h2>
            <pre id="log-display"></pre>
        </div>
        <a href="/RESET_device" target="_blank" class="button reset-button" onclick="return confirm('Are you sure you want to reset the device? This will cause
 a reboot.')">Reset Device</a>       
    </div>
    <script>
        const getLogs = async () => {{
            try {{
                const response = await fetch('/get_log_rfid');
                if (!response.ok) {{
                    throw new Error(`HTTP error! Status: ${{response.status}}`);
                }}
                const logData = await response.text();
                document.getElementById('log-display').textContent = logData || 'No logs found.';
            }} catch (error) {{
                console.error('Failed to fetch logs:', error);
                document.getElementById('log-display').textContent = 'Failed to load logs.';
            }}
        }};
        getLogs()
        setInterval(getLogs, 300);
    </script>
</body>
</html>
"""
    return html
