# lilygo_solar/wifi.py
import network
import utime
import gc
import config_var as c_v


def connect():
    gc.collect()
    gc.collect()
    gc.collect()
    sta_if = network.WLAN(network.STA_IF)
    ap_if = network.WLAN(network.AP_IF)

    # Clean state
    if sta_if.active():
        sta_if.active(False)
    if ap_if.active():
        ap_if.active(False)
    gc.collect()

    if not c_v.E_WIFI:
        return setup_ap()

    print(f"Connecting to {c_v.WIFI_SSID}...")
    sta_if.active(True)
    sta_if.connect(c_v.WIFI_SSID, c_v.WIFI_PASSWORD)

    # Wait max 10 seconds
    for _ in range(20):
        if sta_if.isconnected():
            print("WiFi Connected! IP:", sta_if.ifconfig()[0])
            return sta_if.ifconfig()[0]
        utime.sleep_ms(500)

    print("WiFi Failed, falling back to AP")
    return setup_ap()


def setup_ap():
    gc.collect()
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=c_v.AP_SSID, password=c_v.AP_PASSWORD)
    ap.active(True)
    ap.ifconfig(c_v.AP_IP)
    print("AP Active:", c_v.AP_SSID, "IP:", ap.ifconfig()[0])
    return ap.ifconfig()[0]


def ntp_sync():
    import ntptime
    import machine

    print("Syncing NTP...")
    try:
        # ntptime.settime() already sets RTC with UTC offset
        # Apply custom TZ offset on top of what ntptime does
        offset = getattr(c_v, "TZ_OFFSET", 0)
        t = utime.time()
        tm = utime.localtime(t + offset)
        # ESP32 RTC.datetime: (year, month, day, weekday, hours, minutes, seconds, subseconds)
        # utime.localtime() weekday: Monday=0
        # machine.RTC() weekday: Monday=1
        machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
        print("NTP Synced. Current time:", utime.localtime())
        return True
    except Exception as e:
        print("NTP Error:", e)
        return False
