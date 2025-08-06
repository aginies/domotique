# antoine@ginies.org
# GPL3
from hcsr04 import HCSR04
import esp32_led as e_l
import time
import domo_utils as d_u

sensor = HCSR04(trigger_pin=18, echo_pin=7, echo_timeout_us=100000)

e_l.french_flag()

def show_distance_color(distance_cm):
    """
    Shows a color from green to red based on a distance in centimeters.
    - Blinks green 3 times at 150cm.
    - Fades from green to red between 150cm and 15cm.
    - Blinks red continuously at 15cm.
    """
    last_distance_multiple = None
    current_multiple = int(distance_cm / 10)
    #if current_multiple != last_distance_multiple:
    #    e_l.blink_color(e_l.blue, 3, 250)
    #    last_distance_multiple = current_multiple

    if distance_cm >= 191:
        e_l.internal_led_off()
    elif 190 >= distance_cm >= 150:
        e_l.blink_color(e_l.green, 1, 50)
    elif 151 >= distance_cm >= 40:
        fraction = (150 - distance_cm) / (150 - 41)
        color = e_l.interpolate_color(e_l.green, e_l.red, fraction)
        e_l.set_color(color[0], color[1], color[2])
    elif 41 >= distance_cm >= 30:
        e_l.blink_color(e_l.blue, 1, 50)
    elif 31 >= distance_cm >= 20:
        e_l.blink_color(e_l.violet, 1, 50)
    elif 21 >= distance_cm >= 10:
        e_l.blink_color(e_l.red, 1, 50)
    elif 11 >= distance_cm >= 6:
        e_l.blink_color(e_l.white, 3, 10)
    elif distance_cm <= 6:
        e_l.internal_led_off()

if __name__ == '__main__':
    d_u.set_freq(160)
    try:   
        last_distance = -1
        while True:
            try:
                distance = int(sensor.distance_cm())
                current_distance = int(distance) 
                if current_distance != last_distance:
                    #print(f"Distance changed: {distance} cm -> {current_distance} cm")
                    show_distance_color(current_distance)
                    last_distance = current_distance
                time.sleep(0.01)
            except OSError as ex:
                print('ERROR getting distance:', ex)

    except KeyboardInterrupt:
        e_l.internal_led_off()
        print("Program stopped.")
