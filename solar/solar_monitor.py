# antoine@ginies.org
# GPL3

import asyncio
import ujson
import utime
import esp32
from machine import Pin

import config_var as c_v
import domo_utils as d_u
import mqtt_client as m_c

# ── Public state (read by /status endpoint and web page) ────────────────────
current_grid_power = 0.0   # watts from Shelly (negative = solar export)
equipment_power = 0.0      # watts currently sent to equipment
equipment_active = False
force_mode_active = False
safe_state = False         # True when Shelly unreachable > SHELLY_TIMEOUT
emergency_mode = False     # True if hardware safety cutoff (overheat) is active
last_shelly_error = None
current_water_temp = None  # °C from DS18B20, None if not available
current_ssr_temp = None    # °C from DS18B20 on heatsink, None if not available
current_esp_temp = 0.0     # °C from internal sensor
fan_active = False         # SSR Cooling fan status
fan_percent = 0            # SSR Cooling fan speed percentage (0-100)
grid_source = "MQTT"       # "MQTT" or "HTTP"
night_mode = False         # True between 22:00 and 05:50
boost_end_time = 0         # utime.time() when boost expires
power_history = []         # Rolling buffer of last 5 minutes (60 points)

# ── Private state ────────────────────────────────────────────────────────────
_ssr_pin = None
_relay = None
_fan_pin = None
_current_duty = 0.0        # target duty [0.0–1.0], written by monitor_loop
_last_off_time = 0         # utime.time() when equipment was last turned off
_last_good_poll = 0        # utime.time() of last successful Shelly read
_safe_state_logged = False # avoid log spam
_last_mqtt_report = 0      # utime.time() of last MQTT report
_last_data_log_time = 0    # utime.time() of last solar_data.txt write
_last_pi_time = 0          # utime.ticks_ms() of last PI update
_last_temp_read = 0        # utime.time() of last DS18B20 read
_in_surplus = False        # unused, kept for compatibility

# Statistics & Flash Protection state
_solar_data_buffer = []    # RAM buffer for solar_data.txt
_total_import_Wh = 0.0     # Today's grid import (Wh)
_total_redirect_Wh = 0.0   # Today's equipment redirected energy (Wh)
_hourly_import_Wh = [0.0] * 24
_hourly_redirect_Wh = [0.0] * 24
_total_export_Wh = 0.0     # Today's grid export (Wh)
_hourly_export_Wh = [0.0] * 24
_active_heating_secs = 0   # Today's active heating time (seconds)
_last_stats_save = 0       # utime.time() of last stats.json write
_midnight_reset_done = False # Latch for daily reset
STATS_FILE = "stats.json"


# ── PI controller ────────────────────────────────────────────────────────────

class PIController:
    def __init__(self, kp, ki):
        self.kp = kp
        self.ki = ki
        self._integral = 0.0
        self._output = 0.0

    def update(self, error, dt):
        # Anti-windup: only block integration when it would push further into saturation
        at_upper = self._output >= 1.0
        at_lower = self._output <= 0.0
        if not (at_upper and error > 0) and not (at_lower and error < 0):
            self._integral += error * dt
            # Cap integral so wind-up from a large surplus can't delay shutdown by more than ~5 s
            self._integral = max(-10.0, min(10.0, self._integral))
        self._output = self.kp * error + self.ki * self._integral
        self._output = max(0.0, min(1.0, self._output))
        return self._output

    def reset(self):
        self._integral = 0.0
        self._output = 0.0


_pi = PIController(c_v.PID_KP, c_v.PID_KI)


# ── Hardware init ─────────────────────────────────────────────────────────────

def init_ssr_relay():
    global _ssr_pin, _relay, _fan_pin
    _ssr_pin = Pin(c_v.SSR_PIN, Pin.OUT)
    _ssr_pin.value(0)
    _relay = Pin(c_v.RELAY_PIN, Pin.OUT)
    _relay.value(1)
    
    # Fan init with PWM for 4-pin fan
    if getattr(c_v, 'E_FAN', False):
        from machine import PWM
        try:
            # Use 1kHz instead of 25kHz for better compatibility with 3.3V logic
            _fan_pin = PWM(Pin(c_v.FAN_PIN), freq=1000, duty_u16=0)
            d_u.print_and_store_log(f"Fan PWM on pin={c_v.FAN_PIN} initialized (1kHz, 0%)")
        except Exception as e:
            d_u.print_and_store_log(f"Fan PWM Init Error: {e}")

    d_u.print_and_store_log(
        f"SSR pin={c_v.SSR_PIN} (digital), Relay pin={c_v.RELAY_PIN} initialized (relay ON)"
    )


# ── Statistics Management ───────────────────────────────────────────────────

