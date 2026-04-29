# Lilygo Solar Remote Monitor

A dedicated remote dashboard for the Solar Power Diverter, designed specifically for the **LILYGO T-Display (ESP32 1.14" LCD)**.

## Features

- **Multi-Screen Interface**:
    - **Dashboard**: High-visibility "Huge Text" mode showing real-time ENEDIS and Redirected power.
    - **Power Graph**: 5-minute scrolling history of grid import/export and redirection.
    - **Temperature Graph**: Visual history of ESP32 and SSR temperatures.
- **Interactive Controls**:
    - **Top Button**: Cycle through the three screen modes.
    - **Bottom Button**: Redundant screen cycle (or custom action).
- **Intelligent Visuals**:
    - NTP-synchronized real-time clock with configurable timezone.
    - Dynamic Y-axis scaling for maximum graph detail.
    - Color-coded power values (Green = Surplus, Red = Consumption).
- **Lightweight Core**: Standalone implementation with zero external dependencies, optimized for low RAM usage.

## Configuration

`config_var.py` is in `.gitignore` to prevent credentials from being committed. The `.bck` file contains sample data for reference.

1.  Copy `config_var.py.bck` to `config_var.py` 
2.  Update your Wi-Fi credentials (see `WIFI_SSID`, `WIFI_PASSWORD`) and MQTT settings (see `MQTT_USER`, `MQTT_PASSWORD`)
3.  Set `TZ_OFFSET` to 3600 for CET or 7200 for CEST
2.  Deploy using the Makefile: `make upload`.
3.  The board will automatically sync time via NTP, subscribe to your Solar Diverter's MQTT feed and display the data.

## Hardware Support
Designed for the **LILYGO T-Display (V1.1)** with the 135x240 ST7789 IPS screen. Uses GPIO 35 and 0 for navigation.
- **Top Button (GPIO 35)**: Cycle through the three screen modes.
- **Bottom Button (GPIO 0)**: Flip screen 180 degrees.
