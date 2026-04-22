# Solar Power Diverter (MicroPython)

A high-performance Photovoltaic (PV) Router designed for ESP32. It optimizes self-consumption by redirecting excess solar production to a resistive load (like a water heater or a radiator) instead of exporting it for free to the grid.

## Key Features

- **Multi-Source Power Monitoring**:
    - **MQTT Direct (Fastest)**: Listens to real-time pushes from a Shelly EM.
    - **JSY-MK-194 (Wired)**: Direct UART connection for ultra-low latency and high precision (dual channel).
    - **HTTP Polling (Fallback)**: Standard API requests to Shelly EM.
- **High-Speed Diversion**: Uses a **1-second physical cycle** (Burst-fire) to match the responsiveness of professional wired routers.
- **Home Assistant Integration**: Full MQTT Auto-Discovery support. Automatically creates sensors for Grid Power, Redirected Power, and Temperatures.
- **Safety First**:
    - **Intelligent Cooling**: Supports 4-pin PWM fans with 3-step automatic throttling (0% < 50°C, 50% at 50°C, 100% at 60°C) and manual speed testing.
    - Dual overheat protection (internal ESP32 temp + external SSR heatsink probe).
    - Mechanical relay protection: Keeps the circuit open when idle to reduce SSR wear and provide a hardware safety cutoff.
    - Watchdog timer: Automatically cuts power if the grid meter (Shelly/JSY) becomes unreachable.
- **Rich Web Interface**:
    - Real-time power dashboard with color-coded interactive graphs (Chart.js).
    - Dynamic logs with auto-scrolling and keyword colorization.
    - **Manual Boost** mode (1h, 2h, or 3h) and daily scheduled windows.
    - **Advanced History & Statistics**: 365-day rolling energy tracking (Wh/kWh) for grid import and solar savings. Dedicated dashboard with Day/Month/Year views and interactive Gausse/Bar charts.
    - **Flash Protection System**: High-efficiency RAM buffering for all logging operations (`log.txt` and `solar_data.txt`). Reduces write frequency to flash memory by over 90% to maximize hardware lifespan.
    - **Eco Night Mode**: Smart time-aware logic that reduces polling frequency during non-productive hours (configurable, e.g., 15s interval) to minimize network load and CPU overhead.
    - Secure configuration page for all parameters (PID gains, thresholds, pins).

## Hardware Requirements

- **ESP32-S3** (or standard ESP32)
- **SSR (Solid State Relay)**: Zero-cross type recommended.
- **Mechanical Relay**: For safety cutoff.
- **Power Meter**: Shelly EM (Wi-Fi) or JSY-MK-194 (Wired UART).
- **Cooling**: Heatsink for the SSR is mandatory.

## Installation

1.  Configure your Wi-Fi and MQTT settings in `config_var.py`.
2.  Install requirements: `import mip; mip.install('umqtt.simple')`.
3.  Deploy using the provided Makefile: `make upload`.
4.  Access the web UI at `http://<device_ip>/`.

## Monitoring Options

| Source | Latency | Connection | Notes |
| :--- | :--- | :--- | :--- |
| **MQTT** | ~200ms | Wi-Fi | Requires MQTT Broker (Mosquitto). Fast and wireless. |
| **JSY-MK-194** | ~100ms | Wired | Best performance. Dual-channel (Grid + Equipment). |
| **HTTP** | ~2000ms | Wi-Fi | No extra server needed. Good for basic setups. |

For detailed wiring diagrams and safety instructions, see [WIRING.md](WIRING.md).
