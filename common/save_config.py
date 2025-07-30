# antoine@ginies.org
# GPL3

import web_config as w_c

def save_config(new_config):
    with open('config_var.py', 'w') as f:
        for key, value in new_config.items():
            if isinstance(value, str):
                f.write(f'{key} = "{value.replace('"', '\\"')}"\n')
            elif isinstance(value, bool):
                f.write(f'{key} = {value}\n')
            elif isinstance(value, (int, float)):
                f.write(f'{key} = {value}\n')
            else:
                f.write(f'{key} = {repr(value)}\n')
            f.flush()

def url_decode(s):
    """ Try to do url decode as micropython doesnt have urlib parse..."""
    result = []
    i = 0
    while i < len(s):
        if s[i] == '%':
            if i + 2 < len(s):
                hex_val = s[i+1:i+3]
                try:
                    result.append(chr(int(hex_val, 16)))
                    i += 3
                except ValueError:
                    result.append(s[i])
                    i += 1
            else:
                result.append(s[i])
                i += 1
        elif s[i] == '+':
            result.append(' ')
            i += 1
        else:
            result.append(s[i])
            i += 1
    return ''.join(result)

def save_configuration(request):
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
            parsed_items[url_decode(key)] = url_decode(value)
        else:
            parsed_items[url_decode(pair)] = ""

    for key, value in parsed_items.items():
        if key in w_c.config:
            current_config_value = w_c.config.get(key)
            
            if isinstance(current_config_value, int):
                try:
                    w_c.config[key] = int(value)
                except ValueError:
                    print(f"Warning: Could not convert '{value}' to int for '{key}'. Keeping previous value or string.")
            elif isinstance(current_config_value, float):
                try:
                    w_c.config[key] = float(value)
                except ValueError:
                    print(f"Warning: Could not convert '{value}' to float for '{key}'. Keeping previous value or string.")
            elif isinstance(current_config_value, bool):
                # Convert 'True'/'False' strings to boolean (case-insensitive)
                w_c.config[key] = value.lower() == 'true'
            else:
                w_c.config[key] = value

    save_config(w_c.config)
    redirect_url = "/"
    response_headers = [
        "HTTP/1.1 303 See Other",
        f"Location: {redirect_url}",
        "Connection: close",
        "",
    ]
    return "\r\n".join(response_headers)
