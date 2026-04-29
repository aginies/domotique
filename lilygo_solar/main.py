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
    gc.collect()  # Extra GC to free RAM before large allocations
    gc.collect()
    print("--- Lilygo T-Display Starting ---")

    # 1. Initialize Display
    try:
        spi = machine.SPI(1, baudrate=30000000, sck=Pin(18), mosi=Pin(19), miso=Pin(21))
        display = st7789.ST7789(
            spi,
            240,
            135,
            reset=Pin(23, Pin.OUT),
            dc=Pin(16, Pin.OUT),
            cs=Pin(5, Pin.OUT),
            backlight=Pin(4, Pin.OUT),
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

    # fix #6: initialize last_press with current ticks_ms instead of 0
    last_press = utime.ticks_ms()

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
    wdt = machine.WDT(timeout=120000)
    flush_counter = 0
    ntp_counter = 0

    while True:
        wdt.feed()

        # Periodic flush of logs (every 30 mins)
        flush_counter += 1
        if flush_counter >= 36000:  # 36000 * 50ms = 1800s = 30m
            try:
                import domo_utils as d_u

                d_u.flush_logs()
            except ImportError:
                pass
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
                debounce_timeout = utime.ticks_add(now, 200)

                if _btn1_pressed:
                    while utime.ticks_diff(utime.ticks_ms(), debounce_timeout) < 0:
                        if btn1.value():
                            break
                        utime.sleep_ms(10)
                    mqtt_receiver.screen_mode = (mqtt_receiver.screen_mode + 1) % 3
                    print("Mode Cycle:", mqtt_receiver.screen_mode)

                if _btn2_pressed:
                    while utime.ticks_diff(utime.ticks_ms(), debounce_timeout) < 0:
                        if btn2.value():
                            break
                        utime.sleep_ms(10)
                    mqtt_receiver.rotation = 1 - mqtt_receiver.rotation
                    print("Rotation Toggle:", mqtt_receiver.rotation)
                    if display:
                        display.set_rotation(mqtt_receiver.rotation)

                last_press = now
            _btn1_pressed = False
            _btn2_pressed = False

        # fix #1: process draw requests from worker thread in main loop
        if mqtt_receiver._draw_pending:
            with mqtt_receiver._lock:
                mqtt_receiver._draw_pending = False
                mode = mqtt_receiver._pending_mode
            if mqtt_receiver.last_data:
                if mode == 0:
                    mqtt_receiver.draw_dashboard(mqtt_receiver.last_data)
                elif mode == 1:
                    mqtt_receiver.draw_graph(1)
                elif mode == 2:
                    mqtt_receiver.draw_graph(2)

        utime.sleep_ms(50)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import sys

        sys.print_exception(e)
