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
_btn1_pressed = False
_btn2_pressed = False

def main():
    global _btn1_pressed, _btn2_pressed
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
        global _btn1_pressed
        _btn1_pressed = True

    def irq_btn2(pin):
        global _btn2_pressed
        _btn2_pressed = True

    btn1.irq(trigger=Pin.IRQ_FALLING, handler=irq_btn1)
    btn2.irq(trigger=Pin.IRQ_FALLING, handler=irq_btn2)

    # 3. Wifi
    ip = wifi.connect()
    if ip:
        wifi.ntp_sync()
    
    # 4. MQTT
    mqtt_receiver.start(display)
    
    print("System Running Safely.")
    wdt = machine.WDT(timeout=60000)
    flush_counter = 0
    ntp_counter = 0
    
    while True:
        wdt.feed()
        
        # Periodic flush of logs (every 30 mins)
        flush_counter += 1
        if flush_counter >= 36000: # 36000 * 50ms = 1800s = 30m
            import domo_utils as d_u
            d_u.flush_logs()
            flush_counter = 0

        # Periodic NTP sync (every 1 hour)
        ntp_counter += 1
        if ntp_counter >= 72000:
            wifi.ntp_sync()
            ntp_counter = 0

        # Process button clicks safely outside of IRQ
        if _btn1_pressed or _btn2_pressed:
            now = utime.ticks_ms()
            if utime.ticks_diff(now, last_press) > 300:
                if _btn1_pressed:
                    mqtt_receiver.screen_mode = (mqtt_receiver.screen_mode + 1) % 3
                    print("Mode Cycle:", mqtt_receiver.screen_mode)
                elif _btn2_pressed:
                    mqtt_receiver.rotation = 1 - mqtt_receiver.rotation
                    print("Rotation Toggle:", mqtt_receiver.rotation)
                    if display:
                        display.set_rotation(mqtt_receiver.rotation)
                
                # Redraw
                if mqtt_receiver.last_data:
                    if mqtt_receiver.screen_mode == 0: mqtt_receiver.draw_dashboard(mqtt_receiver.last_data)
                    elif mqtt_receiver.screen_mode == 1: mqtt_receiver.draw_graph(1)
                    elif mqtt_receiver.screen_mode == 2: mqtt_receiver.draw_graph(2)
                
                last_press = now
            _btn1_pressed = False # Reset flags
            _btn2_pressed = False

        utime.sleep_ms(50) # Fast poll, very low CPU usage

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import sys
        sys.print_exception(e)
