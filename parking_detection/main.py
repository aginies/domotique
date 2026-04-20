# antoine@ginies.org
# GPL3
from hcsr04 import HCSR04
import esp32_led as e_l
import time
import domo_utils as d_u
import config_var as c_v

sensor = HCSR04(
    trigger_pin=c_v.HCSR04_TRIGGER_PIN,
    echo_pin=c_v.HCSR04_ECHO_PIN,
    echo_timeout_us=c_v.HCSR04_ECHO_TIMEOUT_US,
)

def show_distance_color(distance_cm):
    """
    Shows a color from green to red based on a distance in centimeters.
    - Blinks green 3 times at 150cm.
    - Fades from green to red between 150cm and 15cm.
    - Blinks red continuously at 15cm.
    """
    if distance_cm >= 191:
        e_l.internal_led_off()
    elif 190 >= distance_cm >= 151:
        e_l.blink_color(e_l.green, 1, 50)
    elif 150 >= distance_cm >= 41:
        fraction = (150 - distance_cm) / (150 - 41)
        color = e_l.interpolate_color(e_l.green, e_l.red, fraction)
        e_l.set_color(color[0], color[1], color[2])
    elif 40 >= distance_cm >= 31:
        e_l.blink_color(e_l.blue, 1, 50)
    elif 30 >= distance_cm >= 21:
        e_l.blink_color(e_l.violet, 1, 50)
    elif 20 >= distance_cm >= 11:
        e_l.blink_color(e_l.red, 1, 50)
    elif 10 >= distance_cm >= 6:
        e_l.blink_color(e_l.white, 3, 10)
    elif distance_cm <= 5:
        e_l.internal_led_off()

if __name__ == '__main__':
    d_u.set_freq(160)
    e_l.french_flag()
    try:
        last_distance = -1
        while True:
            try:
                current_distance = int(sensor.distance_cm())
                if current_distance != last_distance:
                    show_distance_color(current_distance)
                    last_distance = current_distance
                time.sleep(0.01)
            except OSError as ex:
                print('ERROR getting distance:', ex)
                e_l.internal_led_off()
                last_distance = -1

    except KeyboardInterrupt:
        e_l.internal_led_off()
        print("Program stopped.")
