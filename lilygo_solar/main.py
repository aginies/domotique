# lilygo_solar/main.py
import gc
import machine
from machine import Pin
import utime
import wifi
import mqtt_receiver
import config_var as c_v
import st7789

# Safe flags for main loop processing
_btn_pressed = False

def main():
    global _btn_pressed
    gc.collect()
    print("--- Lilygo T-Display Starting ---")

    # 1. Initialize Display
    try:
        spi = machine.SPI(1, baudrate=30000000, sck=Pin(18), mosi=Pin(19), miso=Pin(21))
        display = st7789.ST7789(
            spi, 240, 135,
            reset=Pin(23, Pin.OUT),
            dc=Pin(16, Pin.OUT),
            cs=Pin(5, Pin.OUT),
            backlight=Pin(4, Pin.OUT)
        )
        Pin(4, Pin.OUT).value(1)
        display.fill(st7789.BLACK)
        display.show()
        display.text("Lilygo Starting...", 10, 10, st7789.WHITE)
        display.show()
    except Exception as e:
        print("Display Error:", e)
        display = None

    # 2. Button setup
    btn1 = Pin(35, Pin.IN, Pin.PULL_UP)
    btn2 = Pin(0, Pin.IN, Pin.PULL_UP)
    
    last_press = 0

    def irq_btn1(pin):
        global _btn_pressed
        _btn_pressed = True

    def irq_btn2(pin):
        global _btn_pressed
        _btn_pressed = True

    btn1.irq(trigger=Pin.IRQ_FALLING, handler=irq_btn1)
    btn2.irq(trigger=Pin.IRQ_FALLING, handler=irq_btn2)

    # 3. Wifi
    ip = wifi.connect()
    
    # 4. MQTT
    mqtt_receiver.start(display)
    
    print("System Running Safely.")
    log_check_counter = 0
    wdt = machine.WDT(timeout=60000)
    
    while True:
        wdt.feed()
        
        # Log cleanup check (every 2 hours)
        log_check_counter += 5
        if log_check_counter >= 7200:
            log_check_counter = 0
            import paths
            import domo_utils as d_u
            d_u._rotate_log_if_needed(paths.LOG_FILE, 40 * 1024)

        # Process button clicks safely outside of IRQ
        if _btn_pressed:
            now = utime.ticks_ms()
            if utime.ticks_diff(now, last_press) > 300:
                mqtt_receiver.screen_mode = (mqtt_receiver.screen_mode + 1) % 3
                print("Mode Cycle:", mqtt_receiver.screen_mode)
                
                # Redraw
                if mqtt_receiver.last_data:
                    if mqtt_receiver.screen_mode == 0: mqtt_receiver.draw_dashboard(mqtt_receiver.last_data)
                    elif mqtt_receiver.screen_mode == 1: mqtt_receiver.draw_graph(1)
                    elif mqtt_receiver.screen_mode == 2: mqtt_receiver.draw_graph(2)
                
                last_press = now
            _btn_pressed = False # Reset flag

        utime.sleep_ms(50) # Fast poll, very low CPU usage

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import sys
        sys.print_exception(e)