def _load_stats():
    """ Load current day totals from stats.json to resume after reboot. """
    global _total_import_Wh, _total_redirect_Wh, _hourly_import_Wh, _hourly_redirect_Wh
    global _total_export_Wh, _hourly_export_Wh, _active_heating_secs
    if not d_u.file_exists(STATS_FILE):
        return
    try:
        with open(STATS_FILE, "r") as f:
            stats = ujson.load(f)
        today = d_u.show_rtc_date()
        if today in stats:
            day_data = stats[today]
            _total_import_Wh = day_data.get("import", 0.0)
            _total_redirect_Wh = day_data.get("redirect", 0.0)
            _total_export_Wh = day_data.get("export", 0.0)
            _active_heating_secs = day_data.get("active_time", 0)
            
            # Load hourly data if present
            h_imp = day_data.get("h_import")
            if h_imp and len(h_imp) == 24:
                _hourly_import_Wh = h_imp
            h_red = day_data.get("h_redirect")
            if h_red and len(h_red) == 24:
                _hourly_redirect_Wh = h_red
            h_exp = day_data.get("h_export")
            if h_exp and len(h_exp) == 24:
                _hourly_export_Wh = h_exp
                
            d_u.print_and_store_log(f"STATS: Resumed today ({today}) totals from file")
    except Exception as e:
        d_u.print_and_store_log(f"STATS: Load error: {e}")

def _save_stats_to_file():
    """ Update stats.json with current totals. Keeps a rolling 365-day window. """
    global _total_import_Wh, _total_redirect_Wh, _hourly_import_Wh, _hourly_redirect_Wh
    global _total_export_Wh, _hourly_export_Wh, _active_heating_secs
    today = d_u.show_rtc_date()
    # Check if year is valid (NTP synced), avoid logging to 2000-01-01
    if today.startswith("2000"):
        return

    stats = {}
    if d_u.file_exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                stats = ujson.load(f)
        except:
            pass

    # Update or add today's entry
    stats[today] = {
        "import": round(_total_import_Wh, 1),
        "redirect": round(_total_redirect_Wh, 1),
        "export": round(_total_export_Wh, 1),
        "active_time": int(_active_heating_secs),
        "h_import": [round(x, 1) for x in _hourly_import_Wh],
        "h_redirect": [round(x, 1) for x in _hourly_redirect_Wh],
        "h_export": [round(x, 1) for x in _hourly_export_Wh]
    }

    # Prune hourly data older than 8 days to save flash and RAM
    # This keeps the "1 week with more details" while preserving system resources
    sorted_keys = sorted(stats.keys())
    if len(sorted_keys) > 8:
        for k in sorted_keys[:-8]:
            if "h_import" in stats[k]: del stats[k]["h_import"]
            if "h_redirect" in stats[k]: del stats[k]["h_redirect"]
            if "h_export" in stats[k]: del stats[k]["h_export"]

    # Rolling window: 365 days
    if len(stats) > 365:
        sorted_keys = sorted(stats.keys()) # Refresh keys after potential deletion
        while len(stats) > 365:
            oldest = sorted_keys.pop(0)
            del stats[oldest]
            d_u.print_and_store_log(f"STATS: Removed oldest record: {oldest}")

    try:
        with open(STATS_FILE, "w") as f:
            ujson.dump(stats, f)
    except Exception as e:
        d_u.print_and_store_log(f"STATS: Save error: {e}")

def _store_data_log(msg):
    """ Stores a message in the RAM buffer for solar_data.txt. """
    global _solar_data_buffer
    curr_date = d_u.show_rtc_date()
    h, m, s = d_u.show_rtc_time()
    curr_time = "{:02d}:{:02d}:{:02d}".format(h, m, s)
    _solar_data_buffer.append(f"{curr_date} {curr_time}: {msg}")
    # Always print to console
    print(utime.time(), ": ", msg)

def _flush_solar_data():
    """ Writes buffered solar data to flash and handles rotation. """
    global _solar_data_buffer
    if not _solar_data_buffer:
        return
    
    filename = "solar_data.txt"
    try:
        # Clean up old data file if it gets massive (100KB)
        if d_u.file_exists(filename):
             d_u._rotate_log_if_needed(filename, 100 * 1024)
        
        with open(filename, "a") as f:
            f.write("\n".join(_solar_data_buffer) + "\n")
        _solar_data_buffer = []
    except Exception as e:
        print(f"Failed to flush solar data: {e}")


# ── DS18B20 temperature sensor ────────────────────────────────────────────────

_ds = None
_ds_roms = []
_jsy = None

