# antoine@ginies.org
# GPL3

import config_var as c_v

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

        // Fetch log immediately on page load
        fetchLog();

        // Set up polling to refresh every 1.5 seconds
        setInterval(fetchLog, 1500);
    </script>
</body>
</html>"""
    return html