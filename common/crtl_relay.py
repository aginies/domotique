# antoine@ginies.org
# GPL3

import utime
import os
import _thread
import gc
from machine import Pin
import domo_utils as d_u
import config_var as c_v

lock = _thread.allocate_lock()

# RELAY for BP1 and BP2
# Be sure to put max power to the pin to control the relay
last_ctrl_relay_time = 0
relay1 = Pin(c_v.RELAY1_PIN, Pin.OUT, drive=Pin.DRIVE_3)
relay2 = Pin(c_v.RELAY2_PIN, Pin.OUT, drive=Pin.DRIVE_3)

def ctrl_relay(which_one, duration):
    """ relay 1 or 2, now non-blocking """
    lock.acquire()

    if which_one == 1:
        relay = relay1
    else:
        relay = relay2

    with open('/IN_PROGRESS', 'w') as file:
        file.write('This file was created by clicking BP1 or BP2.')
    try:
        # internal_led_blink(pink, led_off, 3, c_v.time_ok) # Keep if non-blocking
        relay.on()
        d_u.print_and_store_log(f"Relay {which_one} ON for {duration} seconds.")
        start_time = utime.time()
        last_print_time = start_time
        if not check_stop_relay():
            while utime.time() - start_time < duration:
                if check_stop_relay():
                    d_u.print_and_store_log(f"Stop requested for Relay {which_one} (duration left: {duration - (utime.time() - start_time):.1f}s).")
                    relay.off()
                    break
                current_time = utime.time()
                if current_time - last_print_time >= 5:
                    elapsed_time = current_time - start_time
                    d_u.print_and_store_log(f"Relay {which_one} has been ON for {elapsed_time:.1f} seconds. ({duration - elapsed_time:.1f}s remaining).")
                    last_print_time = current_time
                utime.sleep_ms(100)

            if relay.value() == 1:
                d_u.print_and_store_log(f"Switching Relay {which_one} as Off")
                relay.off()

        else:
            # If stopped by emergency, ensure files are cleared
            try:
                os.remove("/BP1")
            except OSError:
                pass
            try:
                os.remove("/BP2")
            except OSError:
                pass
        try:
            os.remove("/IN_PROGRESS")
        except OSError:
            pass
        lock.release()
        gc.collect()

    except Exception as err:
        d_u.print_and_store_log(f"Error in ctrl_relay({which_one}): {err}")
        relay1.off()
        relay2.off()
        # internal_led_blink(pink, led_off, 5, c_v.time_err)
        ERR_CTRL_RELAY = True

def check_stop_relay():
    d_u.file_exists("/EMERGENCY_STOP")

def ctrl_relay_off():
    """ Force all relay Off! """
    d_u.print_and_store_log("Relays forced OFF, stop_relay_action set to True.")
    relay1.off()
    relay2.off()

def thread_do_job_crtl_relay(B_text, relay_nb, duration):
    """ Do the thread job for the realy """
    global last_ctrl_relay_time
    current_time = utime.time()
    response_content = ""
    d_u.print_and_store_log(f"{current_time} {last_ctrl_relay_time}")
    if current_time - last_ctrl_relay_time > duration:
        d_u.print_and_store_log(f"{B_text} activé")
        last_ctrl_relay_time = current_time
        if B_text == "BP1":
            try:
                with open("/BP1", 'w') as file:
                    file.write(f'This file was created by clicking BP1.')
                os.remove("/BP2")
            except OSError:
                pass # BP2 might not exist
        elif B_text == "BP2":
            try:
                with open("/BP2", 'w') as file:
                    file.write(f'This file was created by clicking BP2.')
                os.remove("/BP1")
            except OSError:
                pass # BP1 might not exist

        _thread.start_new_thread(ctrl_relay, (relay_nb, duration))
        response_content = B_text + " activated"
    else:
        d_u.print_and_store_log(f"{B_text} Duplicate request seen...")
        response_content = "Duplicate request " + B_text
    content_type = "text/plain"