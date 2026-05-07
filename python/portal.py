from flask import Flask, request, redirect, render_template_string
import json
import os
import subprocess
import threading

app = Flask(__name__)

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), '../config/settings.json')

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Matrix Display Setup</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; max-width: 400px; margin: 40px auto; padding: 20px; background: #111; color: #fff; }
        h1 { color: #1db954; text-align: center; }
        input { width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; border: none; box-sizing: border-box; font-size: 16px; }
        button { width: 100%; padding: 12px; background: #1db954; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
        button:hover { background: #17a349; }
        .section { background: #222; padding: 15px; border-radius: 8px; margin: 15px 0; }
        h2 { color: #1db954; font-size: 16px; }
        .success { color: #1db954; text-align: center; font-size: 18px; }
        .hint { color: #aaa; font-size: 12px; margin-top: 5px; }
    </style>
</head>
<body>
    <h1>🎵 Matrix Display</h1>
    {% if success %}
    <div class="section">
        <p class="success">✅ Setup complete! Your display will restart in a few seconds.</p>
    </div>
    {% else %}
    <form method="POST" action="/save">
        <div class="section">
            <h2>📶 Wi-Fi Settings</h2>
            <input type="text" name="wifi_ssid" placeholder="Wi-Fi Network Name" required>
            <input type="password" name="wifi_password" placeholder="Wi-Fi Password" required>
        </div>
        <div class="section">
            <h2>🎵 Last.fm Settings</h2>
            <input type="text" name="lastfm_username" placeholder="Last.fm Username" required>
            <p class="hint">Don't have Last.fm? Create a free account at last.fm and connect your Spotify at last.fm/settings/applications</p>
        </div>
        <button type="submit">Save & Connect</button>
    </form>
    {% endif %}
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML, success=False)

@app.route('/save', methods=['POST'])
def save():
    wifi_ssid = request.form.get('wifi_ssid')
    wifi_password = request.form.get('wifi_password')
    lastfm_username = request.form.get('lastfm_username')

    settings = {
        'lastfm_username': lastfm_username,
        'wifi_ssid': wifi_ssid
    }
    with open(SETTINGS_PATH, 'w') as f:
        json.dump(settings, f)

    # Connect to new wifi then reboot
    def connect_and_reboot():
        subprocess.run(['sudo', 'nmcli', 'device', 'wifi', 'connect',
                       wifi_ssid, 'password', wifi_password])
        subprocess.run(['sudo', 'reboot'])

    threading.Timer(3, connect_and_reboot).start()
    return render_template_string(HTML, success=True)

# Captive portal redirects
@app.route('/generate_204')
@app.route('/hotspot-detect.html')
@app.route('/ncsi.txt')
@app.route('/connecttest.txt')
def captive():
    return redirect('http://192.168.4.1/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
