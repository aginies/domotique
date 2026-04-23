# antoine@ginies.org
# GPL3

import os
import web_config as w_c
import domo_utils as d_u
import paths

def save_config(new_config):
    """
    Saves new configuration values while preserving comments and structure.
    Reads current config line-by-line and updates matching keys.
    """
    tmp_path = paths.CONFIG_FILE + '.tmp'
    updated_keys = set()
    
    try:
        with open(paths.CONFIG_FILE, 'r') as f_old, open(tmp_path, 'w') as f_new:
            for line in f_old:
                original_line = line
                stripped = line.strip()
                
                # Check if this is an assignment line (skip comments and empty lines)
                if stripped and not stripped.startswith('#') and '=' in stripped:
                    key = stripped.split('=')[0].strip()
                    if key in new_config:
                        value = new_config[key]
                        updated_keys.add(key)
                        
                        # Format the new line according to type
                        if key in ('AUTHORIZED_CARDS', 'CARD_KEY'):
                            f_new.write(f'{key} = {value}\n')
                        elif isinstance(value, str):
                            escaped_value = value.replace('"', '\\"')
                            f_new.write(f'{key} = "{escaped_value}"\n')
                        elif isinstance(value, bool):
                            f_new.write(f'{key} = {value}\n')
                        elif isinstance(value, (int, float)):
                            f_new.write(f'{key} = {value}\n')
                        else:
                            f_new.write(f'{key} = {repr(value)}\n')
                        continue
                
                # Keep the original line if not updated
                f_new.write(original_line)

            # Append any keys that weren't in the original file
            for key, value in new_config.items():
                if key not in updated_keys:
                    if isinstance(value, str):
                        escaped_value = value.replace('"', '\\"')
                        f_new.write(f'{key} = "{escaped_value}"\n')
                    else:
                        f_new.write(f'{key} = {repr(value)}\n')

        # Atomic replacement
        try:
            os.remove(paths.CONFIG_FILE)
        except OSError:
            pass
        os.rename(tmp_path, paths.CONFIG_FILE)
        
    except Exception as e:
        d_u.print_and_store_log(f"Config Save Error: {e}")

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