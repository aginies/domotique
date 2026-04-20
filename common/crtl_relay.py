# antoine@ginies.org
# GPL3

import utime
import os
import _thread
import gc
from machine import Pin
import domo_utils as d_u
import config_var as c_v
import paths

lock = _thread.allocate_lock()

# RELAY for BP1 and BP2
# Be sure to put max power to the pin to control the relay
last_ctrl_relay_time = 0
relay1 = Pin(c_v.RELAY1_PIN, Pin.OUT, drive=Pin.DRIVE_3)
relay2 = Pin(c_v.RELAY2_PIN, Pin.OUT, drive=Pin.DRIVE_3)

def emergency_manage_files():
    """ manage files if emergency clicked """
    # If stopped by emergency, ensure files are cleared
    TO_REMOVE = [paths.RELAY_BP1_FLAG, paths.RELAY_BP2_FLAG, paths.AJUSTEMENT_FLAG, paths.IN_PROGRESS_FLAG]
    for doit in TO_REMOVE:
        if d_u.file_exists(doit):
            try:
                os.remove(doit)
            except OSError:
                pass
    # If Shelly is enabled, force it OFF immediately
    if getattr(c_v, 'CONTROL_SHELLY', False):
        import shelly_control
        shelly_control.set_power(c_v.SHELLY_IP, False)

def ctrl_relay(which_one, duration):
    """ relay 1 or 2, now non-blocking """
    lock.acquire()
    relay = relay1 if which_one == 1 else relay2

    try:
        with open(paths.IN_PROGRESS_FLAG, 'w') as file:
            file.write('This file was created by clicking BP1 or BP2.')
        
        # Power ON Shelly if enabled
        if getattr(c_v, 'CONTROL_SHELLY', False):
            import shelly_control
            d_u.print_and_store_log("Switching Shelly ON before relay")
            if not shelly_control.set_power(c_v.SHELLY_IP, True):
                d_u.print_and_store_log("ABORT: Shelly connection failed, skipping motor relay.")
                return
            utime.sleep(1)

        relay.on()
        d_u.print_and_store_log(f"Relay {which_one} ON for {duration} seconds.")
        start_time = utime.time()
        last_print_time = start_time
        
        while utime.time() - start_time < duration:
            if check_stop_relay():
                d_u.print_and_store_log(f"Stop requested for Relay {which_one} (duration left: {duration - (utime.time() - start_time):.1f}s).")
                relay.off()
                emergency_manage_files()
                return # Early return, finally will still run

            current_time = utime.time()
            if current_time - last_print_time >= 5:
                elapsed_time = current_time - start_time
                d_u.print_and_store_log(f"Relay {which_one} has been ON for {elapsed_time:.1f} seconds. ({duration - elapsed_time:.1f}s remaining).")
                last_print_time = current_time
            utime.sleep_ms(100)

        if relay.value() == 1:
            d_u.print_and_store_log(f"Switching Relay {which_one} as Off")
            relay.off()
            
            # Power OFF Shelly if enabled, after a short delay
            if getattr(c_v, 'CONTROL_SHELLY', False):
                import shelly_control
                wait_sec = getattr(c_v, 'DELAY_SHELLY', 3)
                d_u.print_and_store_log(f"Waiting {wait_sec}s before switching Shelly OFF")
                utime.sleep(wait_sec)
                shelly_control.set_power(c_v.SHELLY_IP, False)

    except Exception as err:
        d_u.print_and_store_log(f"Error in ctrl_relay({which_one}): {err}")
        relay1.off()
        relay2.off()
    finally:
        if d_u.file_exists(paths.IN_PROGRESS_FLAG):
            try:
                os.remove(paths.IN_PROGRESS_FLAG)
            except OSError:
                pass
        if d_u.file_exists(paths.AJUSTEMENT_FLAG):
            try:
                os.remove(paths.AJUSTEMENT_FLAG)
            except OSError:
                pass
        lock.release()
        gc.collect()

def check_stop_relay():
    test = d_u.file_exists(paths.EMERGENCY_STOP_FLAG)
    return test

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
                with open(paths.RELAY_BP1_FLAG, 'w') as file:
                    file.write('This file was created by clicking BP1.')
                for f in [paths.RELAY_BP2_FLAG, paths.AJUSTEMENT_FLAG]:
                    if d_u.file_exists(f): os.remove(f)
            except OSError:
                pass # BP2 might not exist
        elif B_text == "BP2":
            try:
                with open(paths.RELAY_BP2_FLAG, 'w') as file:
                    file.write('This file was created by clicking BP2.')
                for f in [paths.RELAY_BP1_FLAG, paths.AJUSTEMENT_FLAG]:
                    if d_u.file_exists(f): os.remove(f)
            except OSError:
                pass # BP1 might not exist
        elif B_text in ("OPEN_B", "CLOSE_B"):
            try:
                with open(paths.AJUSTEMENT_FLAG, 'w') as file:
                    file.write('Ajustement in progress')
            except OSError:
                pass

        _thread.start_new_thread(ctrl_relay, (relay_nb, duration))
        response_content = B_text + " activated"
    else:
        d_u.print_and_store_log(f"{B_text} Duplicate request seen...")
        response_content = "Duplicate request " + B_text
    content_type = "text/plain"