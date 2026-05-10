from flask import Flask, request, jsonify, render_template_string
import json
import os

app = Flask(__name__)

COMMAND_PATH = '/tmp/matrix_command.json'
STATUS_PATH = '/tmp/matrix_status.json'

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Matrix Display Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: Arial, sans-serif; background: #111; color: #fff; padding: 20px; max-width: 400px; margin: 0 auto; }
        h1 { color: #1db954; text-align: center; margin-bottom: 5px; font-size: 24px; }
        .subtitle { color: #aaa; text-align: center; font-size: 13px; margin-bottom: 20px; }
        .card { background: #222; border-radius: 12px; padding: 15px; margin-bottom: 15px; }
        h2 { color: #1db954; font-size: 14px; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; }
        .now-playing { text-align: center; padding: 10px 0; }
        .track-name { font-size: 18px; font-weight: bold; margin-bottom: 5px; }
        .artist-name { color: #aaa; font-size: 14px; }
        .not-playing { color: #555; font-size: 14px; text-align: center; padding: 10px 0; }
        .btn { width: 100%; padding: 12px; border: none; border-radius: 8px; font-size: 15px; cursor: pointer; margin-bottom: 8px; font-weight: bold; transition: opacity 0.2s; }
        .btn:active { opacity: 0.7; }
        .btn-green { background: #1db954; color: white; }
        .btn-gray { background: #333; color: white; }
        .btn-red { background: #e74c3c; color: white; }
        .btn-yellow { background: #f39c12; color: white; }
        .btn-row { display: flex; gap: 8px; }
        .btn-row .btn { margin-bottom: 0; }
        .slider-row { display: flex; align-items: center; gap: 10px; }
        .slider-row input { flex: 1; accent-color: #1db954; }
        .slider-row span { color: #1db954; font-weight: bold; min-width: 35px; text-align: right; }
        .status { text-align: center; font-size: 12px; color: #555; margin-top: 15px; }
        .toast { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: #1db954; color: white; padding: 10px 20px; border-radius: 20px; font-size: 14px; display: none; }
    </style>
</head>
<body>
    <h1>🎵 Matrix Display</h1>
    <p class="subtitle">Control Panel</p>

    <div class="card">
        <h2>Now Playing</h2>
        <div id="now-playing" class="not-playing">Loading...</div>
    </div>

    <div class="card">
        <h2>Display</h2>
        <div class="btn-row" style="margin-bottom: 8px;">
            <button class="btn btn-green" onclick="sendCommand('undim')">💡 Full Brightness</button>
            <button class="btn btn-gray" onclick="sendCommand('dim')">🌙 Dim</button>
        </div>
        <button class="btn btn-gray" onclick="sendCommand('refresh')">🔄 Refresh Now Playing</button>
    </div>

    <div class="card">
        <h2>Brightness</h2>
        <div class="slider-row">
            <span>0</span>
            <input type="range" min="1" max="100" value="70" id="brightness-slider" oninput="updateBrightness(this.value)">
            <span id="brightness-value">70</span>
        </div>
    </div>

    <div class="card">
        <h2>Settings</h2>
        <input type="text" id="lastfm-username" placeholder="Last.fm Username" style="width:100%; padding:10px; border-radius:8px; border:none; margin-bottom:8px; font-size:15px;">
        <button class="btn btn-green" onclick="saveUsername()">💾 Save Username</button>
    </div>

    <div class="card">
        <h2>Power</h2>
        <button class="btn btn-red" onclick="confirmShutdown()">⏻ Safe Shutdown</button>
    </div>

    <div class="status" id="status">Connected</div>
    <div class="toast" id="toast"></div>

    <script>
        function showToast(msg) {
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.style.display = 'block';
            setTimeout(() => t.style.display = 'none', 2000);
        }

        function sendCommand(cmd, data={}) {
            fetch('/command', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: cmd, ...data})
            })
            .then(r => r.json())
            .then(d => showToast(d.message))
            .catch(() => showToast('Error sending command'));
        }

        function updateBrightness(val) {
            document.getElementById('brightness-value').textContent = val;
            sendCommand('brightness', {value: parseInt(val)});
        }

        function saveUsername() {
            const username = document.getElementById('lastfm-username').value.trim();
            if (!username) return showToast('Enter a username first');
            sendCommand('set_username', {username: username});
        }

        function confirmShutdown() {
            if (confirm('Are you sure you want to shut down the display?')) {
                sendCommand('shutdown');
                showToast('Shutting down...');
            }
        }

        function updateStatus() {
            fetch('/status')
            .then(r => r.json())
            .then(d => {
                const el = document.getElementById('now-playing');
                if (d.track) {
                    el.innerHTML = `<div class="now-playing"><div class="track-name">${d.track}</div><div class="artist-name">${d.artist}</div></div>`;
                } else {
                    el.innerHTML = '<div class="not-playing">Nothing playing</div>';
                }
                document.getElementById('status').textContent = d.dimmed ? '🌙 Display dimmed' : '💡 Display active';
                if (d.brightness) {
                    document.getElementById('brightness-slider').value = d.brightness;
                    document.getElementById('brightness-value').textContent = d.brightness;
                }
            })
            .catch(() => {
                document.getElementById('status').textContent = 'Connection lost';
            });
        }

        // Update status every 5 seconds
        updateStatus();
        setInterval(updateStatus, 5000);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/command', methods=['POST'])
def command():
    data = request.get_json()
    cmd = data.get('command')

    with open(COMMAND_PATH, 'w') as f:
        json.dump(data, f)

    messages = {
        'dim': 'Display dimmed',
        'undim': 'Brightness restored',
        'refresh': 'Refreshing now playing',
        'brightness': f"Brightness set to {data.get('value')}",
        'shutdown': 'Shutting down safely...',
        'set_username': f"Username updated to {data.get('username')}"
    }

    return jsonify({'status': 'ok', 'message': messages.get(cmd, 'Command sent')})

@app.route('/status')
def status():
    try:
        with open(STATUS_PATH, 'r') as f:
            return jsonify(json.load(f))
    except:
        return jsonify({'track': None, 'artist': None, 'dimmed': False, 'brightness': 70})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
