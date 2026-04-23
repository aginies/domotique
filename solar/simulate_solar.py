#!/usr/bin/env python3
# solar/simulate_solar.py
#
# Closed-loop PV Router Simulator for PC.
# Uses exact logic from solar_monitor.py to test tuning.

import sys
import types
import os
import time

# ── Mocking MicroPython Environment ──────────────────────────────────────────
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "common")))

class _Pin:
    OUT = 1
    def __init__(self, *a, **k): self._v = 0
    def value(self, v=None):
        if v is not None: self._v = v
        return self._v

class _PWM:
    def __init__(self, *a, **k): self.duty = 0
    def duty_u16(self, v): self.duty = v
    def freq(self, v): pass

_machine = types.ModuleType("machine")
_machine.Pin = _Pin
_machine.PWM = _PWM
_machine.RTC = lambda: type('RTC', (), {'datetime': lambda s: (2024, 6, 1, 5, 12, 0, 0, 0)})()
sys.modules["machine"] = _machine

_esp32 = types.ModuleType("esp32")
_esp32.mcu_temperature = lambda: 40.0
sys.modules["esp32"] = _esp32

# Mock utime
class _Utime:
    def __init__(self): self.now = 1000
    def time(self): return int(self.now)
    def ticks_ms(self): return int(self.now * 1000)
    def ticks_diff(self, a, b): return a - b
    def localtime(self, t=None): return time.localtime(t or self.now)
    def sleep(self, s): self.now += s
    def sleep_ms(self, ms): self.now += ms/1000.0
    def advance(self, s): self.now += s

ut = _Utime()
_utime_mod = types.ModuleType("utime")
_utime_mod.time = ut.time
_utime_mod.ticks_ms = ut.ticks_ms
_utime_mod.ticks_diff = ut.ticks_diff
_utime_mod.localtime = ut.localtime
_utime_mod.sleep = lambda s: None # Fast sim
sys.modules["utime"] = _utime_mod

# Mock asyncio
_asyncio = types.ModuleType("asyncio")
_asyncio.sleep = lambda s: None
_asyncio.sleep_ms = lambda ms: None
sys.modules["asyncio"] = _asyncio

# Mock ujson
import json
_ujson = types.ModuleType("ujson")
_ujson.dumps = json.dumps
_ujson.loads = json.loads
sys.modules["ujson"] = _ujson

# Mock other minor ones
sys.modules["mqtt_client"] = types.ModuleType("mqtt_client")
sys.modules["mqtt_client"].publish_status = lambda *a, **k: None
sys.modules["mqtt_client"].ensure_started = lambda: None
sys.modules["mqtt_client"].latest_mqtt_grid_power = [None]

_domo = types.ModuleType("domo_utils")
_domo.print_and_store_log = lambda m: None
_domo.show_rtc_time = lambda: (12, 0, 0)
_domo.show_rtc_date = lambda: "2024-06-01"
_domo.get_paris_time_minutes = lambda: 720
_domo.file_exists = lambda p: False
sys.modules["domo_utils"] = _domo

# ── Load Config & Monitor ─────────────────────────────────────────────────────
import config_var as c_v
import solar_monitor as sm

# ── Simulation Engine ─────────────────────────────────────────────────────────

