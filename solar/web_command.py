# antoine@ginies.org
# GPL3

import config_var as c_v

def create_html_response():
    try:
        with open('web_command.html', 'r') as f:
            tmpl = f.read()
        return tmpl.format(EQUIPMENT_NAME=c_v.EQUIPMENT_NAME)
    except OSError:
        return "Error: web_command.html not found."
