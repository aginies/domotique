# antoine@ginies.org
# GPL3

# Main name — no spaces, max 13 chars (used for AP SSID and OLED)
NAME = "Solaire"

# on ESP32-S3 you must sold the RGB pin on the board!
I_LED_PIN = 48

# ESP32-S3 CPU freq
CPU_FREQ = 240

# CHOOSE AP OR EXISTING WIFI
# E_WIFI = True  -> connect to existing WiFi
# E_WIFI = False -> create a WiFi Access Point
E_WIFI = True
WIFI_SSID = ""
WIFI_PASSWORD = ""

# WIFI STATIC IP (optional, set all 3 if you want static)
# WIFI_STATIC_IP = "10.0.10.20"
# WIFI_SUBNET = "255.255.255.0"
# WIFI_GATEWAY = "10.0.10.1"
# WIFI_DNS = "10.0.10.1"

# WIFI AP
AP_SSID = "W_Solaire"
AP_PASSWORD = "12345678"
AP_HIDDEN_SSID = False
AP_CHANNEL = 6
AP_IP = ('192.168.66.1', '255.255.255.0', '192.168.66.1', '192.168.66.1')

# OLED PIN
OLED_SCL_PIN = 7
OLED_SDA_PIN = 18

# SSR digital output pin (burst-fire control of equipment power)
SSR_PIN = 12
# Relay pin (enables/disables the circuit, protects SSR)
RELAY_PIN = 13

# Time in seconds for LED blink
time_ok = 0.1
time_err = 0.3

# Shelly EM (Gen1) — provides net grid power in watts
# Negative value = solar surplus exported to grid = available for equipment
SHELLY_EM_IP = "10.0.10.60"
E_SHELLY_MQTT = True     # If True, get grid power from MQTT (faster) instead of HTTP
SHELLY_MQTT_TOPIC = "shellies/homeassistant/emeter/0/power"
FAKE_SHELLY = False        # If True, emulates a Shelly EM locally for testing

POLL_INTERVAL = 1         # seconds between Shelly HTTP polls (fallback mode)

# Equipment configuration
EQUIPMENT_NAME = "Ballon"
EQUIPMENT_MAX_POWER = 2300 # watts — must match actual equipment wattage
# 3-region deadband
#   surplus > +DEADBAND_W  → Region 1: PI ramps equipment UP
#   surplus in ±DEADBAND_W → Region 2: HOLD current duty, integral frozen
#   surplus < -DEADBAND_W  → Region 3: PI ramps equipment DOWN (+ nudge)
DEADBAND_W = -20            # watts — half-width of the stable zone (±0 W)
RAMP_DOWN_NUDGE = 0.01     # 10% upward bias when ramping down to avoid overshooting to zero.
TRANSIENT_RESET_THRESHOLD = 400  # watts above setpoint to trigger a PI integral reset (large load switch events)


# Target grid power: 0 = zero export, negative = keep a surplus buffer on the grid
EXPORT_SETPOINT = 0        # watts

# PI controller gains (tune to your installation)
# Kp: immediate response per watt of error, normalised to EQUIPMENT_MAX_POWER
# Ki: integral correction — eliminates steady-state offset
PID_KP = 0.4
PID_KI = 0.4

# Burst-fire period: SSR switches ON for duty*BURST_PERIOD seconds, then OFF
# Matching xlyric project: 1 second
BURST_PERIOD = 0.5           # seconds

# Minimum surplus to activate equipment (avoid micro-activations)
MIN_POWER_THRESHOLD = 10   # watts — reduced to match higher responsiveness



# Minimum time equipment must stay OFF between activations (protects SSR and relay)
MIN_OFF_TIME = 1          # seconds

# Manual Boost duration
BOOST_MINUTES = 60         # minutes

