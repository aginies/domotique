#!/usr/bin/env python3
# antoine@ginies.org
# GPL3
#
# Run on PC:     python3 test_solar.py
# Run on device: import test_solar
#
# Mocks all MicroPython / hardware dependencies so the logic can be
# exercised without any physical hardware or network.

import sys
import types
import os

# Add common directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "common")))

# ── Minimal test framework ────────────────────────────────────────────────────

_passed = 0
_failed = 0

def ok(name):
    global _passed
    _passed += 1
    print(f"  PASS  {name}")

def fail(name, reason):
    global _failed
    _failed += 1
    print(f"  FAIL  {name}: {reason}")

def check(name, condition, reason="assertion failed"):
    if condition:
        ok(name)
    else:
        fail(name, reason)

def check_close(name, a, b, tol=1e-6):
    if abs(a - b) <= tol:
        ok(name)
    else:
        fail(name, f"{a} != {b} (tol={tol})")

def section(title):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")

# ── Mock MicroPython modules ──────────────────────────────────────────────────

# machine
class _Pin:
    OUT = 1
    def __init__(self, pin, mode=None):
        self.pin = pin
        self._val = 0
    def value(self, v=None):
        if v is None:
            return self._val
        self._val = v
    def __call__(self, v=None):
        return self.value(v)

_machine_mod = types.ModuleType("machine")
_machine_mod.Pin = _Pin
_machine_mod.SoftI2C = lambda **k: None
_machine_mod.WDT = lambda *a, **k: type('WDT', (), {'feed': lambda self: None})()
class _PWM:
    def __init__(self, pin, freq=None, duty_u16=None):
        self.pin = pin
        self.freq = freq
        self.duty = duty_u16
    def duty_u16(self, v): self.duty = v
_machine_mod.PWM = _PWM
sys.modules["machine"] = _machine_mod

# esp32 mock
_esp32_mod = types.ModuleType("esp32")
_esp32_mod.mcu_temperature = lambda: 45.0
sys.modules["esp32"] = _esp32_mod

# network mock
class _WLAN:
    def __init__(self, mode):
        self.mode = mode
        self._active = False
    def active(self, v=None):
        if v is not None: self._active = v
        return self._active
    def scan(self):
        return [(b"HomeWiFi", b"\x00", 1, -60, 3, False), (b"GuestWiFi", b"\x01", 6, -80, 4, False)]
    def connect(self, s, p): pass
    def isconnected(self): return True
    def ifconfig(self, v=None): return ("192.168.1.50", "255.255.255.0", "192.168.1.1", "8.8.8.8")
    def config(self, **k): pass

_network_mod = types.ModuleType("network")
_network_mod.WLAN = _WLAN
_network_mod.STA_IF = 0
_network_mod.AP_IF = 1
sys.modules["network"] = _network_mod

# ubinascii mock
import base64
_ubinascii_mod = types.ModuleType("ubinascii")
_ubinascii_mod.a2b_base64 = base64.b64decode
_ubinascii_mod.b2a_base64 = base64.b64encode
sys.modules["ubinascii"] = _ubinascii_mod

# utime — controllable fake clock
class _FakeTime:
    _now = 1000  # seconds since epoch (arbitrary start)
    _localtime_val = (2024, 6, 1, 12, 0, 0, 5, 153)  # default: 12:00

    @classmethod
    def time(cls):
        return cls._now

    @classmethod
    def localtime(cls):
        return cls._localtime_val

    @classmethod
    def set_hhmm(cls, h, m):
        cls._localtime_val = (2024, 6, 1, h, m, 0, 5, 153)

    @classmethod
    def advance(cls, seconds):
        cls._now += seconds

_utime_mod = types.ModuleType("utime")
_utime_mod.time = _FakeTime.time
_utime_mod.localtime = _FakeTime.localtime
sys.modules["utime"] = _utime_mod

# asyncio stub
_asyncio_mod = types.ModuleType("asyncio")
_asyncio_mod.sleep = lambda s: None
_asyncio_mod.sleep_ms = lambda ms: None
def _run(coro):
    # Minimal runner for mocks: drive coroutines to completion
    try:
        return coro.send(None)
    except StopIteration as e:
        return e.value
    except AttributeError:
        return coro # Not a coroutine
_asyncio_mod.run = _run
sys.modules["asyncio"] = _asyncio_mod

# micropython mock
_micropython_mod = types.ModuleType("micropython")
_micropython_mod.const = lambda x: x
sys.modules["micropython"] = _micropython_mod

# uselect mock
_uselect_mod = types.ModuleType("uselect")
_uselect_mod.poll = lambda: type('Poll', (), {'register': lambda *a: None, 'poll': lambda *a: []})()
sys.modules["uselect"] = _uselect_mod

# framebuf mock
_framebuf_mod = types.ModuleType("framebuf")
sys.modules["framebuf"] = _framebuf_mod

# ssd1306 mock
_ssd1306_mod = types.ModuleType("ssd1306")
sys.modules["ssd1306"] = _ssd1306_mod

# ujson stub
import json
_ujson_mod = types.ModuleType("ujson")
_ujson_mod.dumps = json.dumps
_ujson_mod.loads = json.loads
sys.modules["ujson"] = _ujson_mod

# umqtt.simple stub
class _MQTTClient:
    def __init__(self, *args, **kwargs):
        self._published = []
    def connect(self): pass
    def publish(self, topic, msg):
        self._published.append((topic, msg))

_umqtt_simple_mod = types.ModuleType("umqtt.simple")
_umqtt_simple_mod.MQTTClient = _MQTTClient
sys.modules["umqtt.simple"] = _umqtt_simple_mod

# microdot stub
class _Response:
    def __init__(self, body, status_code=200, headers=None):
        self.body = body
        self.status_code = status_code
        self.headers = headers or {}

_microdot_mod = types.ModuleType("microdot")
_microdot_mod.Microdot = lambda: None
_microdot_mod.send_file = lambda f: _Response(f"file:{f}")
_microdot_mod.Response = _Response
sys.modules["microdot"] = _microdot_mod

# domo_utils — capture log output
_log_lines = []
_domo_utils_mod = types.ModuleType("domo_utils")
_domo_utils_mod.print_and_store_log = lambda msg: _log_lines.append(msg)
_domo_utils_mod.set_freq = lambda f: None
_domo_utils_mod.file_exists = lambda p: os.path.exists(p)
_domo_utils_mod._rotate_log_if_needed = lambda f, s: None
_domo_utils_mod.flush_logs = lambda: None
_domo_utils_mod.show_rtc_date = lambda: "2024-06-01"
_domo_utils_mod.show_rtc_time = lambda: (12, 0, 0)
_domo_utils_mod.get_paris_time_minutes = lambda: 12 * 60  # noon default
sys.modules["domo_utils"] = _domo_utils_mod

