# lilygo_solar/mqtt_receiver.py
import ujson
import utime
import _thread
import machine
import ubinascii
import gc
import framebuf
import config_var as c_v
import st7789

_client = None
is_connected = [False]
_display = None

# Global state for multi-screen
# 0: Dashboard, 1: Power Graph, 2: Temp Graph
screen_mode = 0 
history_p = [] # Power: (grid, equip)
history_t = [] # Temp: (esp, ssr)
last_data = {} # Store last MQTT payload for manual redraw

def draw_big_text(display, text, x, y, color):
    for i, char in enumerate(text):
        char_buf = bytearray(8 * 8 * 2)
        fb = framebuf.FrameBuffer(char_buf, 8, 8, framebuf.RGB565)
        fb.text(char, 0, 0, 1)
        for cy in range(8):
            for cx in range(8):
                if fb.pixel(cx, cy):
                    display.fill_rect(x + (i * 16) + (cx * 2), y + (cy * 2), 2, 2, color)

def draw_huge_text(display, text, x, y, color):
    for i, char in enumerate(text):
        char_buf = bytearray(8 * 8 * 2)
        fb = framebuf.FrameBuffer(char_buf, 8, 8, framebuf.RGB565)
        fb.text(char, 0, 0, 1)
        for cy in range(8):
            for cx in range(8):
                if fb.pixel(cx, cy):
                    display.fill_rect(x + (i * 24) + (cx * 3), y + (cy * 3), 3, 3, color)

def draw_dashboard(data):
    grid = data.get('grid_power', 0)
    equip = data.get('equipment_power', 0)
    esp_t = data.get('esp32_temp', 0)
    ssr_t = data.get('water_temp', 'N/A')
    force = "ON" if data.get('force_mode') else "OFF"
    
    _display.fill(st7789.BLACK)
    _display.show()
    _display.fill(st7789.BLACK)
    
    # 1. ENEDIS (Huge)
    g_color = st7789.RED if grid > 0 else st7789.GREEN
    draw_huge_text(_display, "E:", 10, 5, st7789.WHITE)
    draw_huge_text(_display, f"{grid:.0f}", 58, 5, g_color)
    draw_huge_text(_display, "w", 170, 5, st7789.WHITE)
    
    # 2. RED (Huge)
    draw_huge_text(_display, "R:", 10, 35, st7789.WHITE)
    draw_huge_text(_display, f"{equip:.0f}", 58, 35, st7789.YELLOW)
    draw_huge_text(_display, "w", 170, 35, st7789.WHITE)
    # 3. FORCE (Normal Label, Colorized Status)
    force_color = st7789.GREEN if force == "ON" else st7789.RED
    _display.text("Force Mode:", 10, 75, st7789.WHITE)
    _display.text(force, 110, 75, force_color)
    
    esp_txt = f"ESP32: {esp_t:.1f}C" if esp_t is not None else "ESP32: N/A"
    ssr_txt = f"SSR: {ssr_t:.1f}C" if isinstance(ssr_t, (int, float)) else "SSR: N/A"
    _display.text(esp_txt, 10, 95, st7789.WHITE)
    _display.text(ssr_txt, 115, 95, st7789.CYAN)

    # 5. Date & Time (Normal)
    t = utime.localtime()
    # Format: DD/MM/YYYY HH:MM:SS
    date_str = "{:02d}/{:02d}/{:04d} {:02d}:{:02d}:{:02d}".format(t[2], t[1], t[0], t[3], t[4], t[5])
    _display.text(date_str, 5, 115, 0x7BEF)
    
    _display.show()

