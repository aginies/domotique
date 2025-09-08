# antoine@ginies.org
# GPL3

from collections import deque
import config_var as c_v
import utime

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

def format_log_line(line, pattern_c):
    """
    Takes one raw log line and returns it with a formatted date and time.
    If formatting fails, it returns the original line.
    """
    if pattern_c not in line:
        return line

    try:
        parts = line.split(pattern_c, 1)
        datetime_str = parts[0].strip()
        message = parts[1].strip()
        date_part, time_part = datetime_str.split(' ')
        clean_time = time_part.rstrip(':')
        year, month, day = [int(p) for p in date_part.split('-')]
        timestamp = utime.mktime((year, month, day, 0, 0, 0, 0, 0))
        weekday_index = utime.localtime(timestamp)[6] # 0=Monday
        jour_nom = jours[weekday_index]
        mois_nom = mois[month - 1]
        formatted_date = f"{jour_nom} {day} {mois_nom}" # {year}"
        hour, minute, second = [int(p) for p in clean_time.split(':')]
        # We only need the date to find the day of the week
        formatted_time = f"{hour:02d}:{minute:02d}:{second:02d}"        
        return f"{formatted_date} {formatted_time} {message}"

    except (ValueError, IndexError):
        return line

def get_formatted_log_summary(log_lines, pattern_c):
    """
    Takes a list of raw log lines and returns them as a single formatted string.
    """
    formatted_lines = (format_log_line(line, pattern_c) for line in log_lines)
    return "\n".join(formatted_lines)

def serve_log_file(nb_lines, pattern_c):
    try:
        with open("/log.txt", "r", encoding="utf-8") as f:
            log_lines = f.readlines()
            action_lines = [line for line in log_lines if pattern_c in line]
            last_x_lines = action_lines[-nb_lines:]
            formatted_content = get_formatted_log_summary(last_x_lines, pattern_c)
            log_content = "".join(formatted_content)
            if log_content:
                return log_content, 200, {"Content-Type": "text/plain"}
            else:
                return "No matching log lines found", 200, {"Content-Type": "text/plain"}  # Return a valid response
    except OSError as err:
        print(f"Error reading log file: {err}")
        return "Log file not found", 404, {"Content-Type": "text/plain"}
