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
    # print it in hexadecimal format for easy reading
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
        d_u.print_and_store_log("MFRC522 initialized. Waiting for a card...")
        return rdr
    except Exception as err:
        d_u.print_and_store_log(f"An error occurred: {err}")

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
                    d_u.print_and_store_log("Card detected!")
                    d_u.print_and_store_log("UID: " + rdr.tohexstring(uid))
                    utime.sleep(2)
            utime.sleep(0.5)

def update_authorized_cards(new_uid):
    """
    Reads config_var.py, adds a new UID to AUTHORIZED_CARDS if not
    already present, and overwrites the file with the updated list.
    """
    config_path = 'config_var.py'
    try:
        authorized_cards = list(c_v.AUTHORIZED_CARDS)
    except AttributeError:
        authorized_cards = []

    if new_uid in authorized_cards:
        d_u.print_and_store_log(f"UID {new_uid} is already in AUTHORIZED_CARDS. No changes made.")
        return False

    authorized_cards.append(new_uid)
    d_u.print_and_store_log(f"New UID {new_uid} will be added to the list.")

    formatted_cards_list = "AUTHORIZED_CARDS = [\n"
    for card in authorized_cards:
        formatted_cards_list += f"    [{', '.join(hex(i) for i in card)}],\n"
    formatted_cards_list += "]\n"

    try:
        with open(config_path, 'r') as f:
            lines = f.readlines()

        variable_found = False
        with open(config_path, 'w') as f:
            for line in lines:
                if line.strip().startswith('AUTHORIZED_CARDS'):
                    f.write(formatted_cards_list)
                    variable_found = True
                else:
                    f.write(line)

            if not variable_found:
                f.write("\n" + formatted_cards_list)

        d_u.print_and_store_log("Successfully updated config_var.py!")
        return True

    except Exception as err:
        d_u.print_and_store_log(f"Error updating config_var.py: {err}")
        return False

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
                    d_u.print_and_store_log("\nCard detected!")
                    d_u.print_and_store_log("UID: " + rdr.tohexstring(uid))
                    block_addr = 4
                    stat = rdr.auth(rdr.AUTHENT1A, block_addr, c_v.CARD_KEY, uid)

                    if stat == rdr.OK:
                        d_u.print_and_store_log("Authentication successful!")
                        if uid in c_v.AUTHORIZED_CARDS:
                            d_u.print_and_store_log(">>> ACCESS AUTORISE <<<")
                            # data = rdr.read(block_addr)
                            # print("Data on card:", data)
                        else:
                            d_u.print_and_store_log(">>> ACCESS REFUSE - UID NON AUTORISE <<<")
                    else:
                        d_u.print_and_store_log(">>> ACCESS REFUSE - AUTHENTICATION FAILED <<<")
                    rdr.stop_crypto1()
                    utime.sleep(3)
            utime.sleep(0.5)

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
        d_u.print_and_store_log("Failed to initialize MFRC522 reader.")
        return

    d_u.print_and_store_log("MFRC522 initialized. Place a new card on the reader to enroll it...")

    while True:
        (stat, tag_type) = rdr.request(rdr.REQIDL)
        if stat == rdr.OK:
            (stat, uid) = rdr.SelectTagSN()
            if stat == rdr.OK:
                d_u.print_and_store_log("Card detected! UID: " + str(uid))
                if not _update_authorized_cards(uid):
                    d_u.print_and_store_log("Please remove the card and try another.")
                    utime.sleep(3)
                    continue
                d_u.print_and_store_log("Now programming the card with a new secure key...")
                all_sectors_programmed = True
                for sector_trailer_block in SECTOR_TRAILER_BLOCKS:
                    d_u.print_and_store_log(f"Attempting to program sector trailer block {sector_trailer_block}...")
                    stat = rdr.auth(rdr.AUTHENT1A, sector_trailer_block, c_v.DEFAULT_KEY, uid)
                    if stat == rdr.OK:
                        d_u.print_and_store_log("Authentication with default key successful.")
                        block_data = c_v.CARD_KEY + ACCESS_BITS + c_v.CARD_KEY
                        stat = rdr.write(sector_trailer_block, block_data)
                        if stat == rdr.OK:
                            d_u.print_and_store_log(f"Successfully wrote new key to sector trailer block {sector_trailer_block}.")
                        else:
                            d_u.print_and_store_log(f"Error writing to block {sector_trailer_block}: {stat}")
                            all_sectors_programmed = False
                    else:
                        d_u.print_and_store_log(f"Authentication failed for block {sector_trailer_block}. Is this a new card?")
                        all_sectors_programmed = False
                    rdr.stop_crypto1()
                if all_sectors_programmed:
                    d_u.print_and_store_log("Enrollment and programming complete! You can now use this card.")
                else:
                    d_u.print_and_store_log("Programming failed on one or more sectors. The card may not work correctly.")
                
                d_u.print_and_store_log("Please remove the card.")
                utime.sleep(4)
                d_u.print_and_store_log("Waiting for the next card...")
        utime.sleep(0.5)

def program_rfid_card():
    """
    Initializes the MFRC522 sensor, waits for a card, and programs it with a new
    secure key on specified sector trailer blocks.
    """
    rdr = init_mfrc5322()
    ACCESS_BITS = [0xFF, 0x07, 0x80]
    SECTOR_TRAILER_BLOCKS = [7, 11]
    if rdr:
        d_u.print_and_store_log("MFRC522 initialized. Please place a new card on the reader to program it...")
        while True:
            (stat, tag_type) = rdr.request(rdr.REQIDL)
            if stat == rdr.OK:
                (stat, uid) = rdr.SelectTagSN()
                if stat == rdr.OK:
                    d_u.print_and_store_log("Card detected! UID: " + rdr.tohexstring(uid))
                    # Loop through the sectors we want to program
                    for sector_trailer_block in SECTOR_TRAILER_BLOCKS:
                        d_u.print_and_store_log(f"Attempting to program sector trailer block {sector_trailer_block}...")
                        # Step 1: Authenticate with the default key (which the card has by default)
                        stat = rdr.auth(rdr.AUTHENT1A, sector_trailer_block, c_v.DEFAULT_KEY, uid)
                        if stat == rdr.OK:
                            d_u.print_and_store_log("Authentication with default key successful.")
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
                                d_u.print_and_store_log(f"Successfully wrote new key to sector trailer block {sector_trailer_block}.")
                            else:
                                d_u.print_and_store_log(f"Error writing to block {sector_trailer_block}: {stat}")
                            # Step 4: Stop the crypto session
                            rdr.stop_crypto1()
                        else:
                            d_u.print_and_store_log(f"Authentication with default key failed for block {sector_trailer_block}. Is this a new card?")
                            rdr.stop_crypto1()
                    d_u.print_and_store_log("\nProgramming complete. Please remove the card.")
                    utime.sleep(3)
            utime.sleep(0.5)