def draw_graph(mode):
    """ mode 1: Power, mode 2: Temp """
    _display.fill(st7789.BLACK)
    _display.show()
    _display.fill(st7789.BLACK)
    
    hist = history_p if mode == 1 else history_t
    if not hist:
        _display.text("No data", 10, 60, st7789.WHITE)
        _display.show()
        return

    # Draw Axis
    _display.line(35, 10, 35, 110, st7789.WHITE) 
    _display.line(35, 110, 235, 110, st7789.WHITE)
    
    # Dynamic Scaling
    all_vals = [v for pair in hist for v in pair if isinstance(v, (int, float))]
    if not all_vals: return
    
    v_min, v_max = min(all_vals), max(all_vals)
    # Add padding
    if mode == 1: # Power
        v_min = min(v_min, 0)
        v_max = max(v_max, 500)
    else: # Temp
        v_min -= 2
        v_max += 2
        
    v_range = v_max - v_min
    if v_range == 0: v_range = 1
    
    zero_y = 110 - int(( (0 if mode==1 else v_min) - v_min) / v_range * 100)
    zero_y = max(10, min(110, zero_y))

    # Labels
    _display.text(f"{v_max:.0f}", 0, 10, 0x7BEF)
    _display.text(f"{v_min:.0f}", 0, 102, 0x7BEF)
    
    # Draw Zero line for Power graph
    if mode == 1:
        zero_y = 110 - int(((0 - v_min) / v_range) * 100)
        if 10 <= zero_y <= 110:
            _display.line(35, zero_y, 235, zero_y, 0x3333) # Grey zero line

    title = "POW (5m)" if mode == 1 else "TEMP (5m)"
    _display.text(title, 100, 115, st7789.CYAN)

    step = 200 / 75
    for i in range(1, len(hist)):
        x1, x2 = 35 + int((i-1)*step), 35 + int(i*step)
        
        # Line 1 (Grid or ESP)
        y1 = 110 - int((hist[i-1][0] - v_min) / v_range * 100)
        y2 = 110 - int((hist[i][0] - v_min) / v_range * 100)
        c = (st7789.RED if hist[i][0] > 0 else st7789.GREEN) if mode == 1 else st7789.WHITE
        _display.line(x1, y1, x2, y2, c)
        
        # Line 2 (Equip or SSR)
        if hist[i-1][1] is not None and hist[i][1] is not None:
            y1b = 110 - int((hist[i-1][1] - v_min) / v_range * 100)
            y2b = 110 - int((hist[i][1] - v_min) / v_range * 100)
            _display.line(x1, y1b, x2, y2b, st7789.YELLOW if mode == 1 else st7789.CYAN)

    _display.show()

def _mqtt_callback(topic, msg):
    global _display, history_p, history_t, last_data
    try:
        data = ujson.loads(msg.decode('utf-8'))
        last_data = data # Save for button redraw
        grid = data.get('grid_power', 0)
        equip = data.get('equipment_power', 0)
        esp_t = data.get('esp32_temp', 0)
        ssr_t = data.get('water_temp')
        
        history_p.append((grid, equip))
        history_t.append((esp_t, ssr_t))
        if len(history_p) > 75: history_p.pop(0)
        if len(history_t) > 75: history_t.pop(0)
        
        if _display:
            if screen_mode == 0: draw_dashboard(data)
            elif screen_mode == 1: draw_graph(1)
            else: draw_graph(2)
    except Exception as e:
        print("MQTT Data Error:", e)

def _connect():
    from umqtt.simple import MQTTClient
    cid = ubinascii.hexlify(machine.unique_id())
    client = MQTTClient(cid, c_v.MQTT_IP, port=c_v.MQTT_PORT, user=c_v.MQTT_USER, password=c_v.MQTT_PASSWORD, keepalive=60)
    client.set_callback(_mqtt_callback)
    client.connect()
    client.subscribe(c_v.MQTT_TOPIC_SUB)
    is_connected[0] = True
    return client

def _worker():
    global _client
    while True:
        try:
            if _client is None:
                gc.collect()
                _client = _connect()
            _client.check_msg()
            is_connected[0] = True
        except Exception as e:
            is_connected[0] = False
            print("MQTT Worker Error:", e)
            if _display:
                _display.fill(st7789.BLACK)
                _display.show()
                _display.fill(st7789.BLACK)
                draw_huge_text(_display, "MQTT", 10, 20, st7789.RED)
                draw_huge_text(_display, "OFFLINE", 10, 55, st7789.RED)
                _display.text("Check Broker/WiFi", 10, 95, st7789.WHITE)
                _display.text(str(e)[:30], 10, 115, 0x7BEF)
                _display.show()
            
            if _client:
                try: _client.sock.close()
                except: pass
                _client = None
            utime.sleep(5)
        utime.sleep_ms(200)

def start(display):
    global _display
    _display = display
    _thread.start_new_thread(_worker, ())
