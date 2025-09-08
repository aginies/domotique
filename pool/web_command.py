# antoine@ginies.org
# GPL3

""" Main HTML Web interface """
import domo_utils as d_u
import config_var as c_v

def create_html_response():
    """ Créer la réponse HTML """
    emergency_exists = d_u.file_exists("/EMERGENCY_STOP")
    bp1_exists = d_u.file_exists('/BP1')
    disabled1 = "disabled" if bp1_exists else ""
    bp2_exists = d_u.file_exists('/BP2')
    disabled2 = "disabled" if bp2_exists else ""
    disabled_open_b = "disabled" if emergency_exists else ""
    disabled_close_b = "disabled" if emergency_exists else ""
    disabled3 = "disabled" if emergency_exists else ""
    BUTTON_DISABLED = "style='background-color: grey;'"
    button_style1 = BUTTON_DISABLED if bp1_exists else ""
    button_style2 = BUTTON_DISABLED if bp2_exists else ""
    button_style3 = BUTTON_DISABLED if emergency_exists else ""
    button_style_open_b = BUTTON_DISABLED if emergency_exists else ""
    button_style_close_b = BUTTON_DISABLED if emergency_exists else ""
    PIN_CODE = c_v.PIN_CODE
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contrôle {c_v.DOOR}</title>
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
        .small-button {{
            padding: 24px 40px;
            font-size: 12px;
            background-color: #007BFF;
            border: none;
            color: white;
            border-radius: 5px;
            text-decoration: none;
            cursor: pointer;
            margin: 10px;
            transition: background-color 0.3s;
        }}  
        .button-small:hover {{
            background-color: #138496; /* Darker blue on hover */
        }}
        .button-group {{
            display: flex;
            justify-content: center;
            align-items: stretch;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }}
        .button {{
            display: inline-block;
            margin: 8px;
            flex-grow: 1;
            padding: 20px 34px;
            font-size: 16px;
            color: white;
            background-color: #007BFF;
            border: none;
            border-radius: 5px;
            text-decoration: none;
            cursor: pointer;
            transition: background-color 0.3s;
        }}
        .button-small {{
            text-decoration: none;
            margin: 4px;
            padding: 14px 10px;
            border: none;
            cursor: pointer;
            color: white;
            border-radius: 5px;
            font-size: 12px;
            transition: background-color 0.3s;
            background-color: #17A2B8;
        }}
        .button:hover {{
            background-color: #0056b3;
        }}
        .button:disabled {{
            background-color: grey;
            cursor: not-allowed;
        }}
        .button.clicked {{
            background-color: red !important;
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
        #timestamp {{
            margin-top: 20px;
            font-size: 16px;
            color: #555;
        }}
        .emergency-button {{
            display: block;
            margin: 20px auto 0;
            padding: 15px 30px;
            font-size: 18px;
            color: white;
            background-color: #DC3545; /* Red color for emergency */
            border: none;
            border-radius: 5px;
            text-decoration: none;
            cursor: pointer;
            transition: background-color 0.3s;
            width: fit-content;
        }}
        .emergency-button:hover {{
            background-color: #C82333;
        }}
        .emergency-button:disabled {{
            background-color: grey;
            cursor: not-allowed;
        }}
        .reboot-message {{
            margin-top: 25px;
            padding: 15px 20px;
            background-color: #ffdddd; /* Light red background */
            color: #d8000c; /* Darker red text */
            border: 1px solid #d8000c;
            border-radius: 5px;
            font-weight: bold;
            text-align: center;
            font-size: 1.1em;
            display: none;
        }}
        /* Progress Bar Styles */
        .progress-container {{
            width: 370px;
            background-color: #f3f3f3;
            border-radius: 5px;
            overflow: hidden;
            height: 30px;
            margin-left: 20px;
            margin-top: 20px;
            border: 1px solid #ddd;
            margin-left: auto;
            margin-right: auto;
            display: block;
        }}
        .progress-bar {{
            width: 0%;
            height: 100%;
            background-color: #007BFF;
            text-align: center;
            line-height: 30px;
            color: white;
            font-size: 14px;
            transition: width 0.05s linear;
        }}
        .config-button {{
            display: inline-block;
            padding: 8px 16px;
            font-size: 10px;
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
        .config-button-s {{
            display: inline-block;
            padding: 8px 16px;
            font-size: 8px;
            color: white;
            background-color: #373837;
            border: none;
            border-radius: 5px;
            text-decoration: none;
            cursor: pointer;
            transition: background-color 0.3s;
        }}
        .config-button-s:hover {{
            background-color: #218838;
        }}
        .footer-buttons {{
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-bottom: 0px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Contrôle {c_v.DOOR}</h1>
        <p>Toujours <b>contrôler</b> visuellement la <b>{c_v.DOOR}</b></p>
        <div id="progressBarContainer" class="progress-container">
            <div id="progressBar" class="progress-bar">0%</div>
        </div>
        <div class="button-group">
            <button id="BP1" class="button" {disabled1} {button_style1}>{c_v.nom_bp1}</button>
            <button id="BP2" class="button" {disabled2} {button_style2}>{c_v.nom_bp2}</button>
        </div>
        <div class="button-group">
            <button id="OPEN_B" class="button-small" {disabled_open_b} {button_style_open_b}>{c_v.nom_open_b} {c_v.time_adjust}sec</button>
            <button id="CLOSE_B" class="button-small" {disabled_close_b} {button_style_close_b}>{c_v.nom_close_b} {c_v.time_adjust}sec</button>
        </div>
        <div>
            <pre id="log-display"></pre>
        </div>
        <button id="emergencyStop" class="emergency-button" {disabled3} {button_style3}>Arrêt d'Urgence</button>
        <!--<div id="timestamp"></div>-->
        <div id="rebootMessage" class="reboot-message">
            Le dispositif nécessite un redémarrage !
        </div>
    </div>
    <div class="footer">
        <div class="footer-buttons">
            <a href="/web_config" target="_blank" class="config-button">Configurer</a>
            <a href="/livelog" target="_blank" class="config-button">Voir les Log</a>
            <a href="/file_management" target="_blank" class="config-button">Explorer</a>
            <a href="mailto:antoine@ginies.org" class="config-button">Antoine</a>
            <a href="/revert_mode" target="_blank" class="config-button-s">Revert</a>
    </div>
    </div>
    <script>
document.addEventListener('DOMContentLoaded', function() {{
    const TIME_TO_OPEN_MS = {c_v.time_to_open} * 1000; // Converti en millisecondes
    const TIME_TO_CLOSE_MS = {c_v.time_to_close} * 1000; // Converti en millisecondes
    const PIN_CODE = "{PIN_CODE}"; // Code PIN pour la fermeture

    const progressBarContainer = document.getElementById('progressBarContainer');
    const progressBar = document.getElementById('progressBar');
    const rebootMessageDiv = document.getElementById('rebootMessage');
    const emergencyButton = document.getElementById('emergencyStop');
    const bp1Button = document.getElementById('BP1');
    const bp2Button = document.getElementById('BP2');
    const open_bButton = document.getElementById('OPEN_B');
    const close_bButton = document.getElementById('CLOSE_B');
    const logContainer = document.getElementById('log-display');
    const timestampElement = document.getElementById('timestamp');

    let currentProgressBarInterval = null; // Pour gérer l'animation en cours
    let emergencyActiveClient = false; // État d'urgence côté client
    progressBar.style.width = '100%';
    progressBar.textContent = '100%';
    function animateProgressBar(durationMs, startPercent, endPercent) {{
        if (currentProgressBarInterval) {{
            clearInterval(currentProgressBarInterval);
        }}

        const startTime = Date.now();
        let lastRenderedPercent = startPercent;

        const updateBar = () => {{
            const elapsedTime = Date.now() - startTime;
            const progressFraction = Math.min(elapsedTime / durationMs, 1); // Limite à 1 (100%)

            let currentPercent;
            if (startPercent < endPercent) {{
                currentPercent = startPercent + (endPercent - startPercent) * progressFraction;
            }} else {{
                currentPercent = startPercent - (startPercent - endPercent) * progressFraction;
            }}

            if (Math.abs(currentPercent - lastRenderedPercent) >= 0.5 || progressFraction === 1) {{
                progressBar.style.width = `${{currentPercent.toFixed(0)}}%`;
                progressBar.textContent = `${{currentPercent.toFixed(0)}}%`;
                lastRenderedPercent = currentPercent;
            }}

            if (progressFraction >= 1) {{
                clearInterval(currentProgressBarInterval);
                currentProgressBarInterval = null;
                // Force l'état final pour éviter les arrondis
                progressBar.style.width = `${{endPercent.toFixed(0)}}%`;
                progressBar.textContent = `${{endPercent.toFixed(0)}}%`;
            }}
        }};

        if (durationMs === 0) {{
            updateBar();
            return;
        }}

        currentProgressBarInterval = setInterval(updateBar, 50); // Rafraîchit toutes les 50ms
    }}

    const getLogs = async () => {{
        try {{
            const response = await fetch('/get_log_action');
            if (!response.ok) {{
                throw new Error(`HTTP error! Status: ${{response.status}}`);
            }}
            const logData = await response.text();
            console.log("Log data:", logData); // Debug log
            document.getElementById('log-display').textContent = logData || 'No logs found.';
        }} catch (error) {{
            console.error('Failed to fetch logs:', error);
            document.getElementById('log-display').textContent = 'Failed to load logs.';
        }}
    }};

    const updateStatus = async () => {{
        try {{
            const response = await fetch('/status');
            if (!response.ok) {{
                throw new Error(`HTTP error! Status: ${{response.status}}`);
            }}
            const data = await response.json();
            console.log("Status update:", data);

            emergencyActiveClient = data.Emergency_stop;

            if (data.Emergency_stop) {{
                rebootMessageDiv.style.display = 'block';
                disableAllButtons(true);
            }} else {{
                rebootMessageDiv.style.display = 'none';
                emergencyButton.disabled = false;
                emergencyButton.style.backgroundColor = '#DC3545';

                if (!data.In_progress) {{
                    if (data.BP1_active) {{
                        bp1Button.disabled = true;
                        bp1Button.style.backgroundColor = 'grey';
                        bp2Button.disabled = false;
                        bp2Button.style.backgroundColor = '#007BFF';
                        open_bButton.disabled = false;
                        open_bButton.style.backgroundColor = '#007BFF';
                        close_bButton.disabled = false;
                        close_bButton.style.backgroundColor = '#007BFF';
                    }} else if (data.BP2_active) {{
                        bp2Button.disabled = true;
                        bp2Button.style.backgroundColor = 'grey';
                        bp1Button.disabled = false;
                        bp1Button.style.backgroundColor = '#007BFF';
                        open_bButton.disabled = false;
                        open_bButton.style.backgroundColor = '#007BFF';
                        close_bButton.disabled = false;
                        close_bButton.style.backgroundColor = '#007BFF';
                    }} else {{
                        bp1Button.disabled = false;
                        bp1Button.style.backgroundColor = '#007BFF';
                        bp2Button.disabled = false;
                        bp2Button.style.backgroundColor = '#007BFF';
                        open_bButton.disabled = false;
                        open_bButton.style.backgroundColor = '#007BFF';
                        close_bButton.disabled = false;
                        close_bButton.style.backgroundColor = '#007BFF';
                    }}
                }} else if (data.BP1_active) {{
                    disableAllButtons(true, ['BP2', 'CLOSE_B', 'OPEN_B']);
                }} else if (data.BP2_active) {{
                    disableAllButtons(true, ['BP1'], 'CLOSE_B', 'OPEN_B');
                }}
            }}
        }} catch (error) {{
            console.error('Error fetching status:', error);
        }}
    }};

    function disableAllButtons(disable, exceptions = []) {{
        const buttons = [bp1Button, bp2Button, open_bButton, close_bButton];
        buttons.forEach(button => {{
            if (!exceptions.includes(button.id)) {{
                button.disabled = disable;
                button.style.backgroundColor = disable ? 'grey' : '#007BFF';
            }}
        }});
    }}

    function handleButtonClick(buttonId, endpoint, requiresPin = false) {{
        const button = document.getElementById(buttonId);
        if (!button || button.disabled) return;

        button.classList.add('clicked');
        setTimeout(() => button.classList.remove('clicked'), 300);

        if (buttonId === 'BP2' && requiresPin) {{
            const pin = prompt("Pour fermer, entrer le code PIN:");
            if (pin !== PIN_CODE) {{
                alert("Code PIN incorrect. Le volet ne se fermera pas.");
                return;
            }}
        }}

        if (buttonId === 'BP1') {{
            animateProgressBar(TIME_TO_OPEN_MS, 0, 100);
            disableAllButtons(true);
        }} else if (buttonId === 'BP2') {{
            animateProgressBar(TIME_TO_CLOSE_MS, 100, 0);
            disableAllButtons(true);
        }}

        fetch(endpoint, {{ method: 'POST' }})
            .then(response => {{
                if (!response.ok) {{
                    throw new Error('Network response was not ok');
                }}
                return response.text();
            }})
            .then(data => {{
                console.log("Server response:", data);
                if (timestampElement) {{
                    timestampElement.textContent = new Date().toLocaleString();
                }}
                getLogs();
                updateStatus();
            }})
            .catch(error => {{
                console.error('Fetch error:', error);
                updateStatus();
            }});
    }}

    function handleEmergencyStop() {{
        console.log("Emergency Stop triggered!");
        disableAllButtons(true);
        emergencyButton.disabled = true;
        emergencyButton.style.backgroundColor = 'grey';

        if (currentProgressBarInterval) {{
            clearInterval(currentProgressBarInterval);
            currentProgressBarInterval = null;
        }}

        fetch('/EMERGENCY_STOP', {{ method: 'POST' }})
            .then(response => {{
                if (!response.ok) {{
                    throw new Error('Failed to send emergency stop');
                }}
                return response.text();
            }})
            .then(data => {{
                console.log("Emergency Stop response:", data);
                getLogs();
                updateStatus();
            }})
            .catch(error => {{
                console.error('Error:', error);
                updateStatus();
            }});
    }}

    bp1Button.addEventListener('click', () => handleButtonClick('BP1', '/BP1_ACTIF'));
    open_bButton.addEventListener('click', () => handleButtonClick('OPEN_B', '/OPEN_B_ACTIF'));
    close_bButton.addEventListener('click', () => handleButtonClick('CLOSE_B', '/CLOSE_B_ACTIF'));
    bp2Button.addEventListener('click', () => handleButtonClick('BP2', '/BP2_ACTIF', true));
    emergencyButton.addEventListener('click', handleEmergencyStop);
    updateStatus();
    getLogs()
    setInterval(updateStatus, 1000); // Met à jour le statut toutes les secondes
}});
    </script>
</body>
</html>"""
    return html