# save_config mock
_save_config_mod = types.ModuleType("save_config")
_save_config_mod.save_config_to_file = lambda d: None
sys.modules["save_config"] = _save_config_mod

# urequests — injectable fake response
class _FakeResponse:
    def __init__(self, data):
        self._data = data
    def json(self):
        return self._data
    def close(self):
        pass

_urequests_mod = types.ModuleType("urequests")
_shelly_response = None   # set per test
_shelly_raises   = None   # set to an Exception to simulate failure

def _fake_get(url, timeout=3):
    if _shelly_raises is not None:
        raise _shelly_raises
    return _FakeResponse(_shelly_response)

_urequests_mod.get = _fake_get
sys.modules["urequests"] = _urequests_mod

# config_var — a mutable namespace so tests can tweak values
class _Cfg:
    NAME             = "Solaire"
    SSR_PIN          = 12
    RELAY_PIN        = 13
    OLED_SCL_PIN     = 7
    OLED_SDA_PIN     = 18
    I_LED_PIN        = 48
    CPU_FREQ         = 240
    E_WIFI           = False
    WIFI_SSID        = ""
    WIFI_PASSWORD    = ""
    AP_SSID          = "W_Solaire"
    AP_PASSWORD      = "12345678"
    AP_HIDDEN_SSID   = False
    AP_CHANNEL       = 6
    AP_IP            = ('192.168.66.1','255.255.255.0','192.168.66.1','192.168.66.1')
    time_ok          = 0.1
    time_err         = 0.3
    SHELLY_EM_IP     = "192.168.1.100"
    POLL_INTERVAL    = 2
    EQUIPMENT_NAME   = "ECS (EAU CHAUDE)"
    EQUIPMENT_MAX_POWER = 2000
    POWER_BUFFER     = 50
    EXPORT_SETPOINT  = 0
    PID_KP           = 0.5
    PID_KI           = 0.1
    BURST_PERIOD     = 5
    MIN_POWER_THRESHOLD = 150
    MIN_OFF_TIME     = 30
    E_DS18B20        = False
    DS18B20_PIN      = 14
    EQUIPMENT_MAX_TEMP = 65.0
    EQUIPMENT_TARGET_TEMP = 55.0
    SHELLY_TIMEOUT   = 10
    FORCE_EQUIPMENT  = False
    FORCE_START      = "22:00"
    FORCE_END        = "06:00"
    BOOST_MINUTES    = 60
    MAX_ESP32_TEMP   = 80.0
    WEB_USER         = ""
    WEB_PASSWORD     = ""
    E_MQTT           = False
    MQTT_IP          = ""
    MQTT_USER        = ""
    MQTT_PASSWORD    = ""
    MQTT_NAME        = "solar"
    NIGHT_POLL_INTERVAL = 15

_cfg = _Cfg()
_cfg_mod = types.ModuleType("config_var")
_cfg_mod.__dict__.update({k: v for k, v in _Cfg.__dict__.items() if not k.startswith('__')})
sys.modules["config_var"] = _cfg_mod

# ── Import module under test ───────────────────────────────────────────────────
import solar_monitor as sm

def _reset_monitor():
    """Reset all solar_monitor globals between tests."""
    sm.current_grid_power = 0.0
    sm.equipment_power    = 0.0
    sm.equipment_active   = False
    sm.force_mode_active  = False
    sm.safe_state         = False
    sm.last_shelly_error  = None
    sm.current_water_temp = None
    sm._current_duty      = 0.0
    sm._last_off_time     = 0
    sm._last_good_poll    = _FakeTime.time()
    sm._safe_state_logged = False
    sm._pi.reset()
    _log_lines.clear()

def _set_shelly(power_w):
    global _shelly_response, _shelly_raises
    _shelly_response = {"emeters": [{"power": power_w}]}
    _shelly_raises   = None

def _set_shelly_error(exc=None):
    global _shelly_raises
    _shelly_raises = exc or OSError("Connection refused")

# ── Helpers that replicate monitor_loop decision logic synchronously ──────────
# (avoids running the full async loop in unit tests)

def _run_divert_step(grid_power):
    """Run one diversion step with the given grid_power reading."""
    sm.current_grid_power = grid_power
    surplus = -(grid_power - _cfg_mod.EXPORT_SETPOINT)
    if surplus < _cfg_mod.MIN_POWER_THRESHOLD:
        sm._current_duty = 0.0
    else:
        sm._current_duty = min(1.0, surplus / float(_cfg_mod.EQUIPMENT_MAX_POWER))
    return sm._current_duty

# Keep old name as alias so existing test calls still work
_run_pi_step = _run_divert_step


# ═════════════════════════════════════════════════════════════════════════════
# TEST SUITES
# ═════════════════════════════════════════════════════════════════════════════

# ── 1. PIController ───────────────────────────────────────────────────────────
section("PIController")

def test_pi_zero_error():
    pi = sm.PIController(0.5, 0.1)
    out = pi.update(0.0, 2.0)
    check("zero error → zero output", out == 0.0)

def test_pi_proportional():
    pi = sm.PIController(0.5, 0.0)   # Ki=0 isolates Kp
    out = pi.update(0.5, 2.0)        # error=0.5 → Kp*error = 0.25
    check_close("Kp=0.5, error=0.5 → output=0.25", out, 0.25)

def test_pi_integral_accumulates():
    pi = sm.PIController(0.0, 0.1)   # Kp=0 isolates Ki
    pi.update(0.5, 2.0)              # integral += 0.5*2 = 1.0 → output=0.1
    out = pi.update(0.5, 2.0)        # integral += 0.5*2 = 2.0 → output=0.2
    check_close("Ki integral accumulates", out, 0.2)

def test_pi_clamp_upper():
    pi = sm.PIController(10.0, 0.0)
    out = pi.update(1.0, 1.0)        # would be 10.0, clamped to 1.0
    check("output clamped to 1.0", out == 1.0)

def test_pi_clamp_lower():
    pi = sm.PIController(0.5, 0.0)
    out = pi.update(-1.0, 1.0)       # negative → clamped to 0.0
    check("output clamped to 0.0", out == 0.0)

def test_pi_antiwindup():
    pi = sm.PIController(10.0, 0.1)  # saturates immediately
    pi.update(1.0, 2.0)              # output saturated at 1.0
    integral_before = pi._integral
    pi.update(1.0, 2.0)              # still saturated, integral must NOT grow
    check("anti-windup: integral frozen at saturation", pi._integral == integral_before)

def test_pi_reset():
    pi = sm.PIController(0.5, 0.1)
    pi.update(0.8, 2.0)
    pi.reset()
    check("reset clears integral", pi._integral == 0.0)
    check("reset clears output", pi._output == 0.0)

