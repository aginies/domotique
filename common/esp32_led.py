""" ESP32 internal Led """
import utime
from machine import Pin
from neopixel import NeoPixel
import config_var as c_v

I_led = Pin(c_v.I_LED_PIN, Pin.OUT)
np = NeoPixel(I_led, 1)
# One color per function to find the root cause
green = (0, 255 , 0) # OLED display
red = (255, 0, 0) # error?
blue = (0, 0, 255) # setup Wifi access point
violet = (154, 14, 234) # socket bind to address
pink = (255, 192, 203) # relay (web button to control motor)
white = (255, 255, 255) # connect to existing Wifi
led_off = (0, 0, 0)

def internal_led_blink(color1, color2, NB, timing):
    """ rules is: blink 3 times for OK, 5 times for Error/NOK"""
    for _ in (range(0, NB)):  
        np[0] = color1
        np.write()
        utime.sleep(timing)
        np[0] = color2
        np.write()
        utime.sleep(timing)
        internal_led_off()

def french_flag():
    times = 0.8
    np[0] = blue; np.write(); utime.sleep(times)
    np[0] = white; np.write(); utime.sleep(times)
    np[0] = red; np.write(); utime.sleep(times)
    internal_led_off()

def internal_led_color(color):
    """ easy way to change the color led """
    internal_led_color_always(color)
    utime.sleep(0.1)
    internal_led_off()

def internal_led_color_always(color):
    """ Always show the color """
    np[0] = color
    np.write()

def internal_led_off():
    """ Led is off """
    np[0] = led_off
    np.write()