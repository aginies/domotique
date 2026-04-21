# door

Control a Door

* Get info on the status of a door, **open** or **closed** using an external **LED** (optionnal)
* Control using a Wifi Access Point the door with a button on a **web server**
* Display all relevant **informations** on a 0.96" **oled screen** (optionnal)
* Use RFID to open the door (optionnal), and program new card
* **Live log** available
* **Files management**
* **Configuration** using a web interface

![image](https://raw.githubusercontent.com/aginies/domotique/refs/heads/main/images/portail_web.jpg)

# pool

Control a Pool shutter

* Get info on the status of a shutter, **open** or **closed** using external **LED** (optionnal)
* Control using a **Wifi Access Point** the curtain with **Open / Close / Emergency Stop** buttons on a **web server**
* **Quick open/close** with a configurable duration **slider** (1 sec → full open time)
* Display all relevant **informations** on a 0.96" **oled screen** (optionnal)
* **Live log** available (auto-rotated to protect flash)
* **Configuration** the timing and other parameters through a web interface
* **Files management**
* **Udpate** support an **update.bin** file

![image](https://raw.githubusercontent.com/aginies/domotique/refs/heads/main/images/pool_web.jpg)
![image](https://raw.githubusercontent.com/aginies/domotique/refs/heads/main/images/pool_config.jpg)
![image](https://raw.githubusercontent.com/aginies/domotique/refs/heads/main/images/pool_config_02.jpg)
![image](https://raw.githubusercontent.com/aginies/domotique/refs/heads/main/images/pool_log.jpg)
![image](https://raw.githubusercontent.com/aginies/domotique/refs/heads/main/images/file_management.jpg)

# solar

High-performance PV Router: Divert solar surplus power to a resistive load (e.g. hot water tank).

* **Multiple Data Sources**:
    * **MQTT Direct (Fastest)**: Instant push from Shelly EM.
    * **JSY-MK-194 (Wired)**: Direct UART connection for ultra-low latency.
    * **HTTP Polling**: Standard Shelly API requests.
* **1-second physical cycle** (Burst-fire) for maximum responsiveness.
* **Home Assistant**: Full Auto-Discovery support (Power, Temps, Status).
* **Safety**: Dual temperature cutoffs (ESP32 + SSR), relay hardware protection, and watchdog safety state.
* **Advanced Web UI**: Interactive Chart.js graphs, colorized live logs, manual **Boost** (1-3h), and full secure configuration.
* **Update** support via an **update.bin** file.

# lilygo_solar

Dedicated remote color dashboard for the Solar Diverter.

* Hardware: Designed for **LILYGO T-Display (1.14" LCD)**.
* **Multi-Screen Cycle**: Dashboard (Huge text) -> Power Graph (5m) -> Temperature Graph (5m).
* **Interactive**: Use hardware buttons to toggle between visual modes.
* **Intelligent Visuals**: Dynamic Y-axis scaling and color-coded status.
* **Lightweight**: Optimized standalone core for limited memory.

# parking_detection

Get a flash light which indicate the distance between the wall and the car
* green to red between 150cm - 41cm
* blink blue between  40cm - 31cm
* blink purple between 30cm - 21cm
* blink red between 20cm - 11cm
* blink white between 10 - 6 cm
* Off under 6cm

Hardware:
* hcsr-04 ultra sonic sensor

# common

All libs/modules needed to get stuff working.

Common Features:
* Connect to an **existing Wifi**, or Create a **dedicated WIFI Access Point**
* **Background WiFi watchdog** auto-reconnects with exponential backoff.
* **Robust Log Management**: Auto-rotated logs with two generations (`.1`, `.2`) and scheduled cleanup every 2 hours to protect flash space.
* Centralized flash-state paths in **paths.py** (no scattered magic strings)
* **Debug** easily using **color** (internal LED)
* All Variables you need to adapt like **PIN** are in **config_var.py**

# Hardware

* Develop on an **ESP32-S3-WROOM** N16R8. 
* Use **LED** (5V) to get status of the door.
* 5V or 3.3V **relay** to control motors / provide safety cutoff.
* 0.96" **Oled I2C** (SSD1306) or **LILYGO ST7789** IPS screens.
* **Power Meters**: Shelly EM (Wi-Fi) or JSY-MK-194 (UART).
* **MC-38 magnetic** captor, or any other similar stuff to get status of the door.
* **hcsr-04 ultra sonic** sensor (parking_detection).
* **mfrc522 RFID** for card auth.

# Software

* One of the best IDE project to deal with **ESP32/micropython** is **thonny**: https://thonny.org/
* **micropython**: https://micropython.org/
* **esptool**: https://pypi.org/project/esptool/

Optionnal:
* **ampy**: https://pypi.org/project/adafruit-ampy/

# Devel

Any contribution is welcome. I am currently experimenting and testing lot of domotics stuff.

![image](https://raw.githubusercontent.com/aginies/domotique/refs/heads/main/images/devel.jpg)

# External website

* https://newbiely.com/
* https://micropython.org/
* https://github.com/PIBSAS/MicroPython_ESP32-S3-WROOM-1-N16R8_with_SmartConfig
* https://github.com/jonnor/micropython-zipfile
* https://highlightjs.org/download/
* https://github.com/miguelgrinberg/microdot