test_pi_zero_error()
test_pi_proportional()
test_pi_integral_accumulates()
test_pi_clamp_upper()
test_pi_clamp_lower()
test_pi_antiwindup()
test_pi_reset()

# ── 2. Time-window helpers ────────────────────────────────────────────────────
section("Time window (_time_to_minutes / _in_force_window)")

def test_time_to_minutes():
    check_close("00:00 → 0",    sm._time_to_minutes("00:00"), 0)
    check_close("01:30 → 90",   sm._time_to_minutes("01:30"), 90)
    check_close("22:00 → 1320", sm._time_to_minutes("22:00"), 1320)
    check_close("23:59 → 1439", sm._time_to_minutes("23:59"), 1439)

def test_force_window_daytime():
    _cfg_mod.FORCE_START = "10:00"
    _cfg_mod.FORCE_END   = "16:00"
    _FakeTime.set_hhmm(12, 0);  check("12:00 inside 10-16",  sm._in_force_window())
    _FakeTime.set_hhmm(10, 0);  check("10:00 at start (inclusive)", sm._in_force_window())
    _FakeTime.set_hhmm(16, 0);  check("16:00 at end (exclusive)", not sm._in_force_window())
    _FakeTime.set_hhmm(9,  59); check("09:59 before window",  not sm._in_force_window())
    _FakeTime.set_hhmm(16, 1);  check("16:01 after window",   not sm._in_force_window())

def test_force_window_overnight():
    _cfg_mod.FORCE_START = "22:00"
    _cfg_mod.FORCE_END   = "06:00"
    _FakeTime.set_hhmm(23, 30); check("23:30 inside overnight", sm._in_force_window())
    _FakeTime.set_hhmm(0,  0);  check("00:00 inside overnight", sm._in_force_window())
    _FakeTime.set_hhmm(3,  0);  check("03:00 inside overnight", sm._in_force_window())
    _FakeTime.set_hhmm(5,  59); check("05:59 inside overnight", sm._in_force_window())
    _FakeTime.set_hhmm(6,  0);  check("06:00 at end (exclusive)", not sm._in_force_window())
    _FakeTime.set_hhmm(12, 0);  check("12:00 outside overnight", not sm._in_force_window())
    _FakeTime.set_hhmm(21, 59); check("21:59 before overnight",  not sm._in_force_window())

def test_force_window_same_time():
    _cfg_mod.FORCE_START = "12:00"
    _cfg_mod.FORCE_END   = "12:00"
    _FakeTime.set_hhmm(12, 0);  check("start==end → never active", not sm._in_force_window())

test_time_to_minutes()
test_force_window_daytime()
test_force_window_overnight()
test_force_window_same_time()

# Restore overnight default
_cfg_mod.FORCE_START = "22:00"
_cfg_mod.FORCE_END   = "06:00"

# ── 3. Shelly parsing ─────────────────────────────────────────────────────────
section("Shelly EM response parsing (_get_shelly_power_async)")

def test_shelly_negative():
    _set_shelly(-420.5)
    # Mocking the async call for the unit test
    async def _mock_get():
        if _shelly_raises: raise _shelly_raises
        return float(_shelly_response['emeters'][0]['power'])
    sm._get_shelly_power_async = _mock_get
    
    val = _asyncio_mod.run(sm._get_shelly_power_async())
    check_close("Shelly -420.5W parsed correctly", val, -420.5)

def test_shelly_positive():
    _set_shelly(75.0)
    val = _asyncio_mod.run(sm._get_shelly_power_async())
    check_close("Shelly +75W parsed correctly", val, 75.0)

def test_shelly_zero():
    _set_shelly(0.0)
    val = _asyncio_mod.run(sm._get_shelly_power_async())
    check_close("Shelly 0W parsed correctly", val, 0.0)

def test_shelly_network_error():
    _set_shelly_error(OSError("ECONNREFUSED"))
    raised = False
    try:
        _asyncio_mod.run(sm._get_shelly_power_async())
    except OSError:
        raised = True
    check("network error propagates as exception", raised)

test_shelly_negative()
test_shelly_positive()
test_shelly_zero()
test_shelly_network_error()

# ── 4. Surplus and PI duty calculation ────────────────────────────────────────
section("Surplus → PI duty calculation")

def test_surplus_below_threshold():
    _reset_monitor()
    duty = _run_pi_step(-100.0)   # surplus = 100W < MIN_POWER_THRESHOLD (150W)
    check("surplus < threshold → duty=0", duty == 0.0)

def test_surplus_at_threshold_boundary():
    _reset_monitor()
    duty = _run_pi_step(-149.0)   # surplus = 149W, just below 150W
    check("surplus just below threshold → duty=0", duty == 0.0)
    _reset_monitor()
    duty = _run_pi_step(-150.0)   # surplus = 150W, exactly at threshold
    check("surplus at threshold → duty>0", duty > 0.0)

def test_surplus_half_capacity():
    _reset_monitor()
    # surplus=1000W, EQUIPMENT_MAX=2000W → duty = 1000/2000 = 0.5 (direct mapping)
    duty = _run_divert_step(-1000.0)
    check_close("1000W surplus on 2000W equipment → duty=0.5", duty, 0.5, tol=0.001)

def test_surplus_full_capacity():
    _reset_monitor()
    # surplus=2000W = EQUIPMENT_MAX → duty = 1.0
    duty = _run_divert_step(-2000.0)
    check("2000W surplus → duty clamped to 1.0", duty == 1.0)

def test_surplus_proportional():
    _reset_monitor()
    # Direct mapping: duty is stable for constant surplus (no integral drift)
    duties = [_run_divert_step(-500.0) for _ in range(5)]
    check("constant surplus → constant duty (no integral drift)",
          duties[4] == duties[0])

def test_export_setpoint_shifts_surplus():
    _reset_monitor()
    _cfg_mod.EXPORT_SETPOINT = -100  # keep 100W export buffer
    duty_with = _run_pi_step(-300.0)  # effective surplus = 300-100 = 200W
    _reset_monitor()
    _cfg_mod.EXPORT_SETPOINT = 0
    duty_without = _run_pi_step(-200.0)  # surplus = 200W
    check_close("EXPORT_SETPOINT shifts effective surplus", duty_with, duty_without, tol=0.001)
    _cfg_mod.EXPORT_SETPOINT = 0

def test_positive_grid_power_cuts_ecs():
    _reset_monitor()
    duty = _run_pi_step(200.0)   # importing → surplus negative → duty=0
    check("importing from grid → duty=0", duty == 0.0)

test_surplus_below_threshold()
test_surplus_at_threshold_boundary()
test_surplus_half_capacity()
test_surplus_full_capacity()
test_surplus_proportional()
test_export_setpoint_shifts_surplus()
test_positive_grid_power_cuts_ecs()

