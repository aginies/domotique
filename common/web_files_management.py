import os
import time

def serve_file_management_page():
    """Get a list of all files in the root directory and generate the HTML page."""
    files = os.listdir()
    file_table_rows = ""
    for file in files:
        try:
            file_stats = os.stat(file)
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
                    <a href="/delete?file={file}" class="button delete-button" onclick="return confirm('Are you sure you want to delete this file?');">Delete</a>
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
    </style>
</head>
<body>
    <div class="container">
        <h1>File Management</h1>
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

        <h2>Upload a File</h2>
        <div class="upload-form">
            <form action="/upload" method="POST" enctype="multipart/form-data">
                <input type="file" name="file_upload" style="margin-right: 10px;">
                <input type="submit" value="Upload File" class="button">
            </form>
        </div>
    </div>
</body>
</html>
"""
    return html