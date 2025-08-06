# antoine@ginies.org
# GPL3

""" Domotique Utils """
import os
import gc
import micropython
import machine
import ntptime

def file_exists(file_path):
    """Check if a file exists"""
    try:
        os.stat(file_path)
        return True
    except OSError:
        return False

def set_time_with_ntp():
    try:
        print("Synchronizing time with NTP...")
        ntptime.settime()
        print("Time set successfully.")
    except OSError as err:
        print("Error setting time with NTP:", err)

def set_rtc():
    """ Set up the RTC object"""
    rtc = machine.RTC()
    return rtc

def show_rtc_time():
    rtc = machine.RTC()
    dt_tuple = rtc.datetime()
    hour = dt_tuple[4]
    minute = dt_tuple[5]
    second = dt_tuple[6]
    time_str = f"{hour:02}:{minute:02}:{second:02}"
    return time_str

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
    return {
        "allocated_bytes": total_alloc,
        "free_bytes": free_mem,
        "total_heap_bytes": total_heap,
        "allocated_percentage": (total_alloc / total_heap) * 100 if total_heap > 0 else 0
    }

def show_freq():
    """ Show the freq """
    freq_mhz = machine.freq() / 1000000
    return freq_mhz

def set_freq(freq):
    """
    Set the freq in MHz
    frequency must be 20MHz, 40MHz, 80Mhz, 160MHz or 240MHz
    """
    machine.freq(freq*1000000)

def print_info():
    """ Print the info """
    mem_stats = get_memory_info()
    print(f"Memory Allocated: {mem_stats['allocated_bytes']} bytes")
    print(f"Memory Free: {mem_stats['free_bytes']} bytes")
    print(f"Total Heap: {mem_stats['total_heap_bytes']} bytes")
    print(f"Memory Usage: {mem_stats['allocated_percentage']:.2f}%")
    freq = show_freq()
    print(f"Current CPU frequency: {freq} MHz")