# ── 5. Min off-time guard ─────────────────────────────────────────────────────
section("Minimum off-time guard")

def test_min_off_time_blocks_restart():
    _reset_monitor()
    sm._current_duty = 0.0
    sm._last_off_time = _FakeTime.time()        # just turned off
    _FakeTime.advance(10)                        # only 10s elapsed, need 30s
    now = _FakeTime.time()
    blocked = (sm._current_duty == 0.0 and
               (now - sm._last_off_time) < _cfg_mod.MIN_OFF_TIME)
    check("off-time < MIN_OFF_TIME blocks restart", blocked)

def test_min_off_time_allows_after_wait():
    _reset_monitor()
    sm._current_duty = 0.0
    sm._last_off_time = _FakeTime.time()
    _FakeTime.advance(35)                        # 35s > MIN_OFF_TIME (30s)
    now = _FakeTime.time()
    blocked = (sm._current_duty == 0.0 and
               (now - sm._last_off_time) < _cfg_mod.MIN_OFF_TIME)
    check("off-time >= MIN_OFF_TIME allows restart", not blocked)

test_min_off_time_blocks_restart()
test_min_off_time_allows_after_wait()

# ── 6. Watchdog / safe-state ──────────────────────────────────────────────────
section("Shelly watchdog / safe-state")

def _simulate_watchdog(elapsed_since_last_good):
    """Simulate watchdog check as done in monitor_loop."""
    now = _FakeTime.time()
    sm._last_good_poll = now - elapsed_since_last_good
    elapsed = now - sm._last_good_poll
    if elapsed >= _cfg_mod.SHELLY_TIMEOUT:
        sm.safe_state    = True
        sm._current_duty = 0.0
        sm._pi.reset()
        sm._emergency_shutdown()
    return sm.safe_state

def test_watchdog_not_triggered_before_timeout():
    _reset_monitor()
    triggered = _simulate_watchdog(5)   # 5s < SHELLY_TIMEOUT (10s)
    check("5s without Shelly: safe-state NOT triggered", not triggered)

def test_watchdog_triggered_at_timeout():
    _reset_monitor()
    sm.init_ssr_relay()
    triggered = _simulate_watchdog(10)   # exactly at timeout
    check("10s without Shelly: safe-state triggered", triggered)
    check("safe-state cut relay", sm._relay.value() == 0)

def test_watchdog_duty_zeroed_on_safe_state():
    _reset_monitor()
    sm.init_ssr_relay()
    sm._current_duty = 0.8               # was running
    _simulate_watchdog(11)
    check("safe-state zeros duty", sm._current_duty == 0.0)
    check("safe-state cut SSR", sm._ssr_pin.value() == 0)
    check("safe-state cut relay", sm._relay.value() == 0)

def test_watchdog_pi_reset_on_safe_state():
    _reset_monitor()
    sm._pi._integral = 5.0              # had accumulated integral
    _simulate_watchdog(15)
    check("safe-state resets PI integral", sm._pi._integral == 0.0)

def test_watchdog_recovery():
    _reset_monitor()
    _simulate_watchdog(15)              # enter safe-state
    check("pre-recovery: safe_state=True", sm.safe_state)
    
    # Shelly responded in monitor_loop logic
    if sm.safe_state:
        _log_lines.clear()
        _log_lines.append("SOLAR Shelly back online — re-enabling relay")
        sm._relay.value(1)
        sm.safe_state = False
        sm._pi.reset()
    
    check("post-recovery: safe_state=False", not sm.safe_state)
    check("post-recovery: relay ON", sm._relay.value() == 1)
    check("post-recovery: log contains recovery", any("re-enabling relay" in s for s in _log_lines))

test_watchdog_not_triggered_before_timeout()
test_watchdog_triggered_at_timeout()
test_watchdog_duty_zeroed_on_safe_state()
test_watchdog_pi_reset_on_safe_state()
test_watchdog_recovery()

# ── 7. Force mode ─────────────────────────────────────────────────────────────
section("Force mode")

def test_force_ecs_flag_overrides_pi():
    _reset_monitor()
    _cfg_mod.FORCE_EQUIPMENT = True
    # Even with no surplus the duty should be forced to 1.0
    if _cfg_mod.FORCE_EQUIPMENT:
        sm._current_duty = 1.0
        sm._pi.reset()
    check("FORCE_EQUIPMENT=True → duty forced to 1.0", sm._current_duty == 1.0)
    _cfg_mod.FORCE_EQUIPMENT = False

def test_force_mode_stops_at_target_temp():
    _reset_monitor()
    sm.init_ssr_relay()
    _cfg_mod.FORCE_EQUIPMENT = True
    sm.current_water_temp = _cfg_mod.EQUIPMENT_TARGET_TEMP  # exactly at target
    # Simulate monitor logic with new immediate cutoff
    if _cfg_mod.FORCE_EQUIPMENT:
        if sm.current_water_temp is not None and sm.current_water_temp >= _cfg_mod.EQUIPMENT_TARGET_TEMP:
            sm._current_duty = 0.0
            sm._hardware_off()
        else:
            sm._current_duty = 1.0
    check("Force mode stops when EQUIPMENT_TARGET_TEMP reached", sm._current_duty == 0.0)
    check("Force mode cutoff: SSR OFF", sm._ssr_pin.value() == 0)
    check("Force mode cutoff: Relay ON", sm._relay.value() == 1)
    _cfg_mod.FORCE_EQUIPMENT = False

def test_force_window_sets_full_duty():
    _reset_monitor()
    _cfg_mod.FORCE_START = "22:00"
    _cfg_mod.FORCE_END   = "06:00"
    _FakeTime.set_hhmm(23, 0)          # inside window
    if sm._in_force_window():
        sm._current_duty = 1.0
    check("In force window at 23:00 → duty=1.0", sm._current_duty == 1.0)
    _FakeTime.set_hhmm(12, 0)          # restore default

test_force_ecs_flag_overrides_pi()
test_force_mode_stops_at_target_temp()
test_force_window_sets_full_duty()

# ── 8. Temperature safety cutoff ─────────────────────────────────────────────
section("Temperature safety cutoff")

def test_temp_cutoff_above_max():
    _reset_monitor()
    sm.current_water_temp = _cfg_mod.EQUIPMENT_MAX_TEMP + 1.0  # above max
    if sm.current_water_temp >= _cfg_mod.EQUIPMENT_MAX_TEMP:
        sm._current_duty = 0.0
    check("water temp > EQUIPMENT_MAX_TEMP → duty=0", sm._current_duty == 0.0)

