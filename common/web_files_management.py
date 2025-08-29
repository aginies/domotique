import os
import time
import domo_utils as d_u

def handle_upload(cl, socket, request):
    d_u.print_and_store_log("DEUBG Test upload")
    try:
        boundary_start = request.find(b"boundary=")
        if boundary_start == -1:
            return "HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nBoundary non trouvé"

        boundary_end = request.find(b"\r\n", boundary_start)
        boundary = request[boundary_start + 9:boundary_end]

        filename_start = request.find(b'filename="', boundary_end) + 10
        filename_end = request.find(b'"', filename_start)
        filename = request[filename_start:filename_end].decode("utf-8")
        d_u.print_and_store_log(f"Fichier reçu : {filename}")

        data_start = request.find(b"\r\n\r\n", filename_end) + 4
        body = request[data_start:]

        boundary_close = b"\r\n--" + boundary
        data_end = body.find(boundary_close)
        start_time = time.time()
        total_bytes = 0
        with open(filename, "wb") as f:
            if data_end != -1:
                f.write(body[:data_end])
                total_bytes += len(body[:data_end])
            else:
                f.write(body)
                total_bytes += len(body)
                remaining = b""

                while True:
                    chunk = cl.recv(8192)
                    if not chunk:
                        d_u.print_and_store_log(f"Connection closed before boundary found. Total bytes: {total_bytes}")
                        return "HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\n\r\nBoundary non trouvé (connexion fermée)"

                    full_chunk = remaining + chunk
                    data_end = full_chunk.find(boundary_close)

                    if data_end != -1:
                        f.write(full_chunk[:data_end])
                        total_bytes += len(full_chunk[:data_end])
                        break
                    else:
                        f.write(full_chunk)
                        total_bytes += len(full_chunk)
                        remaining = full_chunk[-len(boundary_close):]
                        d_u.print_and_store_log(f"From {filename}, Received: {len(full_chunk)} bytes (chunk size)")

        end_time = time.time()
        elapsed_time = end_time - start_time
        d_u.print_and_store_log(f"File uploaded successfully. Total bytes: {total_bytes}")
        if elapsed_time > 2:
            d_u.print_and_store_log(f"Upload time for {filename}: {elapsed_time:.2f} seconds ({total_bytes / 1024 / elapsed_time:.2f} KB/s)")

        if filename == "update.bin":
            manage_update("update.bin", "/test")

        return "HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n"

    except Exception as err:
        d_u.print_and_store_log(f"Erreur : {err}")
        return "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/plain\r\n\r\nErreur lors de l'upload"

def manage_update(filename, output_dir):
    """ Function to extract filename bin """
    d_u.print_and_store_log(f"Update detected! Extracting")
    try:
        d_u.unpack_files_with_sha256(filename, output_dir)
        d_u.print_and_store_log(f"Successfully extracted {filename}")
        #os.remove(filename)
        #d_u.print_and_store_log(f"Deleted {filename} after extraction")
    except Exception as err:
        d_u.print_and_store_log(f"Failed to extract {filename}: {err}")

