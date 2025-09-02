#!/usr/bin/python3.13
import os
import struct
import hashlib

def pack_files_with_sha256(input_dir, output_bin):
    """
    Packs .py files from input_dir into a single binary file with SHA256.
    """
    packed_data = bytearray()

    # List all .py files in input_dir
    py_files = [f for f in os.listdir(input_dir) if f.endswith('.py')]
    py_files.append("VERSION")
    py_files.sort()

    for filename in py_files:
        filepath = os.path.join(input_dir, filename)
        with open(filepath, 'rb') as f:
            file_data = f.read()

        # Pack filename length (1 byte), filename (utf-8), file size (4 bytes, little-endian), file data
        filename_bytes = filename.encode('utf-8')
        packed_data.extend(struct.pack('B', len(filename_bytes)))  # Filename length
        packed_data.extend(filename_bytes)                         # Filename
        packed_data.extend(struct.pack('<I', len(file_data)))      # File size
        packed_data.extend(file_data)                              # File data

    # Calculate SHA256 hash of the packed data
    sha256 = hashlib.sha256()
    sha256.update(packed_data)
    digest = sha256.digest()

    # Append hash to the packed data
    packed_data.extend(digest)

    # Write the packed data to output file
    with open(output_bin, 'wb') as out_file:
        out_file.write(packed_data)

    print(f"Packed {len(py_files)} files into {output_bin} (SHA256 included).")

input_directory = "temp_pool_domotic"
output_binary = "update.bin"
pack_files_with_sha256(input_directory, output_binary)