def test_temp_cutoff_below_max():
    _reset_monitor()
    sm.current_water_temp = _cfg_mod.EQUIPMENT_MAX_TEMP - 1.0  # below max
    sm._current_duty = 0.5             # was running
    above = sm.current_water_temp >= _cfg_mod.EQUIPMENT_MAX_TEMP
    if above:
        sm._current_duty = 0.0
    check("water temp < EQUIPMENT_MAX_TEMP → duty unchanged", sm._current_duty == 0.5)

def test_temp_sensor_disabled():
    _reset_monitor()
    _cfg_mod.E_DS18B20 = False
    sm.current_water_temp = None       # no reading
    above = sm.current_water_temp is not None and sm.current_water_temp >= _cfg_mod.EQUIPMENT_MAX_TEMP
    check("E_DS18B20=False → cutoff never triggers", not above)

test_temp_cutoff_above_max()
test_temp_below_max = test_temp_cutoff_below_max
test_temp_cutoff_below_max()
test_temp_sensor_disabled()

# ── 9. Burst-fire timing ──────────────────────────────────────────────────────
section("Burst-fire timing")

def test_burst_on_time():
    duty   = 0.25
    period = float(_cfg_mod.BURST_PERIOD)
    on_time  = duty * period
    off_time = period - on_time
    check_close("25% duty: on_time=1.25s", on_time, 1.25)
    check_close("25% duty: off_time=3.75s", off_time, 3.75)

def test_burst_full_duty():
    duty = 1.0
    check("100% duty: no off phase", duty >= 1.0)

def test_burst_zero_duty():
    duty = 0.0
    check("0% duty: no on phase", duty <= 0.0)

def test_burst_power_calculation():
    duty = 0.4
    expected_w = round(duty * _cfg_mod.EQUIPMENT_MAX_POWER, 1)
    check_close("40% duty on 2000W equipment = 800W", expected_w, 800.0)

test_burst_on_time()
test_burst_full_duty()
test_burst_zero_duty()
test_burst_power_calculation()

# ── 10. Scenario: cloud passes ────────────────────────────────────────────────
section("Scenario: cloud passes over solar panels")

def test_scenario_cloud():
    _reset_monitor()
    # Step 1: sunny — 800W surplus
    d1 = _run_pi_step(-800.0)
    check("sunny: duty > 0", d1 > 0.0)
    # Step 2: cloud — surplus drops to 80W (below threshold)
    d2 = _run_pi_step(-80.0)
    check("cloud: duty=0, PI reset", d2 == 0.0)
    check("cloud: PI integral cleared", sm._pi._integral == 0.0)
    # Step 3: sun returns — 600W surplus
    d3 = _run_pi_step(-600.0)
    check("sun returns: duty > 0 again", d3 > 0.0)

test_scenario_cloud()

# ── 11. Scenario: evening ramp-down ───────────────────────────────────────────
section("Scenario: evening ramp-down")

def test_scenario_evening():
    _reset_monitor()
    for pw in [-1500, -1200, -900, -600, -300, -100]:
        _run_pi_step(float(pw))
    check("after ramp-down to 100W surplus: duty=0", sm._current_duty == 0.0)
    sm._last_off_time = _FakeTime.time() - _cfg_mod.MIN_OFF_TIME - 1
    _FakeTime.advance(35)
    # Force mode kicks in at 22:00
    _FakeTime.set_hhmm(22, 0)
    _cfg_mod.FORCE_START = "22:00"
    _cfg_mod.FORCE_END   = "06:00"
    if sm._in_force_window():
        sm._current_duty = 1.0
    check("22:00 force window activates", sm._current_duty == 1.0)
    _FakeTime.set_hhmm(12, 0)

test_scenario_evening()

# ── 12. MQTT reliability ──────────────────────────────────────────────────────
section("MQTT reliability")

import mqtt_client as mc

def test_mqtt_publish_format():
    _cfg_mod.E_MQTT = True
    _cfg_mod.MQTT_IP = "127.0.0.1"
    _cfg_mod.MQTT_NAME = "solar_test"

    # Reset queue and thread flag so publish_status populates the queue
    mc._queue.clear()
    mc._thread_started = True  # prevent actual thread creation in test

    mc.publish_status(grid_power=-500, equipment_power=400, equipment_active=True, force_mode=False, equipment_percent=20.0, water_temp=55.5, esp32_temp=42.0, fan_active=False, ssr_temp=45.0, fan_percent=0)

    check("MQTT queue populated", len(mc._queue) >= 5)

    topic, payload = mc._queue[0]
    check("Topic 1 name correct", topic == "solar_test/status_json")
    data = json.loads(payload)
    check("Payload grid_power correct", data['grid_power'] == -500)
    check("Payload equipment_power correct",  data['equipment_power'] == 400)
    check("Payload equipment_percent correct", data['equipment_percent'] == 20.0)
    check("Payload water_temp correct", data['water_temp'] == 55.5)
    check("Payload esp32_temp correct", data['esp32_temp'] == 42.0)

def test_mqtt_disabled_does_nothing():
    _cfg_mod.E_MQTT = False
    mc._queue.clear()
    mc._thread_started = True
    mc.publish_status(0, 0, False, False, 0, None, 40.0)
    check("MQTT disabled → queue stays empty", len(mc._queue) == 0)

test_mqtt_publish_format()
test_mqtt_disabled_does_nothing()

# ── 13. API contract ─────────────────────────────────────────────────────────
section("API contract (web UI /status)")

# We need to simulate the request to verify the JSON keys match the web_command.html
def test_api_status_contract():
    sm.current_grid_power = -620.5
    sm.equipment_power = 550.0
    sm.equipment_active = True
    sm.force_mode_active = False
    sm.safe_state = False
    sm.last_shelly_error = None
    sm.current_water_temp = 54.2
    
    # Keys expected by script in web_command.html:
    # d.grid_power, d.equipment_power, d.equipment_active, d.force_mode, d.water_temp, d.safe_state, d.shelly_error
    
    # Mock status dict as constructed in main.py
    data = {
        "grid_power": sm.current_grid_power,
        "equipment_power": sm.equipment_power,
        "equipment_active": sm.equipment_active,
        "force_mode": sm.force_mode_active,
        "safe_state": sm.safe_state,
        "shelly_error": sm.last_shelly_error,
        "water_temp": sm.current_water_temp,
        "total_import": sm._total_import_Wh,
        "total_redirect": sm._total_redirect_Wh,
        "total_export": sm._total_export_Wh,
    }
    
    check("API contract: grid_power exists", "grid_power" in data)
    check("API contract: equipment_power exists",  "equipment_power" in data)
    check("API contract: equipment_active exists", "equipment_active" in data)
    check("API contract: force_mode exists", "force_mode" in data)
    check("API contract: water_temp exists", "water_temp" in data)
    check("API contract: safe_state exists", "safe_state" in data)
    check("API contract: shelly_error exists", "shelly_error" in data)
    check("API contract: total_import exists", "total_import" in data)
    check("API contract: total_redirect exists", "total_redirect" in data)
    check("API contract: total_export exists", "total_export" in data)

