# antoine@ginies.org
# GPL3

import domo_utils as d_u
import config_var as c_v
import utime
import os
from mfrc522 import MFRC522
from machine import Pin

def generate_6bytes():
    # Generate a 6-byte key as a bytes object
    key_bytes = os.urandom(6)
    CARD_KEY = list(key_bytes)
    d_u.print_and_store_log("Generated 6-byte key:", CARD_KEY)
    d_u.print_and_store_log("Generated hex key:", key_bytes.hex())

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
        d_u.print_and_store_log("RFID: MFRC522 initialized. Waiting for a card...")
        return rdr
    except Exception as err:
        d_u.print_and_store_log(f"RFID: An error occurred: {err}")

def update_authorized_cards(new_uid):
    """
    Adds a new card UID to the AUTHORIZED_CARDS list in config_var.py.
    """
    if new_uid in c_v.AUTHORIZED_CARDS:
        d_u.print_and_store_log(f"RFID: This card is already authorized. No changes made.")
        return False
    hex_parts = []
    for b in new_uid:
        hex_parts.append('0x' + "{:02X}".format(b))
    formatted_uid_line = f"    [{', '.join(hex_parts)}],\n"

    try:
        with open('config_var.py', 'r') as f:
            lines = f.readlines()
        insertion_point = -1
        for i in range(len(lines) - 1, -1, -1):
            if ']' in lines[i]:
                insertion_point = i
                break
        if insertion_point == -1:
            d_u.print_and_store_log("RFID Error: Could not find the closing bracket of AUTHORIZED_CARDS.")
            return False
        lines.insert(insertion_point, formatted_uid_line)
        with open('config_var.py', 'w') as f:
            for line in lines:
               f.write(line)

        d_u.print_and_store_log(f"RFID: Successfully added new card UID: {new_uid}")
        return True

    except Exception as err:
        d_u.print_and_store_log(f"RFID: An error occurred while updating the file: {err}")
        return False

def enroll_new_card():
    """
    Initializes the MFRC522 sensor, waits for a card, adds its UID to
    the authorized list in config_var.py, and then programs the card
    with a new secure key.
    """
    ACCESS_BITS = [0xFF, 0x07, 0x80, 0x69] # Standard 4 bytes for access bits
    SECTOR_TRAILER_BLOCKS = [7, 11]
    rdr = init_mfrc5322()
    if not rdr:
        d_u.print_and_store_log("RFID: Failed to initialize MFRC522 reader.")
        return
    d_u.print_and_store_log("RFID: MFRC522 initialized. Place a new card on the reader to enroll it...")
    while True:
        (stat, tag_type) = rdr.request(rdr.REQIDL)
        if stat == rdr.OK:
            (stat, uid) = rdr.SelectTagSN()
            if stat == rdr.OK:
                hex_uid = ' '.join([hex(i) for i in uid])
                d_u.print_and_store_log(f"RFID: Card detected! Hex UID: " + str({hex_uid}))
                if not update_authorized_cards(uid):
                    d_u.print_and_store_log("RFID: Please remove the card and try another.")
                    utime.sleep(3)
                    continue
                d_u.print_and_store_log("RFID: Now programming the card with a new secure key...")
                all_sectors_programmed = True
                for sector_trailer_block in SECTOR_TRAILER_BLOCKS:
                    d_u.print_and_store_log(f"RFID: Attempting to program sector trailer block {sector_trailer_block}...")
                    stat = rdr.auth(rdr.AUTHENT1A, sector_trailer_block, c_v.CARD_KEY, uid)
                    if stat == rdr.OK:
                        d_u.print_and_store_log("RFID: Authentication with default key successful.")
                        block_data = c_v.CARD_KEY + ACCESS_BITS + c_v.CARD_KEY
                        stat = rdr.write(sector_trailer_block, block_data)
                        if stat == rdr.OK:
                            d_u.print_and_store_log(f"RFID: Successfully wrote new key to sector trailer block {sector_trailer_block}.")
                        else:
                            d_u.print_and_store_log(f"RFID: Error writing to block {sector_trailer_block}: {stat}")
                            all_sectors_programmed = False
                    else:
                        d_u.print_and_store_log(f"RFID: Authentication failed for block {sector_trailer_block}. Is this a new card?")
                        all_sectors_programmed = False
                    rdr.stop_crypto1()
                if all_sectors_programmed:
                    d_u.print_and_store_log("RFID: Enrollment and programming complete! You can now use this card.")
                else:
                    d_u.print_and_store_log("RFID: Programming failed on one or more sectors. The card may not work correctly.")
                
                d_u.print_and_store_log("RFID: Please remove the card.")
                utime.sleep(4)
                d_u.print_and_store_log("RFID: Waiting for the next card...")
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
                    d_u.print_and_store_log("RFID: Card detected!")
                    d_u.print_and_store_log("RFID: UID: " + rdr.tohexstring(uid))
                    block_addr = 4
                    stat = rdr.auth(rdr.AUTHENT1A, block_addr, c_v.CARD_KEY, uid)

                    if stat == rdr.OK:
                        d_u.print_and_store_log("RFID: Authentication successful!")
                        if uid in c_v.AUTHORIZED_CARDS:
                            d_u.print_and_store_log("RFID: >>> ACCESS AUTORISE <<<")
                            # data = rdr.read(block_addr)
                            # print("Data on card:", data)
                        else:
                            d_u.print_and_store_log("RFID: >>> ACCESS REFUSE - UID NON AUTORISE <<<")
                    else:
                        d_u.print_and_store_log("RFID: >>> ACCESS REFUSE - AUTHENTICATION FAILED <<<")
                    rdr.stop_crypto1()
                    utime.sleep(3)
            utime.sleep(0.5)