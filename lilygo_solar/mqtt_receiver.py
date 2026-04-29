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

_lock = _thread.allocate_lock()

try:
    import esp

    _HAS_NVS = True
except ImportError:
    _HAS_NVS = False

_client = None
is_connected = [False]
_display = None

# Draw request queue (fix #1: move drawing from worker thread to main loop)
_draw_pending = False
_pending_mode = 0

# Global state for multi-screen
screen_mode = 0
rotation = 0
history_p = []
history_t = []
last_data = {}


# --- NVS persistence (deferred to avoid module-load allocation) ---
def _nvs_load(key):
    if not _HAS_NVS:
        return None
    try:
        raw = esp.nvs.read(key)
        if raw:
            return [tuple(d) for d in ujson.loads(raw)]
    except Exception:
        pass
    return None


def _nvs_save(key, data_list):
    if not _HAS_NVS:
        return
    try:
        payload = ujson.dumps([list(d) for d in data_list[:5]]).encode()
        esp.nvs.write(key, payload)
    except Exception:
        pass


def _load_history():
    """Defer NVS load to avoid RAM issues at module load."""
    global history_p, history_t
    p = _nvs_load("histp")
    if p and len(p) > 0:
        history_p = p
    t = _nvs_load("histt")
    if t and len(t) > 0:
        history_t = t


def draw_big_text(display, text, x, y, color):
    for i, char in enumerate(text):
        char_buf = bytearray(8 * 8 * 2)
        fb = framebuf.FrameBuffer(char_buf, 8, 8, framebuf.RGB565)
        fb.text(char, 0, 0, 1)
        for cy in range(8):
            for cx in range(8):
                if fb.pixel(cx, cy):
                    display.fill_rect(
                        x + (i * 16) + (cx * 2), y + (cy * 2), 2, 2, color
                    )


def draw_huge_text(display, text, x, y, color):
    for i, char in enumerate(text):
        char_buf = bytearray(8 * 8 * 2)
        fb = framebuf.FrameBuffer(char_buf, 8, 8, framebuf.RGB565)
        fb.text(char, 0, 0, 1)
        for cy in range(8):
            for cx in range(8):
                if fb.pixel(cx, cy):
                    display.fill_rect(
                        x + (i * 24) + (cx * 3), y + (cy * 3), 3, 3, color
                    )


def draw_electricity_symbol(display, x, y, color):
    """Draw a sharp lightning bolt flash symbol"""
    p1 = (x + 14, y)
    p2 = (x + 4, y + 14)
    p3 = (x + 10, y + 14)
    p4 = (x + 2, y + 28)

    display.line(p1[0], p1[1], p2[0], p2[1], color)
    display.line(p2[0], p2[1], p3[0], p3[1], color)
    display.line(p3[0], p3[1], p4[0], p4[1], color)
    display.line(p1[0] - 1, p1[1], p2[0] - 1, p2[1], color)
    display.line(p3[0] - 1, p3[1], p4[0] - 1, p4[1], color)


def draw_redirection_symbol(display, x, y, color):
    """Draw a redirection arrow symbol"""
    display.hline(x, y + 15, 20, color)
    display.line(x + 15, y + 10, x + 20, y + 15, color)
    display.line(x + 15, y + 20, x + 20, y + 15, color)
    display.vline(x, y + 5, 10, color)
    display.hline(x, y + 5, 10, color)


def draw_dashboard(data):
    """Full dashboard draw — no caching (ESP32 only has one 64KB buffer)."""
    if _display is None:
        return

    grid = data.get("grid_power", 0)
    equip = data.get("equipment_power", 0)
    esp_t = data.get("esp32_temp", 0)
    ssr_t = data.get("ssr_temp")
    force = "ON" if data.get("force_mode") else "OFF"

    _display.fill(st7789.BLACK)

    # 1. ENEDIS
    g_color = st7789.RED if grid > 0 else st7789.GREEN
    grid_str = f"{grid:+.0f}"
    draw_electricity_symbol(_display, 10, 5, st7789.WHITE)
    draw_huge_text(_display, grid_str, 58, 5, g_color)
    draw_huge_text(_display, "w", 216, 5, st7789.WHITE)

    # 2. REDIRECTION
    draw_redirection_symbol(_display, 10, 35, st7789.WHITE)
    draw_huge_text(_display, f"{equip:.0f}", 58, 35, st7789.YELLOW)
    draw_huge_text(_display, "w", 216, 35, st7789.WHITE)

    # 3. FORCE
    force_color = st7789.GREEN if force == "ON" else st7789.RED
    _display.text("Force Mode:", 10, 75, st7789.WHITE)
    _display.text(force, 110, 75, force_color)

    # Temps
    esp_txt = (
        f"ESP32: {esp_t:.1f}C" if isinstance(esp_t, (int, float)) else "ESP32: N/A"
    )
    ssr_txt = f"SSR: {ssr_t:.1f}C" if isinstance(ssr_t, (int, float)) else "SSR: N/A"
    _display.text(esp_txt, 10, 95, st7789.WHITE)
    _display.text(ssr_txt, 115, 95, st7789.CYAN)

    # Date & Time
    t = utime.localtime()
    _display.text(
        "{:02d}/{:02d}/{:04d} {:02d}:{:02d}:{:02d}".format(
            t[2], t[1], t[0], t[3], t[4], t[5]
        ),
        5,
        115,
        0x7BEF,
    )
    _display.show()