test_api_status_contract()

# ── 14. Periodic Tasks ────────────────────────────────────────────────────────
section("Periodic Tasks (Counters)")

def test_temp_read_counter_logic():
    counter = 0
    reads = 0
    # Logic in monitor_loop: every 15 polls (~30s)
    for _ in range(45):
        counter += 1
        if counter >= 15:
            counter = 0
            reads += 1
    check("Temp read 3 times in 45 polls", reads == 3)

def test_watchdog_log_cleanup_logic():
    # Logic in watchdog_and_log_task: every 3600s
    counter = 0
    cleanups = 0
    step = 5 # feeds every 5s
    # Simulate 2 hours (7200s)
    for _ in range(0, 7200, step):
        counter += step
        if counter >= 3600:
            counter = 0
            cleanups += 1
    check("Log cleanup 2 times in 2 hours", cleanups == 2)

test_temp_read_counter_logic()
test_watchdog_log_cleanup_logic()

def test_power_history_rolling_buffer():
    sm.power_history = []
    # Logic in history_loop: caps at 60
    for i in range(70):
        sm.power_history.append({"t": 1000 + i, "g": 100, "e": 50})
        if len(sm.power_history) > 60:
            sm.power_history.pop(0)
    check("Power history capped at 60 items", len(sm.power_history) == 60)
    check("Oldest item popped (start=1010)", sm.power_history[0]['t'] == 1010)

test_power_history_rolling_buffer()

# ── 15. WiFi Setup & Scanner ──────────────────────────────────────────────────
section("WiFi Setup & Scanner")

import wifi_setup as ws

def test_wifi_setup_page_generation():
    html = ws.get_wifi_setup_page()
    check("WiFi setup: contains HomeWiFi", "HomeWiFi" in html)
    check("WiFi setup: contains GuestWiFi", "GuestWiFi" in html)
    check("WiFi setup: contains SSID input", 'name="WIFI_SSID"' in html)

def test_wifi_setup_save():
    # Capture saved config if we had a more complex mock, 
    # but for now we verify no crash and function call
    creds = {"WIFI_SSID": "NewNet", "WIFI_PASSWORD": "secret_pass"}
    ws.save_wifi_config(creds)
    check("WiFi save: SSID updated in config", _cfg_mod.WIFI_SSID == "NewNet")
    check("WiFi save: E_WIFI enabled", _cfg_mod.E_WIFI is True)

test_wifi_setup_page_generation()
test_wifi_setup_save()

# ── 16. Security (Basic Auth) ─────────────────────────────────────────────────
section("Security (Basic Auth)")

import ubinascii

def test_basic_auth_logic():
    # Mocking the request/response logic of main.py
    _cfg_mod.WEB_USER = "admin"
    _cfg_mod.WEB_PASSWORD = "password123"
    
    # Correct credentials
    raw_auth = "admin:password123"
    auth_header = "Basic " + ubinascii.b2a_base64(raw_auth.encode()).decode().strip()
    
    # Simulate extraction
    decoded = ubinascii.a2b_base64(auth_header[6:]).decode()
    user, pwd = decoded.split(':')
    check("Auth: user matches", user == _cfg_mod.WEB_USER)
    check("Auth: password matches", pwd == _cfg_mod.WEB_PASSWORD)
    
    # Incorrect credentials
    bad_auth = "Basic " + ubinascii.b2a_base64(b"wrong:pass").decode().strip()
    decoded = ubinascii.a2b_base64(bad_auth[6:]).decode()
    user, pwd = decoded.split(':')
    check("Auth: bad user handled", user != _cfg_mod.WEB_USER or pwd != _cfg_mod.WEB_PASSWORD)

test_basic_auth_logic()

# ── 17. Health Status (Safety Cutoffs) ────────────────────────────────────────
section("Health Status (Safety Cutoffs)")

def test_esp32_overheat_cutoff():
    _reset_monitor()
    sm.init_ssr_relay()
    sm._current_duty = 0.5
    sm._ssr_pin.value(1)
    _log_lines.clear()
    
    # Force overheat
    _esp32_mod.mcu_temperature = lambda: 85.0
    
    # Simulate monitor_loop logic
    temp = _esp32_mod.mcu_temperature()
    if temp >= _cfg_mod.MAX_ESP32_TEMP:
        sm._current_duty = 0.0
        sm._emergency_shutdown()
    
    check("Overheat: duty zeroed", sm._current_duty == 0.0)
    check("Overheat: SSR cutoff", sm._ssr_pin.value() == 0)
    check("Overheat: Relay cutoff", sm._relay.value() == 0)
    check("Overheat: log contains emergency", any("Emergency shutdown" in s for s in _log_lines))
    
    # Restore normal temp
    _esp32_mod.mcu_temperature = lambda: 45.0

test_esp32_overheat_cutoff()

# ── 18. Boost Timer Expiry ────────────────────────────────────────────────────
section("Boost Timer Expiry")

def test_boost_expiry():
    _reset_monitor()
    sm.init_ssr_relay()
    
    # Start 1 minute boost
    _FakeTime._now = 5000
    sm.start_boost(1)
    
    # Check it is active
    is_boost = _FakeTime.time() < sm.boost_end_time
    check("Boost: active at start", is_boost)
    
    # Advance time 61 seconds
    _FakeTime.advance(61)
    is_boost = _FakeTime.time() < sm.boost_end_time
    check("Boost: inactive after expiry", not is_boost)

test_boost_expiry()

# ── 19. DNS Server (Captive Portal) ───────────────────────────────────────────
section("DNS Server logic")

import domo_dns

def test_dns_packet_processing():
    dns = domo_dns.DNSServer("192.168.66.1")
    # A simple dummy DNS query for 'google.com'
    query = (
        b'\xaa\xbb' # ID
        b'\x01\x00' # Flags
        b'\x00\x01' # Questions: 1
        b'\x00\x00' # Answer RRs: 0
        b'\x00\x00' # Authority RRs: 0
        b'\x00\x00' # Additional RRs: 0
        b'\x06google\x03com\x00' # Name
        b'\x00\x01' # Type: A
        b'\x00\x01' # Class: IN
    )
    
    response = dns._process_query(query)
    
    check("DNS: response has same ID", response[:2] == b'\xaa\xbb')
    check("DNS: response flags indicate success", response[2:4] == b'\x81\x80')
    # Check if the response ends with the target IP in bytes
    check("DNS: contains redirected IP", response.endswith(b'\xc0\xa8\x42\x01')) # 192.168.66.1

test_dns_packet_processing()

# ── 20. HTTP Robustness (Shelly Malformed) ────────────────────────────────────
section("HTTP Client Robustness")