# Force mode (bypass solar logic)
FORCE_EQUIPMENT = False    # If True, equipment is forced ON (respecting target temp)
E_FORCE_WINDOW = False     # If True, enables the daily force window below
FORCE_START = "22:05"      # Daily start time for force window (HH:MM)
FORCE_END = "05:55"        # Daily end time for force window (HH:MM)

# Night mode (low query rate)
NIGHT_START = "22:00"      # Start of low query period
NIGHT_END = "05:50"        # End of low query period
NIGHT_POLL_INTERVAL = 15   # seconds between polls in night mode


# Hardware health: maximum ESP32 internal temperature before safety cutoff
MAX_ESP32_TEMP = 65.0      # °C

# Web security (optional) — if WEB_USER is set, restricted pages will require Basic Auth
WEB_USER = ""
WEB_PASSWORD = ""

# DS18B20 temperature sensors (optional)
E_DS18B20 = False          # Set to True if you have a sensor in the water tank
DS18B20_PIN = 14           # one-wire data pin
EQUIPMENT_MAX_TEMP = 65.0  # °C — safety cutoff, equipment forced off above this
EQUIPMENT_TARGET_TEMP = 62.0 # °C — force mode stops when this temp is reached

# SSR Temperature Monitoring (optional)
E_SSR_TEMP = True          # Set to True to monitor SSR heatsink. 
                           # If only 1 sensor is found and E_DS18B20 is False, 
                           # it will be used for SSR temperature.
SSR_MAX_TEMP = 65.0        # °C — safety cutoff if SSR heatsink gets too hot

# Fan configuration
E_FAN = True               # Enable fan control
FAN_PIN = 5                # GPIO for fan control
FAN_TEMP_OFFSET = 10       # Activate fan at SSR_MAX_TEMP - offset

# Shelly watchdog: if no valid reading for this long, enter safe-state (equipment off).
# MQTT mode: set this to at least 3× the Shelly MQTT "Update period" (Shelly web UI →
# Settings → MQTT → Update period).  With Shelly at 1 s → 10 s is safe.  With the
# factory default of 30 s you will get a spurious safe-state every cycle — fix the
# Shelly config, not this value.
SHELLY_TIMEOUT = 10        # seconds — assumes Shelly MQTT period ≤ 3 s

# JSY-MK-194 (Wired UART 2-channel power meter)
E_JSY = False              # If True, use JSY via UART instead of Shelly (faster)
JSY_UART_ID = 2
JSY_TX = 17
JSY_RX = 16

# SSR control mode:
# "burst"          → burst-fire classique, pas de Zx requis
# "cycle_stealing" → demi-cycles complets via Zx, SSR zero-crossing OK, ~23W résolution
# "phase_angle"    → contrôle de phase via Zx, SSR random-fire requis, ~1W résolution
CONTROL_MODE = "burst"

# GPIO connecté à la pin Zx du JSY-MK-194G (seulement si CONTROL_MODE = "phase_angle")
ZX_PIN = 15

# Demi-période calibrée en µs pour 50 Hz. 9900 compense la latence de détection Renergy.
HALF_PERIOD_US = 9900

# Fenêtre de busy-poll finale en µs — limite le CPU Core 1 à ~10% (1ms / 10ms)
ZX_BUSYPOLL_US = 1000

# Timeout ZX : si aucun pulse pendant ce délai (ms), gate OFF (safe state)
ZX_TIMEOUT_MS = 500

# Logs de diagnostic phase-angle : 1 log toutes les 100 demi-périodes (~1s à 50Hz)
DEBUG_PHASE = False


# MQTT (optional)
E_MQTT = True
MQTT_IP = "10.0.10.101"
MQTT_PORT = 1883
MQTT_USER = ""
MQTT_PASSWORD = ""
MQTT_NAME = "GuiboSolar"
MQTT_RETAIN = False
MQTT_KEEPALIVE = 60
MQTT_DISCOVERY_PREFIX = "homeassistant"
MQTT_REPORT_INTERVAL = 10   # seconds between MQTT status reports
