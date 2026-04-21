# antoine@ginies.org
# GPL3

import asyncio
import ujson
import utime
import urandom
import domo_utils as d_u

# Simulated power state
simulated_power = -800.0
trend = -1.0 # -1 for increasing export, 1 for decreasing

async def _update_power_loop():
    """ Background task to fluctuate power """
    global simulated_power, trend
    while True:
        try:
            # Random jitter between -50 and 50
            rand_val = urandom.getrandbits(10)
            jitter = (rand_val % 101) - 50
            
            # Change trend randomly (approx 10% chance)
            if (urandom.getrandbits(7) % 10) == 0:
                trend *= -1
            
            # Apply movement
            simulated_power += (trend * 30.0) + jitter
            
            # Keep within bounds: -2500W (huge export) to 500W (import)
            if simulated_power < -2500.0:
                simulated_power = -2500.0
                trend = 1.0
            elif simulated_power > 500.0:
                simulated_power = 500.0
                trend = -1.0
        except Exception:
            pass
        await asyncio.sleep(2)

async def handle_request(reader, writer):
    global simulated_power
    
    try:
        # Read the request
        await reader.read(128)
        
        data = {
            "emeters": [{
                "power": round(simulated_power, 1),
                "reactive": 0.0,
                "voltage": 232.5,
                "is_valid": True,
                "total": 12345.6
            }]
        }
        
        response = (
            "HTTP/1.0 200 OK\r\n"
            "Content-Type: application/json\r\n"
            "Connection: close\r\n\r\n"
            + ujson.dumps(data)
        )
        
        writer.write(response.encode())
        await writer.drain()
    except Exception as e:
        print(f"FAKE_SHELLY handler error: {e}")
    finally:
        try:
            writer.close()
        except:
            pass

async def start_fake_shelly():
    """ Runs an async HTTP server emulating Shelly EM Gen1 API """
    d_u.print_and_store_log("FAKE_SHELLY: Starting async server on port 8081")
    asyncio.create_task(_update_power_loop())
    try:
        server = await asyncio.start_server(handle_request, '0.0.0.0', 8081)
        d_u.print_and_store_log("FAKE_SHELLY: Server ready")
    except Exception as e:
        d_u.print_and_store_log(f"FAKE_SHELLY: Failed to start: {e}")
