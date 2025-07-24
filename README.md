# Goal

* Get info on the status of a door, **open** or **closed** using external **LED**.
* Control using a Wifi Access Point the door with a button on a **web server**
* Display all relevant **informations** on a 0.96" **oled screen** (optionnal)
* **Debug** easily using **color** (internal LED)

![image](https://raw.githubusercontent.com/aginies/domotique/refs/heads/main/images/devel.jpg)
![image](https://raw.githubusercontent.com/aginies/domotique/refs/heads/main/images/portail_web.jpg)

# Hardware

* Develop on an ESP32-S3-WROOM. Should work on an ESP32 version but you need to adapt the script for PIN, and myabe disable the internal LED.
* LED (5V) to get status of the door
* Resistance to protect the LED (~270ohms)
* 0.96" Oled I2C screen (aliexpress or any website)
* MC-38 magnetic captor, or any other stuff like this

# Debug color

At start:
* 3 fast blink this is OK
* 5 slow blink at start something is wrong

Color information
* blue: WIFI access point
* green: OLED screen
* pink: Relay
* violet: Socket (port 80)

After start, in case of error, the assigned color will blink one time very fast.

# Software

* **thonny**: https://thonny.org/
* **micropython**: https://micropython.org/
* **esptool**: https://pypi.org/project/esptool/

Optionnal:
* **ampy**: https://pypi.org/project/adafruit-ampy/

# External website

* https://newbiely.com/
* https://micropython.org/
