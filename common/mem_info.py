# antoine@ginies.org
# GPL3

import micropython
import machine
import gc

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
    freq_mhz = machine.freq() / 1000000
    return freq_mhz

def print_info():
    """ Print the info """ 
    mem_stats = get_memory_info()
    print(f"Memory Allocated: {mem_stats['allocated_bytes']} bytes")
    print(f"Memory Free: {mem_stats['free_bytes']} bytes")
    print(f"Total Heap: {mem_stats['total_heap_bytes']} bytes")
    print(f"Memory Usage: {mem_stats['allocated_percentage']:.2f}%")
    freq = show_freq()
    print(f"Current CPU frequency: {freq} MHz")
 

print_info()