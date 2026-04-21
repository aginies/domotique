# jsy_mk194.py
# Modbus RTU driver for JSY-MK-194 2-channel power meter
import machine
import utime
import struct
import config_var as c_v

class JSY_MK194:
    def __init__(self, uart_id=2, tx=17, rx=16):
        self.uart = machine.UART(uart_id, baudrate=19200, tx=tx, rx=rx, timeout=100)
        # Read 14 registers starting at 0x0048 (covers both channels)
        self.read_cmd = b'\x01\x03\x00\x48\x00\x0E\x44\x18'

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