def _init_ds18b20():
    global _ds, _ds_roms
    if not c_v.E_DS18B20 and not getattr(c_v, 'E_SSR_TEMP', False):
        return
    try:
        import onewire, ds18x20
        _ds = ds18x20.DS18X20(onewire.OneWire(Pin(c_v.DS18B20_PIN)))
        _ds_roms = _ds.scan()
        if _ds_roms:
            d_u.print_and_store_log(f"DS18B20 found: {len(_ds_roms)} sensor(s) on pin {c_v.DS18B20_PIN}")
        else:
            d_u.print_and_store_log("DS18B20: no sensor found on bus")
    except Exception as err:
        d_u.print_and_store_log(f"DS18B20 init error: {err}")

async def _read_temps():
    global current_water_temp, current_ssr_temp
    if not _ds or not _ds_roms:
        return
    try:
        _ds.convert_temp()
        await asyncio.sleep_ms(800)
        
        # Sensor 1: Equipment/Water
        if c_v.E_DS18B20 and len(_ds_roms) > 0:
            current_water_temp = round(_ds.read_temp(_ds_roms[0]), 1)
        
        # Sensor 2: SSR Heatsink
        if getattr(c_v, 'E_SSR_TEMP', False):
            if len(_ds_roms) > 1:
                current_ssr_temp = round(_ds.read_temp(_ds_roms[1]), 1)
            elif len(_ds_roms) == 1 and not c_v.E_DS18B20:
                # If only SSR monitoring is enabled, use the first sensor
                current_ssr_temp = round(_ds.read_temp(_ds_roms[0]), 1)
                
    except Exception as err:
        d_u.print_and_store_log(f"DS18B20 read error: {err}")


# ── Shelly EM polling (Async / Non-blocking) ──────────────────────────────────

async def _get_shelly_power_async():
    """ Non-blocking HTTP GET for Shelly EM status with timeouts """
    # FAKE_SHELLY is intercepted in monitor_loop before HTTP is ever called.
    # This function only runs for real HTTP Shelly devices.
    target_ip   = c_v.SHELLY_EM_IP
    target_port = 80
    
    try:
        # Wrap connection in a 5s timeout
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(target_ip, target_port), 5
        )
        
        query = (
            "GET /status HTTP/1.0\r\n"
            "Host: {}\r\n"
            "Connection: close\r\n\r\n"
        ).format(target_ip)
        writer.write(query.encode())
        await writer.drain()

        response = b""
        # Read the response with a cumulative body timeout
        while True:
            line = await asyncio.wait_for(reader.readline(), 2)
            if not line:
                break
            response += line
        
        # Ensure we have a complete HTTP response
        if b"\r\n\r\n" not in response:
            raise ValueError("Incomplete HTTP response")
            
        _, body = response.split(b"\r\n\r\n", 1)
        data = ujson.loads(body)
        return float(data['emeters'][0]['power'])
        
    except Exception as e:
        # Re-raise as OSError to be caught by monitor_loop error handling
        raise OSError("Shelly poll failed: " + str(e))
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass


# ── Force-mode time window ────────────────────────────────────────────────────

def _time_to_minutes(hhmm):
    h, m = hhmm.split(':')
    return int(h) * 60 + int(m)

def _in_force_window():
    now = utime.localtime()
    current = now[3] * 60 + now[4]
    start_str = getattr(c_v, 'FORCE_START', "02:00")
    end_str = getattr(c_v, 'FORCE_END', "06:00")
    # Identical start/end means "disabled"
    if start_str == end_str:
        return False
    start = _time_to_minutes(start_str)
    end   = _time_to_minutes(end_str)
    if start < end:
        return start <= current < end
    return current >= start or current < end   # overnight range


# ── Hardware apply helpers ────────────────────────────────────────────────────

def _hardware_off():
    """Turn off SSR but keep relay on for normal operation."""
    _ssr_pin.value(0)


def _emergency_shutdown():
    """Immediately cut both SSR and relay for safety."""
    d_u.print_and_store_log("SOLAR SAFETY: Emergency shutdown — cutting relay and SSR")
    _ssr_pin.value(0)
    _relay.value(0)


def _publish_status_mqtt():
    """ Helper to publish current state to MQTT if enabled """
    global _last_mqtt_report
    if getattr(c_v, 'E_MQTT', False):
        now = utime.time()
        interval = getattr(c_v, 'MQTT_REPORT_INTERVAL', 30)
        
        if (now - _last_mqtt_report) < interval:
            return

        try:
            esp_temp = esp32.mcu_temperature()
            m_c.publish_status(
                current_grid_power,
                equipment_power,
                equipment_active,
                force_mode_active,
                _current_duty * 100.0,
                current_water_temp,
                esp_temp,
                fan_active=fan_active,
                ssr_temp=current_ssr_temp,
                fan_percent=fan_percent
            )
            _last_mqtt_report = now
        except Exception as err:
            d_u.print_and_store_log(f"MQTT publish error: {err}")


