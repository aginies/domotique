# antoine@ginies.org
# GPL3
#
# Realistic Shelly EM emulator — closed-loop simulation.
#
# Grid = base_load + extra_load + heater_watts - solar_production  (+ noise)
#
# heater_watts is read directly from solar_monitor._current_duty so the
# controller's own adjustments feed back into the meter reading, exactly
# as a real installation behaves.

import asyncio
import ujson
import utime
import urandom
import domo_utils as d_u
import config_var as c_v

# Import lazily to avoid a circular-import risk at module load time.
# solar_monitor does NOT import fake_shelly, so this is safe once the
# event loop is running.
_sm = None

def _get_heater_watts():
    """Return the current heater power from the PI controller."""
    global _sm
    if _sm is None:
        try:
            import solar_monitor
            _sm = solar_monitor
        except Exception:
            return 0.0
    try:
        duty = float(_sm._current_duty)
        max_p = float(getattr(c_v, 'EQUIPMENT_MAX_POWER', 2000))
        return duty * max_p
    except Exception:
        return 0.0


# ── Physical constants ──────────────────────────────────────────────────────────
MAX_SOLAR       = 2825.0   # W  — panel peak
BASE_LOAD_MIN   = 250.0    # W  — minimum house consumption (lights, standby …)
BASE_LOAD_MAX   = 450.0    # W  — maximum background load
NOISE_AMPLITUDE = 15.0     # W  — meter measurement noise

# ── Scenario definitions ────────────────────────────────────────────────────────
# (name, solar_target_W, duration_s_min, duration_s_max)
# Durations are short for fast testing — divide originals by ~10.
_SCENARIOS = [
    ("STABLE",      1600.0,  24,  40),   # Average sun, controller stabilises
    ("CLEAR",       2600.0,  24,  35),   # Full sun, big surplus
    ("CLOUD",        600.0,  6,  9),   # Heavy cloud
    ("LIGHT_CLOUD", 1100.0,  2,  5),   # Partial cloud
    ("STABLE",      2000.0,  20,  30),   # Good afternoon sun
    ("DEEP_CLOUD",   300.0,  4,  7),   # Storm / heavy overcast
]

# Microwave: ~1-in-3 chance on each transition, 2-3 s burst
_MW_CHANCE    = 3
_MW_POWER     = 900    # W
_MW_MIN_SECS  = 2
_MW_MAX_SECS  = 3

# Solar ramp rate (W per second) — fast for short scenarios
_SOLAR_SLEW   = 200.0

# ── Shared state ────────────────────────────────────────────────────────────────
_solar_production = 1500.0
_solar_target     = 1600.0
_base_load        = 350.0
_extra_load       = 0.0
_grid_power       = -1200.0

_scenario_idx     = 0
_scenario_timer   = 0
_microwave_timer  = 0
_microwave_active = False


def _rand_int(lo, hi):
    span = hi - lo + 1
    bits = 1
    while (1 << bits) < span:
        bits += 1
    while True:
        v = urandom.getrandbits(bits)
        if v < span:
            return lo + v


def _noise():
    return float(_rand_int(0, int(NOISE_AMPLITUDE * 2))) - NOISE_AMPLITUDE


async def _simulation_loop():
    global _solar_production, _solar_target, _base_load
    global _extra_load, _grid_power
    global _scenario_idx, _scenario_timer
    global _microwave_timer, _microwave_active

    # Bootstrap first scenario
    _scenario_idx   = _rand_int(0, len(_SCENARIOS) - 1)
    name, target, mn, mx = _SCENARIOS[_scenario_idx]
    _solar_target   = target
    _scenario_timer = _rand_int(mn, mx)
    d_u.print_and_store_log(
        f"FAKE_SHELLY: scenario={name} solar_target={target:.0f}W duration={_scenario_timer}s"
    )

    while True:
        try:
            # ── Solar ramp toward target ──────────────────────────────────────
            diff = _solar_target - _solar_production
            slew = min(abs(diff), _SOLAR_SLEW)
            if diff > 0:
                _solar_production += slew
            elif diff < 0:
                _solar_production -= slew
            _solar_production = max(0.0, min(MAX_SOLAR, _solar_production))

            # ── Base load slow drift ──────────────────────────────────────────
            _base_load += float(_rand_int(0, 20) - 10) * 0.5
            _base_load = max(BASE_LOAD_MIN, min(BASE_LOAD_MAX, _base_load))

            # ── Microwave timer ───────────────────────────────────────────────
            if _microwave_active:
                _microwave_timer -= 1
                if _microwave_timer <= 0:
                    _microwave_active = False
                    _extra_load = 0.0
                    d_u.print_and_store_log("FAKE_SHELLY: microwave OFF")

            # ── Scenario countdown ────────────────────────────────────────────
            _scenario_timer -= 1
            if _scenario_timer <= 0:
                prev_idx = _scenario_idx
                for _ in range(10):
                    _scenario_idx = _rand_int(0, len(_SCENARIOS) - 1)
                    if _scenario_idx != prev_idx:
                        break

                name, target, mn, mx = _SCENARIOS[_scenario_idx]
                _solar_target   = target
                _scenario_timer = _rand_int(mn, mx)
                d_u.print_and_store_log(
                    f"FAKE_SHELLY: scenario={name} solar_target={target:.0f}W "
                    f"duration={_scenario_timer}s"
                )

                # Maybe fire microwave (only when not already on)
                if not _microwave_active and _rand_int(1, _MW_CHANCE) == 1:
                    _microwave_active = True
                    _microwave_timer  = _rand_int(_MW_MIN_SECS, _MW_MAX_SECS)
                    _extra_load       = float(_MW_POWER)
                    d_u.print_and_store_log(
                        f"FAKE_SHELLY: microwave ON for {_microwave_timer}s (+{_MW_POWER}W)"
                    )

            # ── Closed-loop grid power ────────────────────────────────────────
            # Include the heater power that the PI controller is currently
            # applying so the controller's adjustments affect what it reads.
            heater = _get_heater_watts()
            _grid_power = (
                _base_load + _extra_load + heater - _solar_production + _noise()
            )

        except Exception as e:
            d_u.print_and_store_log(f"FAKE_SHELLY sim error: {e}")

        await asyncio.sleep(1)


async def handle_request(reader, writer):
    global _grid_power
    try:
        await reader.read(128)
        data = {
            "emeters": [{
                "power":    round(_grid_power, 1),
                "reactive": 0.0,
                "voltage":  232.5,
                "is_valid": True,
                "total":    12345.6
            }]
        }
        response = (
            "HTTP/1.0 200 OK\r\n"
            "Content-Type: application/json\r\n"
            "Connection: close\r\n\r\n"
            + ujson.dumps(data)
        )
        writer.write(response.encode())
        await writer.drain()
    except Exception as e:
        d_u.print_and_store_log(f"FAKE_SHELLY handler error: {e}")
    finally:
        try:
            writer.close()
        except Exception:
            pass


async def start_fake_shelly():
    """Runs an async HTTP server emulating Shelly EM Gen1 API."""
    d_u.print_and_store_log("FAKE_SHELLY: Starting async server on port 8081")
    asyncio.create_task(_simulation_loop())
    try:
        await asyncio.start_server(handle_request, '0.0.0.0', 8081)
        d_u.print_and_store_log("FAKE_SHELLY: Server ready")
    except Exception as e:
        d_u.print_and_store_log(f"FAKE_SHELLY: Failed to start: {e}")
