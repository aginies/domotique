# antoine@ginies.org
# GPL3

import config_var as c_v
import paths

def create_html_response():
    try:
        with open(paths.VERSION_FILE, 'r') as file:
            version = file.read().strip()
    except OSError:
        version = "unknown"

    try:
        with open('web_command.html', 'r') as f:
            tmpl = f.read()
        return tmpl.format(
            EQUIPMENT_NAME=c_v.EQUIPMENT_NAME,
            VERSION=version
        )
    except OSError:
        return "Error: web_command.html not found."
