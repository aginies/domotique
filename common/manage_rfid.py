# antoine@ginies.org
# GPL3

import config_var as c_v
import utime
import os
from mfrc522 import MFRC522
from machine import Pin

def generate_6bytes():
    # Generate a 6-byte key as a bytes object
    key_bytes = os.urandom(6)
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

# The default key for new, unprogrammed Mifare Classic cards
DEFAULT_KEY = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

def program_rfid_card():
    """
    Initializes the MFRC522 sensor, waits for a card, and programs it with a new
    secure key on specified sector trailer blocks.
    """
    rdr = init_mfrc5322()
    ACCESS_BITS = [0xFF, 0x07, 0x80]
    SECTOR_TRAILER_BLOCKS = [7, 11]
    if rdr:
        print("MFRC522 initialized. Please place a new card on the reader to program it...")
        while True:
            (stat, tag_type) = rdr.request(rdr.REQIDL)
            if stat == rdr.OK:
                (stat, uid) = rdr.SelectTagSN()
                if stat == rdr.OK:
                    print("\nCard detected! UID: " + rdr.tohexstring(uid))
                    # Loop through the sectors we want to program
                    for sector_trailer_block in SECTOR_TRAILER_BLOCKS:
                        print(f"Attempting to program sector trailer block {sector_trailer_block}...")
                        # Step 1: Authenticate with the default key (which the card has by default)
                        stat = rdr.auth(rdr.AUTHENT1A, sector_trailer_block, c_v.DEFAULT_KEY, uid)
                        if stat == rdr.OK:
                            print("Authentication with default key successful.")
                            # Step 2: Construct the new sector trailer block data
                            # The format is: Key A (6 bytes) + Access Bits (4 bytes) + Key B (6 bytes)
                            # Key A is our new key. We'll use the same for Key B for simplicity,
                            # The access bits are 4 bytes, but the MFRC522 library often expects a 16-byte block
                            # where the access bits and key B are combined.
                            # The format is Key A (6), Access Bits (4), Key B (6)
                            # The access bits are the 4 bytes after Key A.
                            # Let's create the 16-byte block data to write
                            block_data = c_v.CARD_KEY + ACCESS_BITS + c_v.CARD_KEY
                            # Step 3: Write the new sector trailer block
                            stat = rdr.write(sector_trailer_block, block_data)
                            if stat == rdr.OK:
                                print(f"Successfully wrote new key to sector trailer block {sector_trailer_block}.")
                            else:
                                print(f"Error writing to block {sector_trailer_block}: {stat}")
                            # Step 4: Stop the crypto session
                            rdr.stop_crypto1()
                        else:
                            print(f"Authentication with default key failed for block {sector_trailer_block}. Is this a new card?")
                            rdr.stop_crypto1()
                    print("\nProgramming complete. Please remove the card.")
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
