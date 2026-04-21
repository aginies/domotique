#!/usr/bin/env python3
import os
import struct
import hashlib

def pack_files_with_sha256(input_dir, output_bin):
    packed_data = bytearray()
    py_files = [f for f in os.listdir(input_dir) if f.endswith('.py') or f.endswith('.html')]
    py_files.append("VERSION")
    py_files.sort()

    for filename in py_files:
        filepath = os.path.join(input_dir, filename)
        with open(filepath, 'rb') as f:
            file_data = f.read()
        filename_bytes = filename.encode('utf-8')
        packed_data.extend(struct.pack('B', len(filename_bytes)))
        packed_data.extend(filename_bytes)
        packed_data.extend(struct.pack('<I', len(file_data)))
        packed_data.extend(file_data)

    sha256 = hashlib.sha256()
    sha256.update(packed_data)
    packed_data.extend(sha256.digest())

    with open(output_bin, 'wb') as out_file:
        out_file.write(packed_data)

    print(f"Packed {len(py_files)} files into {output_bin} (SHA256 included).")

import sys

if __name__ == "__main__":
    input_directory = sys.argv[1] if len(sys.argv) > 1 else "temp_solar_domotic"
    output_binary = "update.bin"
    pack_files_with_sha256(input_directory, output_binary)
