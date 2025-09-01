# door

Control a Door

* Get info on the status of a door, **open** or **closed** using an external **LED** (optionnal)
* Control using a Wifi Access Point the door with a button on a **web server**
* Display all relevant **informations** on a 0.96" **oled screen** (optionnal)
* Use RFID to open the door (optionnal)
* **Configure** using a web interface

![image](https://raw.githubusercontent.com/aginies/domotique/refs/heads/main/images/portail_web.jpg)

# pool

Control a Pool shutter

* Get info on the status of a shutter, **open** or **closed** using external **LED** (optionnal)
* Control using a **Wifi Access Point** the curtain with **Open / Close / Emergency Stop** buttons on a **web server**
* Display all relevant **informations** on a 0.96" **oled screen** (optionnal)
* **Live log** available
* **Configure** the timing and other parameters through a web interface
* **Files management**
* **Udpate** support an **update.bin** file

![image](https://raw.githubusercontent.com/aginies/domotique/refs/heads/main/images/pool_web.jpg)
![image](https://raw.githubusercontent.com/aginies/domotique/refs/heads/main/images/pool_config.jpg)
![image](https://raw.githubusercontent.com/aginies/domotique/refs/heads/main/images/pool_config_02.jpg)
![image](https://raw.githubusercontent.com/aginies/domotique/refs/heads/main/images/pool_log.jpg)
![image](https://raw.githubusercontent.com/aginies/domotique/refs/heads/main/images/file_management.jpg)

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
* **Debug** easily using **color** (internal LED)
* All Variables you need to adapt like **PIN** are in **config_var.py**

# Hardware

* Develop on an ESP32-S3-WROOM N16R8. Should work on an ESP32 version but the script needs to be adapted for PIN, and maybe disable the internal LED. Be sure to build **micropython** for N16R8 to use all **storage** and **SPIRAM** available.
* LED (5V) to get status of the door
* Resistance to protect the LED (~270ohms)
* 5V or 3.3V relay
* 0.96" Oled I2C screen or any other I2C. Adapt to your hardware
* MC-38 magnetic captor, or any other similar stuff
* hcsr-04 ultra sonic sensor (parking_detection)

# Installation

* copy the full directory into **/** directory of the ESP32
* copy needed libs from **common** directory to **/** directory of the ESP32

# Debug LED color

At start:
* 3 fast blink this is OK
* 5 slow blink at start something is wrong

Color information
* blue: setup an WIFI Access Point
* white: Connect to an existing Wifi
* green: Init the OLED screen
* pink: Control the 5V Relay
* purple: Open a Socket (port 80)

After start, in case of error, the assigned color will blink.

# Software

* One of the best IDE project to deal with **ESP32/micropython** is **thonny**: https://thonny.org/
* **micropython**: https://micropython.org/
* **esptool**: https://pypi.org/project/esptool/

Optionnal:
* **ampy**: https://pypi.org/project/adafruit-ampy/

# Devel

Any contribution is welcome. I am currently expermienting and testing lot of domotics stuff.

![image](https://raw.githubusercontent.com/aginies/domotique/refs/heads/main/images/devel.jpg)

# External website

* https://newbiely.com/
* https://micropython.org/
* https://github.com/PIBSAS/MicroPython_ESP32-S3-WROOM-1-N16R8_with_SmartConfig
* https://github.com/jonnor/micropython-zipfile
* https://highlightjs.org/download/