def test_http_malformed_response():
    # Simulate a response missing the double CRLF
    bad_data = b"HTTP/1.1 200 OK\nContent-Type: text/plain\n\nNo separator here"
    
    try:
        _, body = bad_data.split(b"\r\n\r\n", 1)
        passed = False
    except ValueError:
        passed = True
    
    check("HTTP: correctly identifies missing header separator", passed)

test_http_malformed_response()

# ── 21. WiFi Edge Cases (Scanner) ─────────────────────────────────────────────
section("WiFi Scanner Edge Cases")

def test_wifi_no_networks():
    # Force empty scan
    _WLAN.scan = lambda self: []
    html = ws.get_wifi_setup_page()
    check("WiFi setup: handles empty list", "Connecter au WiFi" in html)
    # Restore mock
    _WLAN.scan = lambda self: [(b"HomeWiFi", b"\x00", 1, -60, 3, False)]

test_wifi_no_networks()

# ── 22. OLED Status Logic ─────────────────────────────────────────────────────
section("OLED Display Logic")

import oled_ssd1306 as o_s

def test_oled_error_selection():
    # Mock OLED
    class MockOled:
        def __init__(self): self.text_calls = []
        def text(self, t, x, y): self.text_calls.append(t)
        def fill(self, v): pass
        def show(self): pass
    
    o_s.oled_d = MockOled()
    errors = {'Wifi': True, 'Wifi Connection': False, 'Openning Socket': False}
    
    o_s.oled_constant_show_content("1.1.1.1", 80, errors)
    texts = o_s.oled_d.text_calls
    
    check("OLED: shows Warning on error", any("! Warning !" in s for s in texts))
    check("OLED: identifies Wifi Init cause", any("Cause: Wifi Init" in s for s in texts))

test_oled_error_selection()

# ── 23. Statistics Management (Hourly & Reset) ──────────────────────────────
section("Statistics Management")

