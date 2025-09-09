# antoine@ginies.org
# GPL3

import os
import time
import domo_utils as d_u

def serve_file_management_page():
    """Get a list of all files in the root directory and generate the HTML page."""
    free_mb, total_mb, used_mb = d_u.get_disk_space_info()
    used_percentage = ((total_mb - free_mb) / total_mb) * 100
    files = os.listdir()
    file_table_rows = ""
    for file in files:
        try:
            file_stats = os.stat(file)
            if file == "config_var.py":
                file_table_rows += f"""
                <tr>
                    <td>{file}</td>
                    <td>{formatted_date}</td>
                    <td>{file_size_kb} KB</td>
                    <td>
                    </td>
                </tr>
                """
            elif file_stats[0] & 0o170000 == 0o100000:
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
            width: 40%;
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
        .warning-text {{
            color: red;
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
    </div>
    <div class="container">
        <div>
            <a href="/UPLOAD_server" target="_blank" class="upload-button">Upload</a>
        </div>
    </div>
    <script>
        const usedPercentage = {used_percentage};
        document.getElementById('diskBar').style.width = usedPercentage + '%';
        const CHUNK_SIZE = 16384; // 16KB chunks
        let socket;
        let fileId;
        function connectWebSocket() {{
            socket = new WebSocket("ws://" + window.location.host + "/ws");
            socket.onopen = () => {{
                console.log("WebSocket connected");
            }};
            socket.onmessage = (event) => {{
                const message = JSON.parse(event.data);
                console.log("Server:", message.message);
                if (message.type === "complete") {{
                    alert("File uploaded successfully!");
                }}
            }};
            socket.onclose = ()            => {{
                console.log("WebSocket disconnected");
            }};
            socket.onerror = (error) => {{
                console.error("WebSocket error:", error);
            }};
        }}
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
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        pre code.hljs {{
            padding: 1em;
        }}
        .hljs-ln-numbers {{
            text-align: center;
            color: #ccc;
            border-right: 1px solid #999;
            vertical-align: top;
            padding-right: 5px !important;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>View File: {file_path}</h1>
        <a href="/file_management">← Back to File Management</a>
        <pre><code class="language-python">{escaped_content}</code></pre>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>    <!-- Initialize Highlight.js -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlightjs-line-numbers.js/2.8.0/highlightjs-line-numbers.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', (event) => {{
            if (typeof hljs !== 'undefined') {{
                hljs.highlightAll();
                 hljs.initLineNumbersOnLoad();
                console.log("Highlight.js and lines number initialized and applied.");
            }} else {{
                console.error("Highlight.js not loaded!");
            }}
        }});
    </script>
</body>
</html>
"""
    return html