def test_fan_speed(percent):
    """ Manually set fan speed for testing (resets on next monitor loop) """
    global fan_percent, fan_active
    if not getattr(c_v, 'E_FAN', False) or not _fan_pin:
        return False
    
    try:
        p = max(0, min(100, int(percent)))
        duty = int(p * 65535 / 100)
        _fan_pin.duty_u16(duty)
        fan_percent = p
        fan_active = (p > 0)
        d_u.print_and_store_log(f"SOLAR TEST: Fan set to {p}%")
        return True
    except:
        return False


def start_boost(minutes=None):
    """ Force 100% heating for a set duration """
    global boost_end_time
    if minutes is None:
        minutes = c_v.BOOST_MINUTES
    boost_end_time = utime.time() + (minutes * 60)
    d_u.print_and_store_log("SOLAR BOOST: Manual override started for {} min".format(minutes))


def cancel_boost():
    """ Cancel an active boost """
    global boost_end_time
    boost_end_time = 0
    d_u.print_and_store_log("SOLAR BOOST: Cancelled")


# ── Burst-fire control loop (coroutine) ───────────────────────────────────────

async def burst_control_loop():
    """
    Applies _current_duty using burst-fire: SSR ON for duty*BURST_PERIOD seconds,
    then OFF for the remainder. Runs independently from monitor_loop so the
    Shelly poll interval and the burst period can differ.
    """
    global equipment_active, equipment_power, _last_off_time
    d_u.print_and_store_log("Burst control loop started")
    while True:
        duty   = _current_duty
        period = float(c_v.BURST_PERIOD)
        
        # Steady target power for UI (not flickering)
        equipment_power = round(duty * c_v.EQUIPMENT_MAX_POWER, 1)

        if duty <= 0.0:
            _hardware_off()
            if equipment_active:
                _last_off_time = utime.time()
            equipment_active = False
            await asyncio.sleep(period)

        elif duty >= 1.0:
            _ssr_pin.value(1)
            equipment_active = True
            await asyncio.sleep(period)

        else:
            on_time  = duty * period
            off_time = period - on_time
            _ssr_pin.value(1)
            equipment_active = True
            await asyncio.sleep(on_time)
            _ssr_pin.value(0)
            equipment_active = False
            _last_off_time = utime.time()
            if off_time > 0.05:
                await asyncio.sleep(off_time)


# ── History loop (coroutine) ──────────────────────────────────────────────────

async def history_loop():
    """
    Records grid and equipment power every 5 seconds to power_history.
    Caps at 60 items (5 minutes).
    """
    global power_history
    d_u.print_and_store_log("Power history loop started")
    while True:
        # Use utime.time() for the timestamp.
        # Format for JS: {"t": timestamp, "g": grid, "e": equipment, "s": ssr_temp}
        point = {
            "t": utime.time(),
            "g": current_grid_power,
            "e": equipment_power,
            "s": current_ssr_temp,
            "f": fan_active
        }
        power_history.append(point)
        if len(power_history) > 60:
            power_history.pop(0)
        await asyncio.sleep(5)


# ── Monitor loop (coroutine) ──────────────────────────────────────────────────