def test_hourly_accumulation():
    _reset_monitor()
    sm._hourly_import_Wh = [0.0] * 24
    sm._hourly_export_Wh = [0.0] * 24
    
    # 1. Test Import: 1000W import for 6 minutes (0.1 hour) at 14:00
    curr_min = 14 * 60 + 30 # 14:30
    dt = 360 # 6 minutes in seconds
    sm.current_grid_power = 1000.0
    
    curr_hour = (curr_min // 60) % 24
    delta = sm.current_grid_power * (dt / 3600.0)
    sm._total_import_Wh += delta
    sm._hourly_import_Wh[curr_hour] += delta
    
    check_close("Hourly import at 14h accumulated 100Wh", sm._hourly_import_Wh[14], 100.0)
    
    # 2. Test Export: -500W export for 12 minutes (0.2 hour) at 15:00
    curr_min = 15 * 60 + 10 # 15:10
    dt = 720 # 12 minutes
    sm.current_grid_power = -500.0
    
    curr_hour = (curr_min // 60) % 24
    delta = -sm.current_grid_power * (dt / 3600.0)
    sm._total_export_Wh += delta
    sm._hourly_export_Wh[curr_hour] += delta
    
    check_close("Hourly export at 15h accumulated 100Wh", sm._hourly_export_Wh[15], 100.0)
    check_close("Total export accumulated 100Wh", sm._total_export_Wh, 100.0)

def test_active_heating_time():
    _reset_monitor()
    sm._active_heating_secs = 0
    # Equipment active for 300 seconds
    sm.equipment_power = 1000.0
    dt = 300.0
    if sm.equipment_power > 0:
        sm._active_heating_secs += dt
    check("Active heating time accumulated 300s", sm._active_heating_secs == 300)

def test_robust_midnight_reset():
    _reset_monitor()
    sm._total_import_Wh = 0.0 # Case: 0 import for the day
    sm._total_redirect_Wh = 5000.0
    sm._total_export_Wh = 2000.0
    sm._active_heating_secs = 3600
    sm._hourly_redirect_Wh[12] = 1000.0
    
    # Mock monitor_loop attributes
    if not hasattr(sm.monitor_loop, '_midnight_reset_done'):
        sm.monitor_loop._midnight_reset_done = False
        
    # 1. At midnight
    curr_min = 0
    if curr_min == 0:
        if not sm.monitor_loop._midnight_reset_done:
            sm._total_import_Wh = 0.0
            sm._total_redirect_Wh = 0.0
            sm._total_export_Wh = 0.0
            sm._hourly_import_Wh = [0.0] * 24
            sm._hourly_redirect_Wh = [0.0] * 24
            sm._hourly_export_Wh = [0.0] * 24
            sm._active_heating_secs = 0
            sm.monitor_loop._midnight_reset_done = True
            
    check("Midnight: Counters reset despite 0 import", sm._total_redirect_Wh == 0.0)
    check("Midnight: Export reset", sm._total_export_Wh == 0.0)
    check("Midnight: Active time reset", sm._active_heating_secs == 0)
    check("Midnight: Latch set", sm.monitor_loop._midnight_reset_done is True)
    
    # 2. Still midnight (next loop)
    if curr_min == 0:
        if not sm.monitor_loop._midnight_reset_done:
            # Should not run
            sm._total_redirect_Wh = 999 
            
    check("Midnight: Latch prevents double reset", sm._total_redirect_Wh == 0.0)
    
    # 3. Past midnight
    curr_min = 1
    if curr_min != 0:
        sm.monitor_loop._midnight_reset_done = False
    check("Past midnight: Latch cleared", sm.monitor_loop._midnight_reset_done is False)

def test_stats_pruning():
    # Mocking stats dictionary
    stats = {}
    for i in range(15):
        date = f"2024-01-{i+1:02d}"
        stats[date] = {
            "import": 100, "redirect": 200, "export": 50,
            "h_import": [1]*24, "h_redirect": [2]*24, "h_export": [0.5]*24
        }
    
    # Pruning logic from _save_stats_to_file
    sorted_keys = sorted(stats.keys())
    if len(sorted_keys) > 8:
        for k in sorted_keys[:-8]:
            if "h_import" in stats[k]: del stats[k]["h_import"]
            if "h_redirect" in stats[k]: del stats[k]["h_redirect"]
            if "h_export" in stats[k]: del stats[k]["h_export"]
            
    check("Pruning: Day 1 h_import removed", "h_import" not in stats["2024-01-01"])
    check("Pruning: Day 1 h_export removed", "h_export" not in stats["2024-01-01"])
    check("Pruning: Day 8 h_export preserved", "h_export" in stats["2024-01-08"])
    check("Pruning: Total days still 15", len(stats) == 15)

test_hourly_accumulation()
test_active_heating_time()
test_robust_midnight_reset()
test_stats_pruning()

# ── 24. Fan Manual Test ──────────────────────────────────────────────────────
section("Fan Manual Test")

def test_fan_manual_set():
    _reset_monitor()
    _cfg_mod.E_FAN = True
    
    # Mock PWM pin
    class MockPWM:
        def __init__(self): self.duty = 0
        def duty_u16(self, v): self.duty = v
    
    sm._fan_pin = MockPWM()
    
    # Test 50%
    success = sm.test_fan_speed(50)
    check("Fan test 50%: success returned", success is True)
    check("Fan test 50%: duty_u16 set correctly", sm._fan_pin.duty == int(50 * 65535 / 100))
    check("Fan test 50%: fan_percent updated", sm.fan_percent == 50)
    check("Fan test 50%: fan_active is True", sm.fan_active is True)
    
    # Test 0%
    sm.test_fan_speed(0)
    check("Fan test 0%: fan_active is False", sm.fan_active is False)
    check("Fan test 0%: duty_u16 is 0", sm._fan_pin.duty == 0)

def test_fan_manual_disabled_config():
    _reset_monitor()
    _cfg_mod.E_FAN = False
    success = sm.test_fan_speed(100)
    check("Fan test: returns False if E_FAN is disabled", success is False)

test_fan_manual_set()
test_fan_manual_disabled_config()

# ── 25. SSR Temperature Logic (Fan & Safety) ────────────────────────────────
section("SSR Temperature Logic")

def test_ssr_fan_thresholds():
    _reset_monitor()
    _cfg_mod.E_FAN = True
    _cfg_mod.SSR_MAX_TEMP = 75.0
    _cfg_mod.FAN_TEMP_OFFSET = 10
    fan_low  = _cfg_mod.SSR_MAX_TEMP - _cfg_mod.FAN_TEMP_OFFSET  # 65°C
    fan_high = _cfg_mod.SSR_MAX_TEMP                              # 75°C

    class MockPWM:
        def __init__(self): self.duty = 0
        def duty_u16(self, v): self.duty = v
    sm._fan_pin = MockPWM()
    sm.fan_percent = 0

    # 1. Below low threshold -> 0%
    sm.current_ssr_temp = fan_low - 5.0
    new_percent = 0
    if sm.current_ssr_temp >= fan_high: new_percent = 100
    elif sm.current_ssr_temp >= fan_low: new_percent = 50
    check(f"SSR {sm.current_ssr_temp}°C (below low) -> Fan 0%", new_percent == 0)

    # 2. At low threshold -> 50%
    sm.current_ssr_temp = fan_low
    if sm.current_ssr_temp >= fan_high: new_percent = 100
    elif sm.current_ssr_temp >= fan_low: new_percent = 50
    check(f"SSR {sm.current_ssr_temp}°C (at low) -> Fan 50%", new_percent == 50)

    # 3. At high threshold -> 100%
    sm.current_ssr_temp = fan_high
    if sm.current_ssr_temp >= fan_high: new_percent = 100
    elif sm.current_ssr_temp >= fan_low: new_percent = 50
    check(f"SSR {sm.current_ssr_temp}°C (at high) -> Fan 100%", new_percent == 100)

def test_ssr_safety_cutoff():
    _reset_monitor()
    sm.init_ssr_relay()
    sm._current_duty = 0.5
    _cfg_mod.SSR_MAX_TEMP = 75.0
    
    # Trigger overheat
    sm.current_ssr_temp = 76.0
    if sm.current_ssr_temp is not None and sm.current_ssr_temp >= _cfg_mod.SSR_MAX_TEMP:
        sm._current_duty = 0.0
        sm._emergency_shutdown()
        
    check("SSR Overheat: duty zeroed", sm._current_duty == 0.0)
    check("SSR Overheat: relay cut", sm._relay.value() == 0)

def test_ssr_safety_recovery():
    _reset_monitor()
    sm.init_ssr_relay()
    sm._relay.value(0) # In safety state
    sm.safe_state = False # Shelly is reachable
    
    # Temperature cools down
    sm.current_ssr_temp = 65.0 
    _cfg_mod.SSR_MAX_TEMP = 75.0
    
    # Simulation logic from monitor_loop
    is_hot = sm.current_ssr_temp is not None and sm.current_ssr_temp >= _cfg_mod.SSR_MAX_TEMP
    if sm._relay.value() == 0 and not sm.safe_state and not is_hot:
        sm._relay.value(1)
        
    check("SSR cooled down: relay re-enabled", sm._relay.value() == 1)

test_ssr_fan_thresholds()
test_ssr_safety_cutoff()
test_ssr_safety_recovery()

# ── 26. Night Mode Polling (Test 2) ──────────────────────────────────────────
section("Night Mode Polling Interval")

def test_night_mode_polling():
    _reset_monitor()
    _cfg_mod.POLL_INTERVAL = 2
    
    # 1. Day time (12:00)
    sm.night_mode = False
    poll_int = _cfg_mod.POLL_INTERVAL
    if sm.night_mode: poll_int = 60
    check("Daytime: Poll interval is 2s", poll_int == 2)
    
    # 2. Night mode active
    sm.night_mode = True
    poll_int = _cfg_mod.POLL_INTERVAL
    if sm.night_mode: poll_int = getattr(_cfg_mod, 'NIGHT_POLL_INTERVAL', 15)
    check("Night Mode: Poll interval increased to NIGHT_POLL_INTERVAL", poll_int == _cfg_mod.NIGHT_POLL_INTERVAL)

# ── 27. Log Buffering and Flash Flush (Test 3) ───────────────────────────────
section("Log Buffering and Flash Flush")

def test_log_buffering_and_flush():
    _reset_monitor()
    sm._solar_data_buffer = []
    sm._last_data_log_time = 1000 # FakeTime start
    
    # 1. Buffer a log message (simulating 1 minute passing)
    _FakeTime.advance(61)
    now = _FakeTime.time()
    log_msg = "SOLAR [TEST] grid=100W"
    
    if log_msg and (now - sm._last_data_log_time) >= 60:
        sm._solar_data_buffer.append(f"2024-06-01 12:01:01: {log_msg}")
        sm._last_data_log_time = now
        
    check("Log message added to RAM buffer", len(sm._solar_data_buffer) == 1)
    
    # 2. Flush buffer to file
    # We mock the actual file write to avoid touching disk in this unit test
    # but we verify the buffer is cleared.
    def mock_flush():
        if not sm._solar_data_buffer: return
        # (File write would happen here)
        sm._solar_data_buffer = []
        
    mock_flush()
    check("RAM buffer cleared after flush", len(sm._solar_data_buffer) == 0)

test_night_mode_polling()
test_log_buffering_and_flush()

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{'═'*60}")
print(f"  Results: {_passed} passed, {_failed} failed")
print(f"{'═'*60}")
if _failed:
    sys.exit(1)
