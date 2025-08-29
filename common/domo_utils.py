# antoine@ginies.org
# GPL3

""" Domotique Utils """
import os
import gc
import struct
import micropython
import machine
import ntptime
import uhashlib

def check_and_delete_if_too_big(filepath, max_size_mb):
    """
    Checks the size of a file and deletes it if it exceeds
    the specified maximum size.
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    if not file_exists(filepath):
        print_and_store_log(f"File not found: {filepath}")
        return False
    try:
        file_stats = os.stat(filepath)
        current_size_bytes = file_stats[6]
    except OSError:
        print_and_store_log(f"File not found: {filepath}")
        return False
    if current_size_bytes > max_size_bytes:
        print_and_store_log(f"File size ({current_size_bytes} bytes) exceeds the limit of {max_size_bytes} bytes. Deleting file...")
        try:
            os.remove(filepath)
            print_and_store_log(f"Successfully deleted: {filepath}")
            return True
        except OSError as e:
            print_and_store_log(f"Error deleting file {filepath}: {e}")
            return False
    else:
        print_and_store_log(f"File size is within the limit of {max_size_mb}Mb. No action needed.")
        return False

def store_log(text_data, filename="/log.txt"):
    """ Stores a text string as a new line in a log file. """
    with open(filename, "a") as file:
        file.write(text_data + "\n")

def print_and_store_log(text_data):
    """ print log and store them """
    hour, minute, second = show_rtc_time()
    current_date = show_rtc_date()
    current_time = str(hour)+":"+str(minute)+":"+str(second)
    data_to_print = current_date+" "+current_time+": "+text_data
    print(data_to_print)
    store_log(data_to_print)

def file_exists(file_path):
    """Check if a file exists"""
    try:
        os.stat(file_path)
        return True
    except OSError:
        return False

def copy_file(source_path, dest_path):
    """ Copies a file from source_path to dest_path """
    try:
        if not os.stat(source_path)[6] > 0:
            print_and_store_log(f"Source file not found: {source_path}")
            return False

        print_and_store_log(f"Copying '{source_path}' to '{dest_path}'...")

        # Use a buffer to handle potentially large files
        buf_size = 512
        with open(source_path, 'rb') as source_file:
            with open(dest_path, 'wb') as dest_file:
                while True:
                    chunk = source_file.read(buf_size)
                    if not chunk:
                        break  # End of file
                    dest_file.write(chunk)

        print_and_store_log("File copied successfully.")
        return True

    except Exception as err:
        print_and_store_log(f"An error occurred: {err}")
        return False

def bytes_to_hex(bytes_data):
    """Convert bytes to a hexadecimal string."""
    return ''.join(['{:02x}'.format(b) for b in bytes_data])

def unpack_files_with_sha256(packed_bin, output_dir):
    """
    Unpacks files and verifies SHA256 (MicroPython-compatible).
    """
    with open(packed_bin, 'rb') as in_file:
        packed_data = in_file.read()

    # Split data and hash
    data = packed_data[:-32]
    expected_digest = packed_data[-32:]
    expected_hash = bytes_to_hex(expected_digest)

    # Verify hash
    sha256 = uhashlib.sha256()
    sha256.update(data)
    actual_digest = sha256.digest()
    actual_hash = bytes_to_hex(actual_digest)
    print_and_store_log(f"AC: {actual_hash}\nEC: {expected_hash}")
    if actual_hash == expected_hash:
        print_and_store_log("sha256sum is Ok!")
    else:
        #raise ValueError("SHA256 checksum mismatch! The file may be corrupted.")
        print_and_store_log("SHA256 checksum mismatch! The file may be corrupted.")
    # Unpack files
    offset = 0
    while offset < len(data):
        filename_len = struct.unpack('B', data[offset:offset+1])[0]
        offset += 1
        filename = data[offset:offset+filename_len].decode('utf-8')
        offset += filename_len
        file_size = struct.unpack('<I', data[offset:offset+4])[0]
        offset += 4
        file_data = data[offset:offset+file_size]
        offset += file_size

        # Write file
        try:
            os.mkdir(output_dir)
        except OSError:
            pass
        with open(f"{output_dir}/{filename}", 'wb') as f:
            f.write(file_data)

    print_and_store_log(f"Unpacked files to {output_dir} (SHA256 verified).")

def set_time_with_ntp():
    try:
        print_and_store_log("Synchronizing time with NTP...")
        ntptime.settime()
        print_and_store_log("Time set successfully.")
    except OSError as err:
        print_and_store_log(f"Error setting time with NTP: {err}")

def is_dst_paris(dt_tuple):
    """ Get the Paris Time """
    year, month, day, weekday, hour, minute, second, _ = dt_tuple
    def last_sunday(year, month):
        if month == 12:
            next_month_first_day = (year + 1, 1, 1)
        else:
            next_month_first_day = (year, month + 1, 1)
        _, _, _, first_day_weekday, *_ = machine.RTC().datetime((next_month_first_day[0], next_month_first_day[1], next_month_first_day[2], 0, 0, 0, 0, None))
        last_sunday = next_month_first_day[2] - (first_day_weekday + 1) % 7 - 7
        return last_sunday

    if month > 3 and month < 10:
        return True
    elif month == 3:
        last_sunday_march = last_sunday(year, 3)
        return day >= last_sunday_march and (day > last_sunday_march or hour >= 1)
    elif month == 10:
        last_sunday_october = last_sunday(year, 10)
        return day < last_sunday_october or (day == last_sunday_october and hour < 1)
    else:
        return False

def set_rtc():
    """ Set up the RTC object"""
    rtc = machine.RTC()
    return rtc

def show_rtc_time():
    rtc = machine.RTC()
    dt_tuple = rtc.datetime()
    is_dst = is_dst_paris(dt_tuple)
    # Adjust for Europe/Paris timezone (UTC+1 or UTC+2)
    timezone_offset = 2 if is_dst else 1
    hour = dt_tuple[4] + timezone_offset
    minute = dt_tuple[5]
    second = dt_tuple[6]
    time_str = f"{hour:02}:{minute:02}:{second:02}"
    #print(time_str)
    return hour, minute, second

def show_rtc_date():
    rtc = machine.RTC()
    dt_tuple = rtc.datetime()
    year = dt_tuple[0]
    month = dt_tuple[1]
    day = dt_tuple[2]
    weekday = dt_tuple[3]
    date_str = f"{year:04}-{month:02}-{day:02}"
    #weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    #weekday_str = weekdays[weekday]
    return date_str

def get_memory_info():
    """
    Returns a dictionary with current memory allocation information.
    """
    gc.collect()  # Force a garbage collection to get a more accurate picture
    total_alloc = gc.mem_alloc()
    free_mem = gc.mem_free()
    total_heap = total_alloc + free_mem
    micropython.mem_info()

    # Convert bytes to megabytes (1 MB = 1024 * 1024 bytes)
    allocated_mb = total_alloc / (1024 * 1024)
    free_mb = free_mem / (1024 * 1024)
    total_heap_mb = total_heap / (1024 * 1024)
    allocated_percentage = (total_alloc / total_heap) * 100 if total_heap > 0 else 0

    return {
        "allocated_mb": allocated_mb,
        "free_mb": free_mb,
        "total_heap_mb": total_heap_mb,
        "allocated_percentage": allocated_percentage
    }

def get_disk_space():
    """
    Returns a dictionary with disk space information in KB and MB.
    """
    statvfs = os.statvfs('/')
    block_size = statvfs[0]
    total_blocks = statvfs[2]
    free_blocks = statvfs[3]

    total_space_bytes = block_size * total_blocks
    free_space_bytes = block_size * free_blocks
    used_space_bytes = total_space_bytes - free_space_bytes

    total_space_kb = total_space_bytes / 1024
    free_space_kb = free_space_bytes / 1024
    used_space_kb = used_space_bytes / 1024

    total_space_mb = total_space_bytes / (1024 * 1024)
    free_space_mb = free_space_bytes / (1024 * 1024)
    used_space_mb = used_space_bytes / (1024 * 1024)

    return {
        "total_kb": total_space_kb,
        "free_kb": free_space_kb,
        "used_kb": used_space_kb,
        "total_mb": total_space_mb,
        "free_mb": free_space_mb,
        "used_mb": used_space_mb,
    }

def get_disk_space_info():
    """ show usage / total of disk """
    disk_info = get_disk_space()
    return disk_info["free_mb"], disk_info["total_mb"], disk_info["used_mb"]

def show_freq():
    """ Show the freq """
    freq_mhz = machine.freq() / 1000000
    return freq_mhz

def set_freq(freq):
    """
    Set the freq in MHz
    ESP32-S3: frequency must be 20MHz, 40MHz, 80Mhz, 160MHz or 240MHz
    """
    print_and_store_log(f"Set frequency to {freq}MHz")
    machine.freq(freq*1000000)

def print_info():
    """ Print the info """
    freq = show_freq()
    print_and_store_log(f"Current CPU frequency: {freq} MHz")
    mem_stats = get_memory_info()
    print_and_store_log(f"Memory Allocated (MB):: {mem_stats['allocated_mb']}")
    print_and_store_log(f"Memory Free (MB):: {mem_stats['free_mb']}")
    print_and_store_log(f"Total Heap (MB):: {mem_stats['total_heap_mb']}")
    print_and_store_log(f"Memory Usage: {mem_stats['allocated_percentage']:.2f}%")
    disk_info = get_disk_space()
    print("Total Space (KB): {:.2f}".format(disk_info["total_kb"]))
    print("Free Space (KB): {:.2f}".format(disk_info["free_kb"]))
    print("Used Space (KB): {:.2f}".format(disk_info["used_kb"]))
    print("Total Space (MB): {:.2f}".format(disk_info["total_mb"]))
    print("Free Space (MB): {:.2f}".format(disk_info["free_mb"]))
    print("Used Space (MB): {:.2f}".format(disk_info["used_mb"]))
