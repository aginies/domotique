import domo_utils as d_u
import config_var as c_v

from microdot_websocket import with_websocket
import microdot
import asyncio
import os
import time

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
                os.stat('log.txt')
            except OSError:
                with open('log.txt', 'w') as f:
                    f.write("")
            # Check for changes
            stat = os.stat('log.txt')
            mtime = stat[8]
            if mtime != last_mtime:
                with open('log.txt', 'r') as f:
                    log = f.read()
                if log != last_log:
                    last_log = log
                    last_mtime = mtime
                    #print("Update of log found sending!")
                    for ws_app in active_connections:
                        try:
                            await ws_app.send(log)
                        except:
                            active_connections.remove(ws_app)
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

def start_microdot_ws(IP_ADDR, WS_PORT):
    asyncio.create_task(check_log_updates())
    d_u.print_and_store_log("Start microdot ws server")
    await ws_app.start_server(
        debug=False,
        host=IP_ADDR,
        port=WS_PORT,
        )