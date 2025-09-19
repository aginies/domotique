# antoine@ginies.org
# GPL3

""" Oled SSD1306 """
import utime
import ssd1306 # the small oled screen
from machine import Pin, SoftI2C
import esp32

import config_var as c_v
import domo_utils as d_u

# ESP32 Pin assignment OLED
i2c = SoftI2C(scl=Pin(c_v.OLED_SCL_PIN), sda=Pin(c_v.OLED_SDA_PIN))
oled_width = 128
oled_height = 64

oled_d = None

def show_info_on_oled(info_start):
    """ Show some info on oled"""
    if oled_d:
        oled_d.text(info_start, 0, 0)
        info_control = "guibo.com"
        oled_d.text(info_control, 0, 10)
        oled_d.text('https://github.c', 0, 20)
        oled_d.text('om/aginies/domot', 0, 30)
        oled_d.text('ique', 0, 40)
        oled_d.text('ag@ginies.org', 0, 50)
        oled_d.show()
        utime.sleep(1)

def initialize_oled():
    """ Attempt to initialize the SSD1306 display """
    global oled_d
    try:
        oled_d = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)
        d_u.print_and_store_log("Ecran OLED Ok")
        oled_d.fill(0)
        return oled_d
    except OSError as err:
        d_u.print_and_store_log(f"Ecran OLED NOK: {err}")
        ERR_OLED = True
        pass

def oled_show_text_line(text, line):
    """ Show a text on a specific line """
    if oled_d:
        oled_d.text(text, 0, line)
        oled_d.text('guibo.com', 0, 50)
        oled_d.show()
        utime.sleep(0.5)

def oled_constant_show(IP_ADDR, PORT, error_vars):
    """ Data always displayed, using the error_vars dictionary for status. """
    while True:
        if oled_d:
            oled_d.fill(0)
            SSID = c_v.AP_SSID
            if c_v.E_WIFI and not error_vars['Wifi Connection']:
                SSID = c_v.WIFI_SSID
            if not error_vars['Wifi'] and not error_vars['Openning Socket']:
                oled_d.text("Wifi SSID:", 0, 0)
                oled_d.text(SSID, 0, 10)
                oled_d.text("Wifi IP AP:", 0, 20)
                INFO_W = f"{IP_ADDR}:{PORT}"
                oled_d.text(INFO_W, 0, 30)
            else:
                oled_d.text(" ! Warning !", 0, 0)
                error_cause = "Network Error"
                if error_vars['Wifi']:
                    error_cause = "Wifi Init"
                elif error_vars['Openning Socket']:
                    error_cause = "Socket Open"

                oled_d.text(f"Cause: {error_cause}", 0, 10)
                oled_d.text(" ! ** !", 0, 20)
                oled_d.text("Mode degrade!", 0, 30)

            mcu_t = esp32.mcu_temperature()
            temp_mcu = f"Temp ESP32: {mcu_t}C"
            oled_d.text(temp_mcu, 0, 40)
            oled_d.show()
            utime.sleep(1)
