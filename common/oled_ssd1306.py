# antoine@ginies.org
# GPL3

""" Oled SSD1306 """
import utime
import ssd1306 # the small oled screen
from machine import Pin, SoftI2C

# ESP32 Pin assignment OLED
i2c = SoftI2C(scl=Pin(36), sda=Pin(21))
oled_width = 128
oled_height = 64

oled_d = None

def initialize_oled():
    """ Attempt to initialize the SSD1306 display """
    global oled_d
    try:
        oled_d = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)
        print("Ecran OLED Ok")
        oled_d.fill(0)
        return oled_d
    except OSError as err:
        print(f"Ecran OLED NOK: {err}")
        ERR_OLED = True

def oled_show_text_line(text, line):
    """ Show a text on a specific line """
    if oled_d:
        oled_d.text(text, 0, line)
        oled_d.text('guibo.com', 0, 50)
        oled_d.show()
        utime.sleep(0.5)
