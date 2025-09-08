# antoine@ginies.org
# GPL3

import time
import domo_utils as d_u
import uos
import json
import socket

def handle_upload_simple(cl, socket, request, IP_ADDR):
    try:
        # Extract boundary
        #filename_encoded = path.split('/')[-1]
        #filename = d_u.url_decode(filename_encoded)
        #d_u.print_and_store_log(f"UPLOAD: Filename from URL: {filename}")
        boundary_start = request.find(b"boundary=")
        if boundary_start == -1:
            return "HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nBoundary non trouvé"
        boundary_end = request.find(b"\r\n", boundary_start)
        boundary = request[boundary_start + 9:boundary_end]
        closing_boundary = b"\r\n--" + boundary + b"--"

        filename_start = request.find(b'filename="', boundary_end) + 10
        filename_end = request.find(b'"', filename_start)
        filename = request[filename_start:filename_end].decode("utf-8")
        d_u.print_and_store_log(f"UPLOAD: Will Received File: {filename}")

        data_start = request.find(b"\r\n\r\n", filename_end) + 4
        body = request[data_start:]

        start_time = time.time()
        total_bytes = 0
        data_end = body.find(closing_boundary)
        if data_end != -1:
            with open(filename, "wb") as f:
                f.write(body[:data_end])
            d_u.print_and_store_log(f"UPLOAD: File uploaded successfully. Total bytes: {len(body[:data_end])}")
        else:
            with open(filename, "wb") as f:
                f.write(body)
                total_bytes = len(body)
                remaining = b""
                d_u.print_and_store_log(f"UPLOAD: Initial chunk: {len(body)} bytes. Waiting for more data...")
                counter = 0
                while True:
                    chunk = cl.recv(8192)
                    if not chunk:
                        d_u.print_and_store_log(f"UPLOAD: Connection closed before boundary found. Total bytes: {total_bytes}")
                        return "HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nBoundary non trouvé (connexion fermée)"

                    full_chunk = remaining + chunk
                    data_end = full_chunk.find(closing_boundary)

                    if data_end != -1:
                        f.write(full_chunk[:data_end])
                        total_bytes += len(full_chunk[:data_end])
                        #d_u.print_and_store_log(f"UPLOAD: Final chunk: {len(full_chunk[:data_end])} bytes. Total bytes: {total_bytes}")
                        break
                    else:
                        bytes_to_write = len(full_chunk) - len(closing_boundary)
                        if bytes_to_write > 0:
                            f.write(full_chunk[:bytes_to_write])
                            total_bytes += bytes_to_write
                        if counter == 15:
                            d_u.print_and_store_log(f"UPLOAD: Received {len(full_chunk)} bytes. Total so far: {total_bytes}. Waiting for more data...")
                            counter = 0
                        remaining = full_chunk[-len(closing_boundary):]
                        counter +=1

        end_time = time.time()
        elapsed_time = end_time - start_time
        d_u.print_and_store_log(f"UPLOAD: File uploaded successfully. Total bytes: {total_bytes}")
        if elapsed_time > 2:
            d_u.print_and_store_log(f"UPLOAD: Upload time for {filename}: {elapsed_time:.2f} seconds ({total_bytes / 1024 / elapsed_time:.2f} KB/s)")

        if filename == "update.bin":
            d_u.manage_update("/update.bin", "/update")

        redirect_url = (f"http://{IP_ADDR}/UPLOAD_server")
        response_headers = [
            "HTTP/1.1 303 See Other",
            f"Location: {redirect_url}",
            "Connection: close",
            "",
        ]
        response = "\r\n".join(response_headers)
        return response

    except Exception as err:
        d_u.print_and_store_log(f"UPLOAD: Erreur : {err}")
        return "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/plain\r\n\r\nErreur lors de l'upload"

def serve_file_upload_page(IP_ADDR, WS_PORT):
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Upload</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f4f4f9;
            color: #333;
        }}
        .container {{
            max-width: 800px;
            margin: auto;
            background-color: #fff;
            padding: 20px 40px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }}
        h1, h2 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        .button {{
            padding: 8px 12px;
            text-decoration: none;
            color: white;
            border-radius: 5px;
            display: inline-block;
            text-align: center;
        }}
        .upload-form {{
            margin-top: 20px;
            padding: 20px;
            background-color: #ecf0f1;
            border-radius: 8px;
        }}
        .log-display {{
            background-color: #ecf0f1;
            border: 1px solid #bdc3c7;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', Courier, monospace;
            white-space: pre-wrap;
            word-wrap: break-word;
            height: 300px;
            overflow-y: scroll;
        }}
        .upload-text {{
            color: green;
        }}
        .upload-status {{
            font-weight: bold;
            color: #3498db;
            margin-top: 10px;
        }}
        .upload-button {{
            padding: 10px 25px;
            border: none;
            background-color: #007bff;
            color: white;
            font-size: 16px;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }}
        .upload-button:hover {{
            background-color: #0056b3;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Upload a file</h1>
        <div class="upload-form">
            <form id="uploadForm" action="/upload_file" method="POST" enctype="multipart/form-data">
                <input type="file" id="fileInput" name="file_content">
                <input type="submit" value="Upload">
            </form>
        </div>
        <div class="container">
            <h2>Log.txt (slow update)</h2>
            <pre id="log-display"></pre>
        </div>
    </div>
    <script>
        const uploadForm = document.getElementById('uploadForm');
        const fileInput = document.getElementById('fileInput');
        const uploadServerUrl = 'http://{IP_ADDR}:{WS_PORT}';
        fileInput.addEventListener('change', () => {{
            const file = fileInput.files[0];
            if (file) {{
                const encodedFilename = encodeURIComponent(file.name);
                uploadForm.action = uploadServerUrl + '/upload/' + encodedFilename;
                console.log('Form action set to:', uploadForm.action);
            }}
        }});

        const getLogs = async () => {{
            try {{
                const response = await fetch('/get_log_upload');
                if (!response.ok) {{
                    throw new Error(`HTTP error! Status: ${{response.status}}`);
                }}
                const logData = await response.text();
                document.getElementById('log-display').textContent = logData || 'No logs found.';
            }} catch (error) {{
                console.error('Failed to fetch logs:', error);
                document.getElementById('log-display').textContent = 'Failed to load logs.';
            }}
        }};
        getLogs()
        setInterval(getLogs, 1000);
    </script>
</body>
</html>
"""
    return html
