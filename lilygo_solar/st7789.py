# lilygo_solar/st7789.py
import time
from machine import Pin, SPI
import framebuf

class ST7789(framebuf.FrameBuffer):
    def __init__(self, spi, width=240, height=135, reset=None, dc=None, cs=None, backlight=None):
        self.width = 240
        self.height = 135
        self.spi = spi
        self.reset = reset
        self.dc = dc
        self.cs = cs
        self.backlight = backlight
        self.x_offset = 40
        self.y_offset = 53
        self.buffer = bytearray(self.width * self.height * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        self.init()

    def _write(self, command, data=None):
        self.dc.value(0)
        if self.cs: self.cs.value(0)
        self.spi.write(bytearray([command]))
        if self.cs: self.cs.value(1)
        if data is not None:
            self.dc.value(1)
            if self.cs: self.cs.value(0)
            self.spi.write(data)
            if self.cs: self.cs.value(1)

    def init(self):
        self.reset.value(0)
        time.sleep_ms(50)
        self.reset.value(1)
        time.sleep_ms(50)
        self._write(0x01) # SW reset
        time.sleep_ms(150)
        self._write(0x11) # Sleep out
        time.sleep_ms(255)
        self._write(0x3A, b'\x55') # 16-bit color
        
        # 0x78 = Landscape for T-Display (BGR mode)
        self._write(0x36, b'\x78') 
        
        self._write(0x21) # Display inversion on
        self._write(0x13) # Normal display mode on
        self._write(0x29) # Main screen turn on
        if self.backlight: self.backlight.value(1)

    def set_rotation(self, rotation):
        """ 0: Landscape, 1: Landscape Flipped """
        if rotation == 0:
            self._write(0x36, b'\x78') # BGR
            self.x_offset = 40
            self.y_offset = 53
        else:
            self._write(0x36, b'\xB8') # BGR
            self.x_offset = 40
            self.y_offset = 52
        self.show()

    def show(self):
        # Use dynamic offsets
        self._write(0x2A, bytearray([0, self.x_offset, (self.width+self.x_offset-1) >> 8, (self.width+self.x_offset-1) & 0xFF]))
        self._write(0x2B, bytearray([0, self.y_offset, (self.height+self.y_offset-1) >> 8, (self.height+self.y_offset-1) & 0xFF]))
        self._write(0x2C, self.buffer)

    def text_large(self, t, x, y, color):
        """ Draw text at 2x size """
        for i, char in enumerate(t):
            # Draw char to a tiny temporary buffer
            char_buf = bytearray(8 * 8 * 2)
            fb = framebuf.FrameBuffer(char_buf, 8, 8, framebuf.RGB565)
            fb.text(char, 0, 0, color)
            # Scale up 2x
            for cy in range(8):
                for cx in range(8):
                    if fb.pixel(cx, cy):
                        # Draw 2x2 block
                        px = x + (i * 16) + (cx * 2)
                        py = y + (cy * 2)
                        self.fill_rect(px, py, 2, 2, color)

# Color Constants
BLACK = 0x0000
RED = 0xF800
GREEN = 0x07E0
WHITE = 0xFFFF
YELLOW = 0xFFE0
CYAN = 0x07FF
