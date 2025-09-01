import zipfile
import os
import domo_utils as d_u

def serve_ota_page():
    html_page = """
<!DOCTYPE html>
<html>
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
    </style>
<head>
    <title>OTA Update</title>
    <meta charset="utf-8">
</head>
<body>
<div class="container">
    <h1>Mise à jour OTA</h1>
    <div class="upload-form">
    <form action="/OTA_update" method="POST" enctype="multipart/form-data">
        <input type="file" name="file" accept=".zip">
        <button type="submit">Mettre à jour</button>
    </form>
    </div>
</div>
</body>
</html>
    """
    return html_page

def handle_ota_update(request):
    try:
        request_bytes = request
        boundary_start = request_bytes.find(b"boundary=")
        if boundary_start == -1:
            raise ValueError("Boundary non trouvé")

        boundary_end = request_bytes.find(b"\r\n", boundary_start)
        boundary = request_bytes[boundary_start + 9:boundary_end]

        data_start = request_bytes.find(b"\r\n\r\n", boundary_end) + 4
        data_end = request_bytes.find(b"\r\n--" + boundary, data_start)
        data = request_bytes[data_start:data_end]

        with open("update.zip", "wb") as f:
            f.write(data)

        with zipfile.ZipFile("update.zip", "r") as zip_ref:
            zip_ref.extractall("/")

        redirect_url = "/file_management"
        response_headers = [
            "HTTP/1.1 303 See Other",
            f"Location: {redirect_url}",
            "Connection: close",
            "",
        ]
        return "\r\n".join(response_headers)

    except Exception as err:
        print(f"Erreur : {err}")
        redirect_url = "/"
        response_headers = [
            "HTTP/1.1 500 Internal Server Error",
            "Content-Type: text/plain",
            f"Location: {redirect_url}",
            "Connection: close",
            "",
        ]
        return "\r\n".join(response_headers)