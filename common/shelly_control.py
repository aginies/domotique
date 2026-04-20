# antoine@ginies.org
# GPL3

import urequests
import domo_utils as d_u

def set_power(ip, turn_on):
    """
    Sets the power state of a Shelly Gen2/Gen3 device via its RPC API.
    URL: http://<ip>/rpc/Switch.Set?id=0&on=<true/false>
    """
    if not ip:
        d_u.print_and_store_log("Shelly Error: No IP address provided.")
        return False
        
    state = "true" if turn_on else "false"
    url = f"http://{ip}/rpc/Switch.Set?id=0&on={state}"
    
    try:
        d_u.print_and_store_log(f"Shelly: Sending {state} to {ip}")
        response = urequests.get(url, timeout=3)
        if response.status_code == 200:
            d_u.print_and_store_log(f"Shelly ({ip}) turned {'ON' if turn_on else 'OFF'} successfully.")
            success = True
        else:
            d_u.print_and_store_log(f"Shelly error: Received HTTP {response.status_code}")
            success = False
        response.close()
        return success
    except Exception as err:
        d_u.print_and_store_log(f"Shelly connection failed: {err}")
        return False
