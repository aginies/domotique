# antoine@ginies.org
# GPL3
#
# MQTT with Home Assistant Auto-Discovery
# Adapted from t.py logic for proven stability.

import ujson
import utime
import _thread
import machine
import ubinascii
import gc
import config_var as c_v
import domo_utils as d_u

_client         = None
_queue          = []          # list of (topic, payload) pairs
_lock           = _thread.allocate_lock()
_thread_started = False
is_connected    = [False]
_discovery_sent = False
latest_mqtt_grid_power = [None] # Store latest reading from Shelly

def _send_discovery(client, node_id):
    """ Send Home Assistant MQTT Discovery payloads """
    global _discovery_sent
    if _discovery_sent:
        return
    
    # Common device info (Full keys for maximum compatibility)
    device = {
        "identifiers": [node_id],
        "name": c_v.NAME,
        "model": "Solar Diverter",
        "manufacturer": "Antoine Ginies"
    }

    # Availability config (matching the LWT topic)
    avail_topic = f"{c_v.MQTT_NAME}/status"
    avail = {
        "availability_topic": avail_topic,
        "payload_available": "online",
        "payload_not_available": "offline"
    }

    sensors = [
        {
            "name": "Puissance Réseau",
            "state_topic": f"{c_v.MQTT_NAME}/power",
            "unit_of_measurement": "W",
            "device_class": "power",
            "state_class": "measurement",
            "unique_id": f"{node_id}_grid_power"
        },
        {
            "name": f"Puissance {c_v.EQUIPMENT_NAME}",
            "state_topic": f"{c_v.MQTT_NAME}/equipment_power",
            "unit_of_measurement": "W",
            "device_class": "power",
            "state_class": "measurement",
            "unique_id": f"{node_id}_equipment_power"
        },
        {
            "name": f"Charge {c_v.EQUIPMENT_NAME}",
            "state_topic": f"{c_v.MQTT_NAME}/equipment_percent",
            "unit_of_measurement": "%",
            "state_class": "measurement",
            "unique_id": f"{node_id}_equipment_percent"
        }
    ]

    if getattr(c_v, 'E_DS18B20', False):
        sensors.append({
            "name": f"Température {c_v.EQUIPMENT_NAME}",
            "state_topic": f"{c_v.MQTT_NAME}/temperature",
            "unit_of_measurement": "°C",
            "device_class": "temperature",
            "state_class": "measurement",
            "unique_id": f"{node_id}_temp"
        })

    # Add ESP32 Internal Temperature
    sensors.append({
        "name": "Température ESP32",
        "state_topic": f"{c_v.MQTT_NAME}/esp32_temp",
        "unit_of_measurement": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
        "unique_id": f"{node_id}_esp32_temp"
    })

    for s in sensors:
        s["device"] = device
        s.update(avail)
        disc_topic = f"homeassistant/sensor/{node_id}/{s['unique_id']}/config"
        # CRITICAL: Explicitly encode payload to bytes
        payload = ujson.dumps(s).encode("utf-8")
        client.publish(disc_topic, payload, retain=True)
        gc.collect()
        utime.sleep_ms(500)

    _discovery_sent = True
    d_u.print_and_store_log("MQTT: Sent Home Assistant discovery")

def _mqtt_callback(topic, msg):
    """ Handle incoming messages (e.g. from Shelly) """
    try:
        t = topic.decode('utf-8')
        if t == getattr(c_v, 'SHELLY_MQTT_TOPIC', ''):
            latest_mqtt_grid_power[0] = float(msg.decode('utf-8'))
    except:
        pass

def _connect():
    from umqtt.simple import MQTTClient
    
    # Proven working Client ID from t.py
    client_id = ubinascii.hexlify(machine.unique_id())
    
    client = MQTTClient(
        client_id=client_id,
        server=c_v.MQTT_IP,
        port=getattr(c_v, 'MQTT_PORT', 1883),
        user=c_v.MQTT_USER,
        password=c_v.MQTT_PASSWORD,
        keepalive=getattr(c_v, 'MQTT_KEEPALIVE', 60)
    )

    # Set Last Will
    lwt_topic = f"{c_v.MQTT_NAME}/status"
    client.set_last_will(lwt_topic, b"offline", retain=True, qos=0)

    client.connect()
    d_u.print_and_store_log(f"MQTT connected: {client_id.decode()}")
    
    # Subscribe to Shelly if enabled
    if getattr(c_v, 'E_SHELLY_MQTT', False):
        client.set_callback(_mqtt_callback)
        client.subscribe(c_v.SHELLY_MQTT_TOPIC)
        d_u.print_and_store_log(f"MQTT: Subscribed to Shelly {c_v.SHELLY_MQTT_TOPIC}")

    # Announce online
    client.publish(lwt_topic, b"online", retain=True, qos=0)
    
    return client

def _worker():
    """Background thread for MQTT communication."""
    global _client, _discovery_sent
    node_id = c_v.MQTT_NAME.replace(" ", "_").lower()

    while True:
        _lock.acquire()
        msgs = list(_queue)
        _queue.clear()
        _lock.release()

        try:
            if msgs or not _discovery_sent or getattr(c_v, 'E_SHELLY_MQTT', False):
                if _client is None:
                    _client = _connect()
                    is_connected[0] = True
                    utime.sleep_ms(1000) # Wait for connection to settle
                    if not _discovery_sent:
                        _send_discovery(_client, node_id)
                
                # Check for incoming messages (Shelly)
                _client.check_msg()

                retain = getattr(c_v, 'MQTT_RETAIN', False)
                for topic, payload in msgs:
                    # Explicitly encode payload to bytes
                    p_bytes = payload.encode("utf-8") if isinstance(payload, str) else payload
                    _client.publish(topic, p_bytes, retain=retain)
                    utime.sleep_ms(100) # Inter-packet gap
                
                is_connected[0] = True

        except Exception as err:
            if is_connected[0]:
                d_u.print_and_store_log(f"MQTT error: {err}")
            is_connected[0] = False
            if _client:
                try: _client.sock.close()
                except: pass
            _client = None

        utime.sleep_ms(1000)

def _ensure_thread():
    global _thread_started
    if not _thread_started:
        _thread_started = True
        _thread.start_new_thread(_worker, ())

def publish_status(grid_power, equipment_power, equipment_active, force_mode, equipment_percent, water_temp, esp32_temp):
    if not getattr(c_v, 'E_MQTT', False) or not c_v.MQTT_IP:
        return

    _ensure_thread()

    payload = ujson.dumps({
        "grid_power":        grid_power,
        "equipment_power":   equipment_power,
        "equipment_active":  equipment_active,
        "force_mode":        force_mode,
        "equipment_percent": round(equipment_percent, 1),
        "water_temp":        water_temp,
        "esp32_temp":        esp32_temp
    })

    _lock.acquire()
    _queue.clear()
    # Using MQTT_NAME for topics as confirmed by your previous logs
    base = c_v.MQTT_NAME
    _queue.append((f"{base}/status_json",       payload))
    _queue.append((f"{base}/power",             str(grid_power)))
    _queue.append((f"{base}/equipment_power",   str(equipment_power)))
    _queue.append((f"{base}/equipment_percent", str(round(equipment_percent, 1))))
    _queue.append((f"{base}/esp32_temp",        str(esp32_temp)))
    if water_temp is not None:
        _queue.append((f"{base}/temperature",   str(water_temp)))
    _lock.release()
