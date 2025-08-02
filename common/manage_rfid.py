# antoine@ginies.org
# GPL3

import config_var as c_v
import utime
import secrets
from mfrc522 import MFRC522
from machine import Pin

def generate_6bytes():
    # Generate a 6-byte key as a bytes object
    key_bytes = secrets.token_bytes(6)
    CARD_KEY = list(key_bytes)
    print("Generated 6-byte key:", CARD_KEY)
    # print it in hexadecimal format for easy reading
    print("Generated hex key:", key_bytes.hex())

def init_mfrc5322():
    """ Init The card """
    try:
        rdr = MFRC522(
            Pin(c_v.SCK_PIN),
            Pin(c_v.MOSI_PIN),
            Pin(c_v.MISO_PIN),
            Pin(c_v.RST_PIN),
            Pin(c_v.CS_PIN),
            )        
        print("MFRC522 initialized. Waiting for a card...")
        return rdr
    except Exception as err:
        print(f"An error occurred: {err}")

def rfid_do_read():
    """
    Initializes the MFRC522 sensor, waits for a card, and reads its UID.
    """
    rdr = init_mfrc5322()
    if rdr:
        while True:
            (stat, tag_type) = rdr.request(rdr.REQIDL)
            if stat == rdr.OK:
                (stat, uid) = rdr.SelectTagSN()
                if stat == rdr.OK:
                    print("Card detected!")
                    print("UID: " + rdr.tohexstring(uid))
                    utime.sleep(2)
            utime.sleep(0.5)

def rfid_do_access_control():
    """
    Initializes the MFRC522 sensor, waits for a card, authenticates it
    with a key, and then checks the UID against an authorized list.
    """
    rdr = init_mfrc5322()
    if rdr:
        while True:
            (stat, tag_type) = rdr.request(rdr.REQIDL)
            if stat == rdr.OK:
                (stat, uid) = rdr.SelectTagSN()
                if stat == rdr.OK:
                    print("\nCard detected!")
                    print("UID: " + rdr.tohexstring(uid))
                    block_addr = 4
                    # The authenticate() method requires the key and UID
                    stat = rdr.auth(rdr.AUTHENT1A, block_addr, c_v.CARD_KEY, uid)

                    if stat == rdr.OK:
                        # Authentication successful! Now check if the UID is authorized.
                        print("Authentication successful!")
                        if uid in c_v.AUTHORIZED_CARDS:
                            print(">>> ACCESS AUTORIS <<<")
                            # data = rdr.read(block_addr)
                            # print("Data on card:", data)
                        else:
                            print(">>> ACCESS REFUSE - UID NON AUTORISE <<<")
                    else:
                        print(">>> ACCESS REFUSE - AUTHENTICATION FAILED <<<")
                    rdr.stop_crypto1()
                    utime.sleep(3)
            utime.sleep(0.5)

def rfid_do_access_control2():
    """
    Initializes the MFRC522 sensor, waits for a card, and checks its UID
    against a list of authorized cards.
    """
    rdr = init_mfrc5322()
    if rdr:
        while True:
            (stat, tag_type) = rdr.request(rdr.REQIDL)
            if stat == rdr.OK:
                (stat, uid) = rdr.SelectTagSN()
                if stat == rdr.OK:
                    #print("\nCard detected!")
                    print("UID: " + rdr.tohexstring(uid))
                    if uid in c_v.AUTHORIZED_CARDS:
                        print(">>> ACCESS AUTORISE <<<")
                    else:
                        print(">>> ACCESS REJETE <<<")
                    utime.sleep(3)
            utime.sleep(0.5)
