#!/usr/bin/python3.13
import os
import struct

def unpack_update_bin(input_filename, output_directory):
    """ Unpacks a udpate binary file """
    if not os.stat(input_filename):
        print(f"Error: The file '{input_filename}' does not exist.")
        return
        
    try:
        os.mkdir(output_directory)
    except OSError:
        pass

    try:
        with open(input_filename, 'rb') as bin_file:
            print("Read the header: total number of files")
            num_files_bytes = bin_file.read(4)
            if len(num_files_bytes) < 4:
                print("Error: Incomplete file header.")
                return
            num_files = struct.unpack('<I', num_files_bytes)[0]

            print(f"Unpacking {num_files} files from '{input_filename}'...")
            print("Read the Table of Contents (TOC)")
            file_metadata = []
            for _ in range(num_files):
                # Read filename length
                filename_len_bytes = bin_file.read(1)
                if not filename_len_bytes:
                    print("Error: Incomplete file metadata.")
                    return
                filename_len = struct.unpack('B', filename_len_bytes)[0]

                # Read filename
                filename_bytes = bin_file.read(filename_len)
                if len(filename_bytes) < filename_len:
                    print("Error: Incomplete filename data.")
                    return
                filename = filename_bytes.decode('utf-8')

                # Read file size
                file_size_bytes = bin_file.read(4)
                if len(file_size_bytes) < 4:
                    print("Error: Incomplete file size data.")
                    return
                file_size = struct.unpack('<I', file_size_bytes)[0]

                file_metadata.append({'name': filename, 'size': file_size})
            
            for meta in file_metadata:
                print(f"{meta['name']} {meta['size']} Bytes")

            for meta in file_metadata:
                file_data = bin_file.read(meta['size'])
                if len(file_data) < meta['size']:
                    print(f"Error: Incomplete data for file '{meta['name']}'.")
                    continue

                output_path = output_directory+"/"+meta['name']
                # Create subdirectories if the filename contains path separators
                parts = output_path.split('/')
                directory_parts = parts[:-1]
                directory = '/'.join(directory_parts)
                try:
                    os.mkdir(directory)
                except OSError:
                    pass
                
                with open(output_path, 'wb') as output_file:
                    output_file.write(file_data)
                
                print(f"  Unpacked: {output_path} ({meta['size']} bytes)")

        print(f"\nSuccessfully unpacked all files to '{output_directory}'.")

    except Exception as err:
        print(f"An error occurred: {err}")

if __name__ == '__main__':
    unpack_update_bin('update.bin', 'unpacked_files')
