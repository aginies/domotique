# Goals

* Get info on the status of a door, **open** or **closed** using external **LED**
* Control using a Wifi Access Point the door with a button on a **web server**
* Connect to An existing Wifi, or Create a dedicated WIFI Access Point
* Display all relevant **informations** on a 0.96" **oled screen** (optionnal)
* **Debug** easily using **color** (internal LED)

![image](https://raw.githubusercontent.com/aginies/domotique/refs/heads/main/images/devel.jpg)
![image](https://raw.githubusercontent.com/aginies/domotique/refs/heads/main/images/portail_web.jpg)

# Hardware

* Develop on an ESP32-S3-WROOM. Should work on an ESP32 version but the script needs to be adapted for PIN, and maybe disable the internal LED.
* LED (5V) to get status of the door
* Resistance to protect the LED (~270ohms)
* 5V or 3.3V relay
* 0.96" Oled I2C screen
* MC-38 magnetic captor, or any other similar stuff

# Debug LED color

At start:
* 3 fast blink this is OK
* 5 slow blink at start something is wrong

Color information
* blue: setup an WIFI Access Point
* white: Connect to an existing Wifi
* green: Init the OLED screen
* pink: Control the 5V Relay
* violet: Open a Socket (port 80)

After start, in case of error, the assigned color will blink.

# Software

* **thonny**: https://thonny.org/
* **micropython**: https://micropython.org/
* **esptool**: https://pypi.org/project/esptool/

Optionnal:
* **ampy**: https://pypi.org/project/adafruit-ampy/

# External website

* https://newbiely.com/
* https://micropython.org/
