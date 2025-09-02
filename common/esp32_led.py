# antoine@ginies.org
# GPL3

""" ESP32 internal Led """
import utime
from machine import Pin
from neopixel import NeoPixel
import config_var as c_v

# on ESP32-S3 you must sold the RGB pin on the board!
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
    times = 0.4
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

def set_color(r, g, b):
    """Sets the color of the NeoPixel """
    np[0] = (r, g, b)
    np.write()

def blink_color(color, num_blinks, delay_ms):
    """Blinks the NeoPixel with a given color """
    for _ in range(num_blinks):
        set_color(color[0], color[1], color[2])
        utime.sleep_ms(delay_ms)
        set_color(0, 0, 0)
        utime.sleep_ms(delay_ms)
 
def interpolate_color(start_color, end_color, fraction):
    """Interpolates between two colors based on a fraction """
    r = int(start_color[0] + (end_color[0] - start_color[0]) * fraction)
    g = int(start_color[1] + (end_color[1] - start_color[1]) * fraction)
    b = int(start_color[2] + (end_color[2] - start_color[2]) * fraction)
    return (r, g, b)