def run_simulation(duration_mins=10, silent=False):
    if not silent:
        print(f"\n{'═'*80}")
        print(f"  SOLAR DIVERTER SIMULATION (PC)")
        print(f"  Kp={c_v.PID_KP}, Ki={c_v.PID_KI}, Deadband={c_v.DEADBAND_W}W, Nudge={c_v.RAMP_DOWN_NUDGE}")
        print(f"{'═'*80}")
        print(f"{'Time':>8} | {'Solar':>6} | {'Load':>6} | {'Heater':>6} | {'Grid':>7} | {'Duty':>5} | {'Tag':>8}")
        print(f"{'─'*80}")

    # Physical State
    solar_prod = 2300.0
    base_load = 300.0
    extra_load = 0.0
    
    # Sim metrics
    total_injected_Wh = 0.0
    total_imported_Wh = 0.0
    total_redirected_Wh = 0.0

    
    # Initialize monitor
    sm._last_good_poll = ut.time()
    sm._last_pi_time = ut.ticks_ms()
    sm._pi.reset()
    sm._current_duty = 0.0
    
    # Start Loop
    steps = duration_mins * 60 // 2 # 2s steps
    for i in range(steps):
        # 1. Update Physics (Scenarios)
        if i < 50: solar_prod = 1200 # Stable
        elif i < 100: solar_prod += 20 # Ramp up
        elif i < 150: solar_prod -= 30 # Cloud
        elif i < 200: extra_load = 1500 # Oven ON
        else: extra_load = 0 # Oven OFF

        # 2. Closed Loop Grid Calculation
        heater_w = sm._current_duty * c_v.EQUIPMENT_MAX_POWER
        grid_w = base_load + extra_load + heater_w - solar_prod
        
        # 3. Feed Router Logic
        sm.current_grid_power = grid_w
        sm.equipment_power = heater_w
        
        # We manually invoke the core logic of monitor_loop to see it react
        max_p = float(c_v.EQUIPMENT_MAX_POWER)
        base_setpoint = float(c_v.EXPORT_SETPOINT)
        min_threshold = float(c_v.MIN_POWER_THRESHOLD)
        surplus = base_setpoint - grid_w
        error = surplus / max_p  # Normalized by max power, matching solar_monitor.py
        dt = 2.0
        
        status_tag = "WAIT"
        if surplus < min_threshold and sm._current_duty == 0.0:
            status_tag = "OFF"
        else:
            deadband_w = float(c_v.DEADBAND_W)
            if surplus > deadband_w:
                sm._current_duty = sm._pi.update(error, dt)
                status_tag = "PI+"
            elif surplus < -deadband_w:
                raw = sm._pi.update(error, dt)
                nudge = float(getattr(c_v, 'RAMP_DOWN_NUDGE', 0.01))
                sm._current_duty = max(0.0, min(1.0, raw + nudge)) if sm._current_duty > 0.0 else raw
                status_tag = "PI-"
            else:
                status_tag = "HOLD"
        
        # Metrics
        if grid_w < 0: total_injected_Wh += (-grid_w * (dt/3600))
        if grid_w > 0: total_imported_Wh += (grid_w * (dt/3600))
        total_redirected_Wh += (heater_w * (dt/3600))

        # Print state
        if not silent and i % 5 == 0:
            t_str = f"{i*2}s"
            print(f"{t_str:>8} | {solar_prod:6.0f}W | {base_load+extra_load:6.0f}W | {heater_w:6.0f}W | {grid_w:7.1f}W | {sm._current_duty:5.2f} | {status_tag:>8}")

        ut.advance(dt)

    efficiency = (total_redirected_Wh / (total_redirected_Wh + total_injected_Wh) * 100) if (total_redirected_Wh + total_injected_Wh) > 0 else 0

    if not silent:
        print(f"{'─'*80}")
        print(f"RESULTS for {duration_mins} mins simulation:")
        print(f"  Total Injected (Wasted): {total_injected_Wh:.2f} Wh")
        print(f"  Total Imported (Paid):   {total_imported_Wh:.2f} Wh")
        print(f"  Total Redirected:        {total_redirected_Wh:.2f} Wh")
        efficiency = (total_redirected_Wh / (total_redirected_Wh + total_injected_Wh) * 100) if (total_redirected_Wh + total_injected_Wh) > 0 else 0
        print(f"  Surplus Capture Efficiency: {efficiency:.1f}%")
        print(f"{'═'*80}\n")
    
    return efficiency, total_injected_Wh

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--kp", type=float, default=0.4)
    parser.add_argument("--ki", type=float, default=0.4)
    parser.add_argument("--deadband", type=float, default=5)
    parser.add_argument("--nudge", type=float, default=0.01)
    parser.add_argument("--mins", type=int, default=10)
    parser.add_argument("--silent", action="store_true")
    args = parser.parse_args()

    c_v.PID_KP = args.kp
    c_v.PID_KI = args.ki
    c_v.DEADBAND_W = args.deadband
    c_v.RAMP_DOWN_NUDGE = args.nudge
    
    # Corrected return handling
    results = run_simulation(args.mins, args.silent)
    if args.silent:
        eff, injected = results
        print(f"EFFICIENCY:{eff:.2f}|INJECTED:{injected:.2f}")
