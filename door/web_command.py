# antoine@ginies.org
# GPL3

""" Web command page """
import config_var as c_v

def create_html_response():
    """ Créer la réponse HTML """
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contrôle</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            color: #333;
        }}
        .container {{
            text-align: center;
            background: white;
            padding: 20px 40px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }}
        h1 {{
            color: #444;
            margin-bottom: 30px;
        }}
        .button {{
            display: inline-block;
            margin: 10px;
            padding: 24px 40px;
            font-size: 20px;
            color: white;
            background-color: #007BFF;
            border: none;
            border-radius: 5px;
            text-decoration: none;
            cursor: pointer;
            transition: background-color 0.3s;
        }}
        .button:hover {{
            background-color: #0056b3;
        }}
        .button:disabled {{
            background-color: grey;
            cursor: not-allowed;
        }}
        .button.clicked {{
            background-color: red;
        }}
        .status {{
            margin: 20px auto;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background-color: 'green';
        }}
        .footer {{
            position: fixed;
            bottom: 10px;
            width: 100%;
            text-align: center;
            color: #fff;
            background-color: rgba(0, 0, 0, 0.5);
            padding: 10px;
        }}
        .footer-buttons {{
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-bottom: 0px;
        }}
        #timestamp {{
            margin-top: 20px;
            font-size: 16px;
            color: #555;
        }}
        .config-button {{
            display: block;
            padding: 8px 16px;
            font-size: 12px;
            color: white;
            background-color: #373837;
            border: none;
            border-radius: 5px;
            text-decoration: none;
            cursor: pointer;
            transition: background-color 0.3s;
        }}
        .config-button:hover {{
            background-color: #218838;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Contrôle """+c_v.DOOR+"""</h1>
        <p>Toujours <b>contrôler</b> visuellement le <b>"""+c_v.DOOR+"""</b></p>
        <button id="BP1" class="button">BP1</button>
        <div id="timestamp"></div>
        <div id="user-agent"></div>
    <script>
        document.getElementById('BP1').addEventListener('click', function() {
            fetch('/BP1_ACTIF', { method: 'POST' })
                .then(response => response.text())
                .then(data => console.log(data));
             setTimeout(() => {{
                button.classList.remove('clicked');
            }}, 1000);
            const userAgent = navigator.userAgent;
            document.getElementById('user-agent').textContent = 'User Agent: ' + navigator.userAgent;
            const now = new Date();
            const timestamp = now.toLocaleString();
            document.getElementById('timestamp').textContent = 'Dernier clic: ' + timestamp;
        });
    </script>
    </div>
    <div class="footer">
        <div class="footer-buttons">
            <a href="/web_config" target="_blank" class="config-button">Configurer</a>
            <a href="/livelog" target="_blank" class="config-button">Voir les Log</a>
            <a href="/file_management" target="_blank" class="config-button">Explorer</a>
            <a href="mailto:antoine@ginies.org" class="config-button">Antoine</a>
        </div>
    </div>
</body>
</html>"""
    return html
