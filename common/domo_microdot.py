import domo_utils as d_u
import config_var as c_v
import paths

from microdot_websocket import with_websocket
import microdot
import asyncio
import os

ws_app = microdot.Microdot()
microdot.Response.default_content_type = 'text/html'
active_connections = set()
last_log = ""
last_mtime = 0

async def check_log_updates():
    """Background task to check for log.txt changes and notify clients."""
    global last_log, last_mtime
    while True:
        try:
            try:
                os.stat(paths.LOG_FILE)
            except OSError:
                with open(paths.LOG_FILE, 'w') as f:
                    f.write("")
            # Check for changes
            stat = os.stat(paths.LOG_FILE)
            mtime = stat[8]
            if mtime != last_mtime:
                with open(paths.LOG_FILE, 'r') as f:
                    log = f.read()
                if log != last_log:
                    last_log = log
                    last_mtime = mtime
                    #print("Update of log found sending!")
                    dead = []
                    for ws in list(active_connections):
                        try:
                            await ws.send(log)
                        except Exception:
                            dead.append(ws)
                    for ws in dead:
                        active_connections.discard(ws)
        except Exception as err:
            d_u.print_and_store_log(f"Error in check_log_updates: {err}")
        await asyncio.sleep(1)

@ws_app.route('/ws')
@with_websocket
async def handle_websocket(request, ws):
    """Handle WebSocket connections and send log updates."""
    d_u.print_and_store_log("New WebSocket connection")
    active_connections.add(ws)
    try:
        if last_log:
            await ws.send(last_log)
        while True:
            await asyncio.sleep(1)
    except Exception as err:
        d_u.print_and_store_log(f"WebSocket error: {err}")
    finally:
        active_connections.remove(ws)

async def start_microdot_ws(IP_ADDR, WS_PORT, error_vars=None, wifi_watchdog_enabled=False):
    asyncio.create_task(check_log_updates())
    if wifi_watchdog_enabled:
        import domo_wifi as d_w
        asyncio.create_task(d_w.wifi_watchdog(error_vars=error_vars))
    d_u.print_and_store_log("Start microdot ws server")
    await ws_app.start_server(
        debug=False,
        host=IP_ADDR,
        port=WS_PORT,
        )