# jsy_mk194.py
# Modbus RTU driver for JSY-MK-194 2-channel power meter.
# Optionally handles the Zx zero-cross output pin (JSY-MK-194G) for phase-angle control.
import machine
import utime
import struct
import config_var as c_v

class JSY_MK194:
    def __init__(self, uart_id=2, tx=17, rx=16, zx_pin=None):
        self.uart = machine.UART(uart_id, baudrate=19200, tx=tx, rx=rx, timeout=100)
        # Read 14 registers starting at 0x0048 (covers both channels)
        self.read_cmd = b'\x01\x03\x00\x48\x00\x0E\x44\x18'

        # Zero-cross detection support.
        # Pre-allocated bytearrays — IRQ handlers must not allocate heap memory.
        # _zx_flag[0]:    set to 1 by IRQ, cleared to 0 by consumer.
        # _zx_time_us[0:4]: ticks_us() at IRQ time, little-endian uint32.
        self._zx_flag    = bytearray(1)
        self._zx_time_us = bytearray(4)
        self._zx_pin_obj = None

        if zx_pin is not None:
            pin = machine.Pin(zx_pin, machine.Pin.IN)
            pin.irq(trigger=machine.Pin.IRQ_RISING, handler=self._zx_irq)
            self._zx_pin_obj = pin

    def _zx_irq(self, pin):
        # IRQ handler: NO heap allocation allowed.
        # Encode ticks_us() as little-endian uint32 into pre-allocated bytearray.
        t = utime.ticks_us()
        self._zx_time_us[0] =  t        & 0xFF
        self._zx_time_us[1] = (t >>  8) & 0xFF
        self._zx_time_us[2] = (t >> 16) & 0xFF
        self._zx_time_us[3] = (t >> 24) & 0xFF
        self._zx_flag[0] = 1

    def get_zx_event(self):
        """
        Returns (timestamp_us, True) if a new ZX event is pending, else (0, False).
        Clears the flag before reading the timestamp: a ZX that fires between
        the clear and the read will set the flag again and be caught next call.
        """
        if self._zx_flag[0]:
            self._zx_flag[0] = 0
            t = (self._zx_time_us[0]
                 | (self._zx_time_us[1] <<  8)
                 | (self._zx_time_us[2] << 16)
                 | (self._zx_time_us[3] << 24))
            return t, True
        return 0, False

    def read_data(self):
        """ Returns (grid_power, equip_power) or None """
        # Clear junk
        while self.uart.any(): self.uart.read()

        self.uart.write(self.read_cmd)

        # Response is 61 bytes. Wait up to 150ms
        start = utime.ticks_ms()
        while self.uart.any() < 61 and utime.ticks_diff(utime.ticks_ms(), start) < 150:
            utime.sleep_ms(10)

        res = self.uart.read(61)
        if not res or len(res) < 61:
            return None

        try:
            # Channel 1: Power at offset 11, Direction at offset 27
            c1_p_raw = struct.unpack('>I', res[11:15])[0]
            c1_p = c1_p_raw * 0.0001
            if res[27] == 0x01: c1_p = -c1_p

            # Channel 2: Power at offset 43, Direction at offset 59
            c2_p_raw = struct.unpack('>I', res[43:47])[0]
            c2_p = c2_p_raw * 0.0001
            if res[59] == 0x01: c2_p = -c2_p

            return c1_p, c2_p
        except Exception:
            return None