async def monitor_loop():
    """
    Polls Shelly EM every POLL_INTERVAL seconds, runs PI controller,
    enforces safety rules, and updates _current_duty for burst_control_loop.
    """
    global current_grid_power, equipment_power, force_mode_active, safe_state, equipment_active
    global last_shelly_error, _current_duty, _last_good_poll, _safe_state_logged
    global current_water_temp, current_ssr_temp, grid_source, _last_data_log_time, _last_pi_time
    global _last_temp_read, fan_active, fan_percent, _jsy
    global _total_import_Wh, _total_redirect_Wh, _hourly_import_Wh, _hourly_redirect_Wh
    global _total_export_Wh, _hourly_export_Wh, _active_heating_secs, _last_stats_save
    global _solar_data_buffer, night_mode, _midnight_reset_done

    _init_ds18b20()
    _load_stats()
    _last_good_poll = utime.time()
    _last_stats_save = utime.time()

    # Ensure MQTT worker is running when Shelly MQTT is the grid source,
    # even if E_MQTT (status publishing) is disabled.
    if getattr(c_v, 'E_SHELLY_MQTT', False):
        m_c.ensure_started()

    d_u.print_and_store_log("Solar monitor loop started")

    while True:
        try:
            now = utime.time()
            # Timezone-aware minutes since midnight (Paris)
            curr_min = d_u.get_paris_time_minutes()
            
            # Night mode logic (disabled if FAKE_SHELLY is active for development)
            if getattr(c_v, 'FAKE_SHELLY', False):
                is_night = False
            else:
                n_start_str = getattr(c_v, 'NIGHT_START', "22:00")
                n_end_str = getattr(c_v, 'NIGHT_END', "05:50")
                
                # Use _time_to_minutes to handle HH:MM parsing
                night_start = _time_to_minutes(n_start_str)
                night_end = _time_to_minutes(n_end_str)
                
                if night_start < night_end:
                    is_night = (night_start <= curr_min < night_end)
                else: # Overnight range (e.g. 22:00 to 06:00)
                    is_night = (curr_min >= night_start or curr_min < night_end)
            
            if is_night != night_mode:
                night_mode = is_night
                d_u.print_and_store_log(f"SOLAR: {'Entering' if is_night else 'Leaving'} Night Mode")
                if not night_mode:
                    # Leaving night mode: ensure relay is ready and PI is fresh
                    _relay.value(1)
                    _pi.reset()

            poll_int = getattr(c_v, 'POLL_INTERVAL', 2)
            if night_mode:
                poll_int = getattr(c_v, 'NIGHT_POLL_INTERVAL', 15)
            
            # Dynamic watchdog: must be at least poll_int * 3 to allow for network jitters
            watchdog_timeout = max(getattr(c_v, 'SHELLY_TIMEOUT', 10), poll_int * 3)
            
            max_p = float(getattr(c_v, 'EQUIPMENT_MAX_POWER', 2000))
            base_setpoint = float(getattr(c_v, 'EXPORT_SETPOINT', 0))
            min_threshold = float(getattr(c_v, 'MIN_POWER_THRESHOLD', 150))
            
            status_tag = "WAIT"
            surplus = 0.0
            log_msg = None
            force_reason = "Unknown"
            
            # Mode Selection
            is_boost = utime.time() < boost_end_time
            is_force_equipment = getattr(c_v, 'FORCE_EQUIPMENT', False)
            in_window = _in_force_window() if getattr(c_v, 'E_FORCE_WINDOW', False) else False
            target_temp = getattr(c_v, 'EQUIPMENT_TARGET_TEMP', 55.0)
            target_reached = (current_water_temp is not None and current_water_temp >= target_temp)
            
            is_forcing = (is_force_equipment or in_window or is_boost) and not target_reached
            force_mode_active = is_forcing

            # ── ESP32 Temperature safety cutoff ───────────────────────────────
            esp_temp = esp32.mcu_temperature()
            current_esp_temp = esp_temp
            max_esp_temp = getattr(c_v, 'MAX_ESP32_TEMP', 70.0)
            if esp_temp >= max_esp_temp:
                d_u.print_and_store_log(
                    f"SOLAR SAFETY: ESP32 {esp_temp:.1f}C >= {max_esp_temp}C — equipment OFF"
                )
                emergency_mode = True
                _current_duty = 0.0
                _emergency_shutdown()
                _publish_status_mqtt()
                await asyncio.sleep(poll_int)
                continue

            # ── DS18B20: read every 30 s regardless of loop speed ───────────────
            temp_interval = getattr(c_v, 'TEMP_READ_INTERVAL', 30)
            if (now - _last_temp_read) >= temp_interval:
                _last_temp_read = now
                await _read_temps()
                
                # SSR Fan Control Logic (PWM 4-pin fan)
                if getattr(c_v, 'E_FAN', False) and current_ssr_temp is not None:
                    _fan_max  = float(getattr(c_v, 'SSR_MAX_TEMP', 75.0))
                    _fan_low  = _fan_max - float(getattr(c_v, 'FAN_TEMP_OFFSET', 10))
                    new_percent = 0
                    if current_ssr_temp >= _fan_max:
                        new_percent = 100
                    elif current_ssr_temp >= _fan_low:
                        new_percent = 50
                    
                    if new_percent != fan_percent:
                        d_u.print_and_store_log(f"SOLAR COOLING: Fan speed {new_percent}% (temp={current_ssr_temp}°C)")
                        fan_percent = new_percent
                        fan_active = (new_percent > 0)
                        if _fan_pin:
                            # duty_u16 range is 0-65535
                            duty = int(new_percent * 65535 / 100)
                            _fan_pin.duty_u16(duty)

            # ── Temperature safety cutoffs ─────────────────────────────────────
            # 1. Equipment/Water
            max_water_temp = getattr(c_v, 'EQUIPMENT_MAX_TEMP', 65.0)
            if current_water_temp is not None and current_water_temp >= max_water_temp:
                d_u.print_and_store_log(
                    f"SOLAR SAFETY: water {current_water_temp}°C >= {max_water_temp}°C — equipment OFF"
                )
                emergency_mode = True
                _current_duty = 0.0
                _emergency_shutdown()
                _publish_status_mqtt()
                await asyncio.sleep(poll_int)
                continue
            
            # 2. SSR Heatsink
            max_ssr_temp = getattr(c_v, 'SSR_MAX_TEMP', 75.0)
            if current_ssr_temp is not None and current_ssr_temp >= max_ssr_temp:
                d_u.print_and_store_log(
                    f"SOLAR SAFETY: SSR {current_ssr_temp}°C >= {max_ssr_temp}°C — equipment OFF"
                )
                emergency_mode = True
                _current_duty = 0.0
                _emergency_shutdown()
                _publish_status_mqtt()
                await asyncio.sleep(poll_int)
                continue
            
            # Re-enable relay if we were in safety (e.g. overheat cooled down)
            # AND we are not in safe_state (Shelly is reachable)
            if _relay.value() == 0 and not safe_state:
                d_u.print_and_store_log("SOLAR SAFETY: conditions back to normal — re-enabling relay")
                _relay.value(1)
                emergency_mode = False

            # ── Grid Power Retrieval ──────────────────────────────────────────
            if getattr(c_v, 'FAKE_SHELLY', False):
                # Direct in-process read — no socket, no MQTT, overrides E_JSY /
                # E_SHELLY_MQTT so FAKE_SHELLY works regardless of other source flags.
                try:
                    import fake_shelly as _fs_mod
                    current_grid_power = float(_fs_mod._grid_power)
                    last_shelly_error = None
                except Exception as _e:
                    last_shelly_error = str(_e)
                if grid_source != "FAKE":
                    grid_source = "FAKE"
                    d_u.print_and_store_log("SOLAR: FAKE_SHELLY grid source active")
                _last_good_poll = now
                safe_state = False
                _safe_state_logged = False

            else:
                # 1. Try JSY (Wired UART) first if enabled
                use_shelly = True
                if getattr(c_v, 'E_JSY', False):
                    # Import and Init on first run
                    global _jsy
                    if _jsy is None:
                        from jsy_mk194 import JSY_MK194
                        _jsy = JSY_MK194(c_v.JSY_UART_ID, c_v.JSY_TX, c_v.JSY_RX)
                        d_u.print_and_store_log("SOLAR: JSY-MK-194 initialized")

                    jsy_data = _jsy.read_data()
                    if jsy_data:
                        current_grid_power, equipment_power = jsy_data
                        if grid_source != "JSY":
                            d_u.print_and_store_log("SOLAR: JSY-MK-194 grid source active")
                        grid_source = "JSY"
                        last_shelly_error = None
                        _last_good_poll = now
                        use_shelly = False
                        if safe_state:
                            d_u.print_and_store_log("SOLAR JSY-MK-194 recovered — resuming control")
                            _pi.reset()
                        safe_state = False
                    else:
                        # JSY error: wait for next poll
                        if (now - _last_good_poll) >= watchdog_timeout:
                            if not _safe_state_logged:
                                d_u.print_and_store_log("SOLAR WATCHDOG: JSY-MK-194 timeout — safe-state")
                                _safe_state_logged = True
                                _pi.reset()
                            safe_state = True
                            _current_duty = 0.0
                            _emergency_shutdown()
                        await asyncio.sleep(0.1)
                        continue

                # 2. Try MQTT if enabled and JSY not used
                if getattr(c_v, 'E_SHELLY_MQTT', False):
                    # --- MQTT SOURCE ---
                    mqtt_val = m_c.latest_mqtt_grid_power[0]
                    # In night mode, we only process MQTT data if poll_int (60s) has passed
                    time_since_poll = now - _last_good_poll
                    if mqtt_val is not None and (not night_mode or time_since_poll >= poll_int):
                        # Fresh data received or interval reached: consume
                        m_c.latest_mqtt_grid_power[0] = None

                        if grid_source != "MQTT":
                            d_u.print_and_store_log("SOLAR: MQTT grid source active")
                        grid_source = "MQTT"
                        current_grid_power = mqtt_val
                        last_shelly_error = None
                        _last_good_poll = now
                        if safe_state:
                            d_u.print_and_store_log("SOLAR Shelly MQTT recovered — resuming control")
                            _relay.value(1)
                            _pi.reset()
                            _safe_state_logged = False
                        safe_state = False
                    else:
                        # No new data: check for timeout then skip PI logic
                        if (now - _last_good_poll) >= watchdog_timeout:
                            if not _safe_state_logged:
                                d_u.print_and_store_log("SOLAR WATCHDOG: No MQTT data from Shelly — safe-state")
                                _safe_state_logged = True
                                _pi.reset()
                            if not safe_state:
                                _emergency_shutdown()
                            safe_state = True
                            _current_duty = 0.0
                        await asyncio.sleep(0.1)
                        continue

                else:
                    # --- STRICT HTTP MODE ---
                    if grid_source != "HTTP":
                        grid_source = "HTTP"
                        d_u.print_and_store_log("SOLAR: HTTP grid source active")

                    # Wait for poll interval
                    if (now - _last_good_poll) >= poll_int:
                        try:
                            current_grid_power = await _get_shelly_power_async()
                            last_shelly_error  = None
                            _last_good_poll    = now
                            if safe_state:
                                d_u.print_and_store_log("SOLAR Shelly HTTP recovered — re-enabling relay")
                                _relay.value(1)
                                _pi.reset()
                            safe_state         = False
                            _safe_state_logged = False
                        except Exception as err:
                            last_shelly_error = str(err)
                            if (now - _last_good_poll) >= watchdog_timeout:
                                if not _safe_state_logged:
                                    d_u.print_and_store_log("SOLAR WATCHDOG: Shelly HTTP unreachable — safe-state")
                                    _safe_state_logged = True
                                    _pi.reset()
                                if not safe_state:
                                    _emergency_shutdown()
                                safe_state    = True
                                _current_duty = 0.0
                    else:
                        await asyncio.sleep(0.1)
                        continue

            if target_reached and (is_force_equipment or in_window or is_boost):
                if _current_duty > 0:
                    d_u.print_and_store_log(
                        f"SOLAR Force mode: target {target_temp}C reached — holding"
                    )
                _current_duty = 0.0
                _hardware_off()
                _publish_status_mqtt()
                await asyncio.sleep(poll_int)
                continue

            # ── Surplus calculation and diversion ────────────────────────────
            if is_forcing:
                # Force mode: run at full duty, let burst_control_loop drive the relay
                _current_duty = 1.0
                if is_force_equipment:
                    force_reason = "FORCE_EQUIPMENT"
                elif is_boost:
                    force_reason = "BOOST"
                else:
                    _t = utime.localtime()
                    force_reason = "WINDOW({:02d}:{:02d} in {}-{})".format(
                        _t[3], _t[4],
                        getattr(c_v, 'FORCE_START', '?'),
                        getattr(c_v, 'FORCE_END', '?')
                    )
                d_u.print_and_store_log(
                    f"SOLAR FORCE({force_reason}) grid={current_grid_power}W"
                    f" duty=1.0 {getattr(c_v, 'EQUIPMENT_NAME', 'EQUIPMENT')}≈{max_p:.0f}W"
                    + (f" temp={current_water_temp}C" if current_water_temp is not None else "")
                )
                _publish_status_mqtt()
                await asyncio.sleep(poll_int)
                continue

            surplus = base_setpoint - current_grid_power  # positive = room to ramp up toward setpoint

            # Minimum off-time guard (anti-cycling when equipment is off)
            min_off = getattr(c_v, 'MIN_OFF_TIME', 30)
            if _current_duty == 0.0 and (now - _last_off_time) < min_off:
                remaining = min_off - (now - _last_off_time)
                _store_data_log(
                    f"SOLAR [OFF-WAIT {remaining:.0f}s] grid={current_grid_power:.0f}W surplus={surplus:.0f}W"
                )
                _publish_status_mqtt()
                await asyncio.sleep(poll_int)
                continue

            # Compute dt here so energy accumulation can use it regardless of PI path
            now_ms = utime.ticks_ms()
            if _last_pi_time == 0:
                dt = float(poll_int)
            else:
                dt = utime.ticks_diff(now_ms, _last_pi_time) / 1000.0
            _last_pi_time = now_ms

            # Threshold: only prevents *starting* when headroom to setpoint is negligible.
            # Never cut running equipment — the PI's negative error ramps duty down smoothly.
            if surplus < min_threshold and _current_duty == 0.0:
                status_tag = "OFF"
            else:
                # ── 3-region deadband + PI (best of C++ and Python) ──────────
                # surplus = base_setpoint - grid_power
                #   > +DEADBAND_W  → Region 1: ramp UP   (clear solar surplus)
                #   in ±DEADBAND_W → Region 2: HOLD      (stable, freeze integral)
                #   < -DEADBAND_W  → Region 3: ramp DOWN  (importing too much)
                error = (base_setpoint - current_grid_power) / max_p
                deadband_w = float(getattr(c_v, 'DEADBAND_W', 30))
                transient_threshold = float(getattr(c_v, 'TRANSIENT_RESET_THRESHOLD', 200))

                # Large-transient guard: grid jumped far above setpoint (e.g. big load on).
                if (current_grid_power > base_setpoint + transient_threshold
                        and _current_duty > 0.0):
                    _pi.reset()
                    _store_data_log(
                        f"SOLAR: large transient (grid={current_grid_power:.0f}W, "
                        f"setpoint={base_setpoint:.0f}W) — PI reset"
                    )

                if surplus > deadband_w:
                    # Region 1: clear surplus → ramp equipment UP
                    _current_duty = _pi.update(error, dt)
                    status_tag = "PI+({:.0f}W)".format(_current_duty * max_p)

                elif surplus < -deadband_w:
                    # Region 3: importing more than target → ramp equipment DOWN.
                    # Anti-oscillation nudge (C++ "+1" equivalent): adds a small
                    # upward offset so the controller doesn't overshoot to 0 on
                    # small transients and avoids rapid on/off cycling.
                    raw = _pi.update(error, dt)
                    nudge = float(getattr(c_v, 'RAMP_DOWN_NUDGE', 0.01))
                    _current_duty = max(0.0, min(1.0, raw + nudge)) if _current_duty > 0.0 else raw
                    if _current_duty > 0.0:
                        status_tag = "PI-({:.0f}W)".format(_current_duty * max_p)
                    else:
                        status_tag = "OFF(PI)"
                        _pi.reset()

                else:
                    # Region 2: within ±DEADBAND_W of setpoint → hold duty.
                    # Integral is frozen (no _pi.update) so it can't drift.
                    status_tag = "HOLD({:.0f}W)".format(_current_duty * max_p)
                
            # ── Energy Accumulation (Wh) ──────────────────────────────────
            # dt is the time in seconds since last loop
            # This must happen outside the threshold check to log idle consumption!
            if dt > 0 and dt < 60: # Avoid spikes from large time jumps
                curr_hour = (curr_min // 60) % 24
                # 1. Grid import (only when grid > 0)
                if current_grid_power > 0:
                    # Wh = Watts * (seconds / 3600)
                    delta = current_grid_power * (dt / 3600.0)
                    _total_import_Wh += delta
                    _hourly_import_Wh[curr_hour] += delta
                # 2. Grid export (only when grid < 0)
                elif current_grid_power < 0:
                    delta = -current_grid_power * (dt / 3600.0)
                    _total_export_Wh += delta
                    _hourly_export_Wh[curr_hour] += delta
                
                # 3. Redirected power
                if equipment_power > 0:
                    delta = equipment_power * (dt / 3600.0)
                    _total_redirect_Wh += delta
                    _hourly_redirect_Wh[curr_hour] += delta
                    _active_heating_secs += dt

            # ── Stats & Log Periodic Flush ──────────────────────────────────
            # 1. Save stats to JSON every 15 minutes (or on day change)
            if (now - _last_stats_save) >= 900:
                _save_stats_to_file()
                _last_stats_save = now
            
            # Reset daily counters at midnight (00:00 to 00:01)
            if curr_min == 0:
                if not _midnight_reset_done:
                    d_u.print_and_store_log("STATS: Midnight - saving and resetting daily counters")
                    _save_stats_to_file()
                    _total_import_Wh = 0.0
                    _total_redirect_Wh = 0.0
                    _total_export_Wh = 0.0
                    _hourly_import_Wh = [0.0] * 24
                    _hourly_redirect_Wh = [0.0] * 24
                    _hourly_export_Wh = [0.0] * 24
                    _active_heating_secs = 0
                    _midnight_reset_done = True
                    
                    # Periodic NTP sync to avoid clock drift (once per day)
                    if getattr(c_v, 'E_WIFI', False):
                        try:
                            d_u.set_time_with_ntp()
                        except:
                            pass
            else:
                _midnight_reset_done = False

            # --- Selective Logging ---
            log_msg = (
                f"SOLAR [{status_tag}] grid={current_grid_power:.0f}W"
                f" surplus={surplus:.0f}W"
                f" {getattr(c_v, 'EQUIPMENT_NAME', 'EQUIPMENT')}={_current_duty * max_p:.0f}W({_current_duty * 100:.0f}%)"
                + (f" temp={current_water_temp}C" if current_water_temp is not None else "")
            )
            
            # 1. Print to console (always)
            print(utime.time(), ": ", log_msg)
            
            # 2. Store to RAM buffer (every 1 minute)
            if log_msg and (now - _last_data_log_time) >= 60:
                _store_data_log(log_msg)
                _last_data_log_time = now
            
            # 3. Periodic flush of all logs to flash (every 15 minutes)
            if (now % 900) < (poll_int + 1):
                _flush_solar_data()
                d_u.flush_logs()

            # ── MQTT publish ──────────────────────────────────────────────────
            _publish_status_mqtt()

            # Dynamic sleep: fast for MQTT, POLL_INTERVAL for HTTP.
            # In Night Mode, always use poll_int (60s).
            if night_mode:
                await asyncio.sleep(poll_int)
            elif getattr(c_v, 'E_SHELLY_MQTT', False) and grid_source == "MQTT":
                await asyncio.sleep(0.5) # Fast check for new MQTT pushes
            else:
                await asyncio.sleep(poll_int)

        except Exception as err:
            d_u.print_and_store_log(f"SOLAR monitor loop critical error: {err}")
            await asyncio.sleep(5)
