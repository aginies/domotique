# antoine@ginies.org
# GPL3

""" Oled SSD1306 """
import utime
import ssd1306 # the small oled screen
from machine import Pin, SoftI2C

import config_var as c_v
import domo_utils as d_u

# ESP32 Pin assignment OLED
i2c = SoftI2C(scl=Pin(c_v.OLED_SCL_PIN), sda=Pin(c_v.OLED_SDA_PIN))
oled_width = 128
oled_height = 64

oled_d = None

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
