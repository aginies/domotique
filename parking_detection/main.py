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
    - Off if distance > 190cm or < 6cm.
    - Blinks green if between 151cm and 190cm.
    - Fades green to red between 41cm and 150cm.
    - Blinks blue if between 31cm and 40cm.
    - Blinks violet if between 21cm and 30cm.
    - Blinks red if between 11cm and 20cm.
    - Blinks white if between 6cm and 10cm.
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

def get_smoothed_distance(readings):
    """Calculates the average of the last few readings."""
    if not readings:
        return 0
    return sum(readings) / len(readings)

if __name__ == '__main__':
    d_u.set_freq(80)  # 80MHz is enough for sensor reading and saves power
    e_l.french_flag()
    try:
        last_distance = -1
        readings = []
        MAX_READINGS = 5
        
        while True:
            try:
                distance = int(sensor.distance_cm())
                readings.append(distance)
                if len(readings) > MAX_READINGS:
                    readings.pop(0)
                
                current_distance = int(get_smoothed_distance(readings))
                
                if current_distance != last_distance:
                    show_distance_color(current_distance)
                    last_distance = current_distance
                
                # HC-SR04 needs at least 60ms between pings to avoid echo interference
                time.sleep(0.1)
                
            except OSError as ex:
                d_u.print_and_store_log(f"ERROR getting distance: {ex}")
                e_l.internal_led_off()
                last_distance = -1
                readings = []

    except KeyboardInterrupt:
        e_l.internal_led_off()
        d_u.print_and_store_log("Program stopped.")