def serve_file_management_page():
    """Get a list of all files in the root directory and generate the HTML page."""
    free_mb, total_mb, used_mb = d_u.get_disk_space_info()
    used_percentage = ((total_mb - free_mb) / total_mb) * 100
    files = os.listdir()
    file_table_rows = ""
    for file in files:
        try:
            file_stats = os.stat(file)
            if file_stats[0] & 0o170000 == 0o100000:
                file_mod_timestamp = file_stats[8]
                file_size_bytes = file_stats[6]
                file_mod_date = time.localtime(file_mod_timestamp)
                formatted_date = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
                    file_mod_date[0], file_mod_date[1], file_mod_date[2],
                    file_mod_date[3], file_mod_date[4], file_mod_date[5]
                )
                file_size_kb = round(file_size_bytes / 1024, 2)

                file_table_rows += f"""
                <tr>
                    <td>{file}</td>
                    <td>{formatted_date}</td>
                    <td>{file_size_kb} KB</td>
                    <td>
                        <a href="/view?file={file}" class="button view-button">View</a>
                        <a href="/delete?file={file}" class="button delete-button" onclick="return confirm('Are you sure you want to delete this file?');">Delete</a>
                    </td>
                </tr>
                """
            elif file == "config_var.py":
                file_table_rows += f"""
                <tr>
                    <td>{file}</td>
                    <td>{formatted_date}</td>
                    <td>{file_size_kb} KB</td>
                    <td>
                    </td>
                </tr>
                """
            else:
                file_table_rows += f"""
                <tr>
                    <td>{file} (Directory)</td>
                    <td>{formatted_date}</td>
                    <td>{file_size_kb} KB</td>
                    <td>
                    </td>
                </tr>
                """
        except OSError:
            continue

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Management</title>
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
        .disk-info {{
            background: #f0f8ff;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .disk-bar-container {{
            width: 100%;
            background: #ecf0f1;
            border-radius: 5px;
            margin: 10px 0;
            overflow: hidden;
        }}
        .disk-bar {{
            height: 20px;
            background: #3498db;
            width: 40%; /* This will be set dynamically via JavaScript */
            border-radius: 5px;
        }}
        .disk-stats {{
            display: flex;
            justify-content: space-between;
            font-size: 0.9em;
            color: #7f8c8d;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: #fff;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .button {{
            padding: 8px 12px;
            text-decoration: none;
            color: white;
            border-radius: 5px;
            display: inline-block;
            text-align: center;
        }}
        .delete-button {{
            background-color: #e74c3c;
        }}
        .delete-button:hover {{
            background-color: #c0392b;
        }}
        .upload-form {{
            margin-top: 20px;
            padding: 20px;
            background-color: #ecf0f1;
            border-radius: 8px;
        }}
        .download-button {{
            background-color: #27ae60;
        }}
        .download-button:hover {{
            background-color: #219653;
        }}
        .view-button {{
            background-color: #3498db;
        }}
        .view-button:hover {{
            background-color: #2980b9;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>File Management</h1>
        <div class="disk-info">
            <div>
                <strong>Disk Space:</strong>
                <span id="diskUsageText">{used_mb:.2f} MB / {total_mb:.2f} MB used</span>
            </div>
        </div>
        <div class="disk-bar-container">
            <div class="disk-bar" id="diskBar" style="width: {used_percentage}%;"></div>
        </div>
        <div class="disk-stats">
            <span>{free_mb:.2f} MB free</span>
            <span>{used_percentage:.1f}% used</span>
        </div>
        <h2>Current Files</h2>
        <table>
            <thead>
                <tr>
                    <th>Filename</th>
                    <th>Last Modified</th>
                    <th>Size (KB)</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {file_table_rows}
            </tbody>
        </table>
        </div>
    <div class="container">
        <h1>Upload a file</h1>
        <div class="upload-form">
        <form action="/UPLOAD_file" method="POST" enctype="multipart/form-data">
            <input type="file" name="file" accept=".py,.txt,.bin">
            <button type="submit">Upload</button>
        </form>
        </div>
    </div>
    <script>
        const usedPercentage = {used_percentage};
        document.getElementById('diskBar').style.width = usedPercentage + '%';
    </script>
</body>
</html>
"""
    return html

def create_view_file_page(file_path):
    """Generate an HTML page to display the content of a file with Python syntax highlighting."""
    try:
        with open(file_path, 'r') as file:
            content = file.read()
    except OSError:
        content = f"<p>Unable to read file: {file_path}</p>"

    # Escape HTML special characters to prevent XSS
    escaped_content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>View File: {file_path}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/github-dark.min.css">
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
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        pre {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>View File: {file_path}</h1>
        <a href="/file_management">← Back to File Management</a>
        <pre><code class="language-python">{escaped_content}</code></pre>
    </div>
    <!-- Load Highlight.js from local -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>    <!-- Initialize Highlight.js -->
    <script>
        // Wait for DOM to be fully loaded
        document.addEventListener('DOMContentLoaded', (event) => {{
            if (typeof hljs !== 'undefined') {{
                hljs.highlightAll();
                console.log("Highlight.js initialized and applied.");
            }} else {{
                console.error("Highlight.js not loaded!");
            }}
        }});
    </script>
</body>
</html>
"""
    return html