def draw_graph(mode):
    """mode 1: Power, mode 2: Temp"""
    if _display is None:
        return
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
    if not all_vals:
        return

    v_min, v_max = min(all_vals), max(all_vals)
    if mode == 1:
        v_min = min(v_min, 0)
        v_max = max(v_max, 500)
    else:
        v_min -= 2
        v_max += 2

    v_range = v_max - v_min
    if v_range == 0:
        v_range = 1

    zero_y = 110 - int(((0 if mode == 1 else v_min) - v_min) / v_range * 100)
    zero_y = max(10, min(110, zero_y))

    # Labels
    _display.text(f"{v_max:.0f}", 0, 10, 0x7BEF)
    _display.text(f"{v_min:.0f}", 0, 102, 0x7BEF)

    # Draw Zero line for Power graph
    if mode == 1:
        zero_y = 110 - int(((0 - v_min) / v_range) * 100)
        if 10 <= zero_y <= 110:
            _display.line(35, zero_y, 235, zero_y, 0x3333)

    title = "POW (5m)" if mode == 1 else "TEMP (5m)"
    _display.text(title, 100, 115, st7789.CYAN)

    step = 200 / 75
    for i in range(1, len(hist)):
        x1, x2 = 35 + int((i - 1) * step), 35 + int(i * step)

        y1 = 110 - int((hist[i - 1][0] - v_min) / v_range * 100)
        y2 = 110 - int((hist[i][0] - v_min) / v_range * 100)
        c = (
            (st7789.RED if hist[i][0] > 0 else st7789.GREEN)
            if mode == 1
            else st7789.WHITE
        )
        _display.line(x1, y1, x2, y2, c)

        if hist[i - 1][1] is not None and hist[i][1] is not None:
            y1b = 110 - int((hist[i - 1][1] - v_min) / v_range * 100)
            y2b = 110 - int((hist[i][1] - v_min) / v_range * 100)
            _display.line(x1, y1b, x2, y2b, st7789.YELLOW if mode == 1 else st7789.CYAN)

    _display.show()


def _mqtt_callback(topic, msg):
    """Sets draw request flags instead of drawing directly (fix #1)."""
    global _draw_pending, _pending_mode
    try:
        data = ujson.loads(msg.decode("utf-8"))
        last_data.clear()
        last_data.update(data)
        grid = data.get("grid_power", 0)
        equip = data.get("equipment_power", 0)
        esp_t = data.get("esp32_temp", 0)
        ssr_t = data.get("ssr_temp")

        with _lock:
            history_p.append((grid, equip))
            history_t.append((esp_t, ssr_t))
            if len(history_p) > 75:
                history_p.pop(0)
            if len(history_t) > 75:
                history_t.pop(0)
            # Debounce NVS: only save near the cap
            if len(history_p) > 65:
                _nvs_save("histp", history_p)
                _nvs_save("histt", history_t)

            # Request draw in main thread (fix #1)
            _draw_pending = True
            _pending_mode = screen_mode
    except Exception as e:
        print("MQTT Data Error:", e)


def _connect():
    from umqtt.simple import MQTTClient

    cid = ubinascii.hexlify(machine.unique_id())
    client = MQTTClient(
        cid,
        c_v.MQTT_IP,
        port=c_v.MQTT_PORT,
        user=c_v.MQTT_USER,
        password=c_v.MQTT_PASSWORD,
        keepalive=60,
    )
    client.set_callback(_mqtt_callback)
    client.connect()
    client.subscribe(c_v.MQTT_TOPIC_SUB)
    is_connected[0] = True
    return client


# Exponential backoff for reconnection (fix #4)
_reconnect_delay = 5
_max_reconnect_delay = 300


def _worker():
    global _client, _reconnect_delay
    while True:
        try:
            if _client is None:
                gc.collect()
                _client = _connect()
                _reconnect_delay = 5  # reset on success
            is_connected[0] = True
            _client.check_msg()
        except Exception as e:
            is_connected[0] = False
            print("MQTT Worker Error:", e)
            if _display is not None:
                try:
                    _display.fill(st7789.BLACK)
                    draw_huge_text(_display, "MQTT", 10, 20, st7789.RED)
                    draw_huge_text(_display, "OFFLINE", 10, 55, st7789.RED)
                    _display.text("Check Broker/WiFi", 10, 95, st7789.WHITE)
                    _display.text(str(e)[:30], 10, 115, 0x7BEF)
                    _display.show()
                except Exception:
                    pass

            if _client:
                try:
                    _client.sock.close()
                except Exception:
                    pass
                _client = None

            # Exponential backoff (fix #4)
            utime.sleep(_reconnect_delay)
            _reconnect_delay = min(_reconnect_delay * 2, _max_reconnect_delay)

        # fix #5: removed utime.sleep_ms(200) - check_msg is blocking


def start(display):
    global _display
    gc.collect()
    _display = display
    # Defer NVS load — too early at module import
    try:
        _load_history()
    except Exception:
        pass
    _thread.start_new_thread(_worker, ())
