# antoine@ginies.org
# GPL3

import os
import web_config as w_c
import domo_utils as d_u
import paths

def save_config(new_config):
    tmp_path = paths.CONFIG_FILE + '.tmp'
    with open(tmp_path, 'w') as f:
        for key, value in new_config.items():
            if key in ('AUTHORIZED_CARDS', 'CARD_KEY'):
                f.write(f'{key} = {value}\n')
            elif isinstance(value, str):
                escaped_value = value.replace('"', '\\"')
                f.write(f'{key} = "{escaped_value}"\n')
            elif isinstance(value, bool):
                f.write(f'{key} = {value}\n')
            elif isinstance(value, (int, float)):
                f.write(f'{key} = {value}\n')
            else:
                f.write(f'{key} = {repr(value)}\n')
    try:
        os.remove(paths.CONFIG_FILE)
    except OSError:
        pass
    os.rename(tmp_path, paths.CONFIG_FILE)

def save_configuration(request, IP_ADDR):
    """ Save the configuration file """
    decoded_request = request.decode('utf-8')
    body_start = decoded_request.find('\r\n\r\n')
    if body_start == -1:
        return "Error: Request body not found."

    form_data_str = decoded_request[body_start + 4:] # +4 to skip '\r\n\r\n'
    parsed_items = {}
    pairs = form_data_str.split('&')
    for pair in pairs:
        if '=' in pair:
            key, value = pair.split('=', 1) # Split only on the first '='
            parsed_items[d_u.url_decode(key)] = d_u.url_decode(value)
        else:
            parsed_items[d_u.url_decode(pair)] = ""

    # Get current config
    config = w_c.get_config()

    for key, value in parsed_items.items():
        # Specific handling for CPU_FREQ from the dropdown
        if key == 'CPU_FREQ':
            try:
                config[key] = int(value)
            except ValueError:
                d_u.print_and_store_log(f"Warning: Could not convert '{value}' to int for '{key}'. Keeping previous value.")
            continue

    for key, value in parsed_items.items():
        if key in config:
            current_config_value = config.get(key)

            if isinstance(current_config_value, bool):
                config[key] = value.lower() == 'true'
            elif isinstance(current_config_value, int):
                try:
                    config[key] = int(value)
                except ValueError:
                    d_u.print_and_store_log(f"Warning: Could not convert '{value}' to int for '{key}'. Keeping previous value or string.")
            elif isinstance(current_config_value, float):
                try:
                    config[key] = float(value)
                except ValueError:
                    d_u.print_and_store_log(f"Warning: Could not convert '{value}' to float for '{key}'. Keeping previous value or string.")
            else:
                config[key] = value

    save_config(config)
    redirect_url = (f"http://{IP_ADDR}/web_config?reboot_needed=1")
    response_headers = [
        "HTTP/1.1 303 See Other",
        f"Location: {redirect_url}",
        "Connection: close",
        "",
    ]
    response = "\r\n".join(response_headers)
    return response