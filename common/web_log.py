# antoine@ginies.org
# GPL3

import config_var as c_v
import utime
import paths

def create_log_page():
    """ Creates the HTML page for viewing the log with auto-refresh. """
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Log {c_v.DOOR}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            color: #333;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            margin: auto;
            background-color: #fff;
            padding: 20px 40px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }}
        .log-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            white-space: pre-wrap; /* Preserve whitespace and line breaks */
            max-height: 80vh;
            overflow-y: auto; /* Enable scrolling */
            border: 1px solid #ddd;
        }}
        h1 {{
            text-align: center;
        }}
    </style>
</head>
<body>
    <h1>Log du Système</h1>
    <div id="logContent" class="log-container">
        Chargement du log...
    </div>
    <script>
        const logContentDiv = document.getElementById('logContent');

        function fetchLog() {{
            fetch('/log.txt')
                .then(response => {{
                    if (!response.ok) {{
                        throw new Error('Log file not found or server error');
                    }}
                    return response.text();
                }})
                .then(data => {{
                    logContentDiv.textContent = data;
                    // Auto-scroll to the bottom on update
                    logContentDiv.scrollTop = logContentDiv.scrollHeight;
                }})
                .catch(error => {{
                    logContentDiv.textContent = 'Erreur: ' + error.message;
                    console.error('Error fetching log:', error);
                }});
        }}
        fetchLog();
        setInterval(fetchLog, 2000);
    </script>
</body>
</html>"""
    return html

jours = ("Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche")
# Month tuple (index 0 = January)
mois = ("jan", "fév", "mars", "avr", "mai", "juin", "jui", "août", "sept", "oct", "nov", "déc")

def format_log_line(line):
    """
    Takes one raw log line and returns it with a formatted date and time.
    Format: YYYY-MM-DD HH:MM:SS: MESSAGE
    """
    try:
        # Split at the 3rd colon to separate timestamp from message
        # Format is "YYYY-MM-DD HH:MM:SS: MESSAGE"
        parts = line.split(': ', 1)
        if len(parts) < 2:
            return line
            
        timestamp_part = parts[0].strip()
        message = parts[1].strip()
        
        date_part, time_part = timestamp_part.split(' ')
        year, month, day = [int(p) for p in date_part.split('-')]
        
        # Get weekday
        timestamp = utime.mktime((year, month, day, 0, 0, 0, 0, 0))
        weekday_index = utime.localtime(timestamp)[6] # 0=Monday
        jour_nom = jours[weekday_index]
        mois_nom = mois[month - 1]
        
        formatted_date = f"{jour_nom} {day} {mois_nom}"
        return f"{formatted_date} {time_part} {message}"

    except (ValueError, IndexError, Exception):
        return line

def serve_log_file(nb_lines, patterns):
    """ 
    patterns can be a string or a list of strings.
    """
    if isinstance(patterns, str):
        patterns = [patterns]
        
    try:
        with open(paths.LOG_FILE, "r") as f:
            log_lines = f.readlines()
            
            # Filter lines that match ANY of the patterns
            matched_lines = []
            for line in log_lines:
                if any(p in line for p in patterns):
                    matched_lines.append(line)
            
            last_x_lines = matched_lines[-nb_lines:]
            formatted_lines = [format_log_line(line) for line in last_x_lines]
            log_content = "\n".join(formatted_lines)
            
            if log_content:
                return log_content, 200, {"Content-Type": "text/plain"}
            else:
                return "No matching log lines found", 200, {"Content-Type": "text/plain"}
    except OSError as err:
        print(f"Error reading log file: {err}")
        return "Log file not found", 404, {"Content-Type": "text/plain"}
