#!/usr/bin/python3.13
import os
import struct
import hashlib

def create_custom_bin(output_filename, directory_to_pack, files_to_pack):
    """
    Creates a custom binary file (.bin) with a header, table of contents, and file data.
    """
    files_to_archive = []
    
    # Add files from the specified directory
    if os.path.exists(directory_to_pack) and os.path.isdir(directory_to_pack):
        for root, _, filenames in os.walk(directory_to_pack):
            for filename in filenames:
                full_path = os.path.join(root, filename)
                relative_path = os.path.relpath(full_path, os.path.dirname(directory_to_pack))
                files_to_archive.append((full_path, relative_path))
    
    for file_path in files_to_pack:
        if os.path.exists(file_path):
            files_to_archive.append((file_path, os.path.basename(file_path)))

    if not files_to_archive:
        print("No files found to archive. Exiting.")
        return

    try:
        with open(output_filename, 'wb') as bin_file:
            print("Write the header: total number of files")
            num_files = len(files_to_archive)
            bin_file.write(struct.pack('<I', num_files)) # '<I' for little-endian unsigned int

            print("Build and write the Table of Contents (TOC)")
            file_data_bytes = b''
            for local_path, archive_name in files_to_archive:
                with open(local_path, 'rb') as f:
                    data = f.read()
                    
                filename_bytes = archive_name.encode('utf-8')
                filename_len = len(filename_bytes)
                file_size = len(data)

                # Write filename length, filename, and file size to the TOC
                bin_file.write(struct.pack('B', filename_len)) # 'B' for unsigned char (1 byte)
                bin_file.write(filename_bytes)
                bin_file.write(struct.pack('<I', file_size))

                # Store file data to be written after the TOC
                file_data_bytes += data

            print("Write the concatenated file data")
            bin_file.write(file_data_bytes)

        #h = hashlib.sha256()
        #h.update(file_data_bytes)
        #hash_digest = h.digest() # This returns the 32-byte binary hash
        #output_dir = os.path.dirname(output_filename)
        #if output_dir and not os.path.exists(output_dir):
        #    os.makedirs(output_dir)
        #with open(output_filename, 'wb') as bin_file:
        #    bin_file.write(file_data_bytes)
        #    bin_file.write(hash_digest)
        print(f"\nSuccessfully created '{output_filename}' with {num_files} files.")
        #print(f"SHA256 hash appended: {hash_digest.hex()}")

    except Exception as e:
        print(f"An error occurred: {e}")

def bytes_to_hex(bytes_data):
    """Convert bytes to a hexadecimal string."""
    return ''.join(['{:02x}'.format(b) for b in bytes_data])

def generate_sha256sums(directory):
    """
    Generate a 'sha256sum' file containing the SHA-256 checksums of all files in the specified directory.
    """
    try:
        with open(os.path.join(directory, "sha256sum"), "w") as sum_file:
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):  # Skip directories
                    sha256 = hashlib.sha256()
                    with open(filepath, "rb") as f:
                        while True:
                            chunk = f.read(4096)  # Read in chunks
                            if not chunk:
                                break
                            sha256.update(chunk)
                    calculated_digest = sha256.digest()
                    checksum = bytes_to_hex(calculated_digest)
                    sum_file.write(f"{checksum}  {filename}\n")
        print(f"sha256sum file created in {directory}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    temp_pool_domotic_dir = 'temp_pool_domotic'
    
    #current_dir_py_files = [
    #    f for f in os.listdir('.') 
    #    if f.endswith('.py') and os.path.isfile(f)
    #]
    current_dir_py_files = "" 
    output_file = 'update.bin'
    create_custom_bin(output_file, temp_pool_domotic_dir, current_dir_py_files)
    generate_sha256sums(temp_pool_domotic_dir)
