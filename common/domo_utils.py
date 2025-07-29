""" Domotique Utils """
import os

def file_exists(file_path):
    """Check if a file exists"""
    try:
        os.stat(file_path)
        return True
    except OSError:
        return False