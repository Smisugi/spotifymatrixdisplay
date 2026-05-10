import os
import json
import subprocess
import time

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), '../config/settings.json')

def has_settings():
    try:
        with open(SETTINGS_PATH, 'r') as f:
            settings = json.load(f)
            return 'lastfm_username' in settings and 'wifi_ssid' in settings
    except:
        return False

def is_connected():
    try:
        import socket
        socket.setdefaulttimeout(3)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(('8.8.8.8', 53))
        return True
    except:
        return False

def wait_for_connection(timeout=60):
    print('Waiting for internet connection...')
    start = time.time()
    while time.time() - start < timeout:
        if is_connected():
            print('Connected!')
            return True
        time.sleep(5)
    print('No internet after timeout.')
    return False

def start_hotspot():
    print('No settings found, starting hotspot...')
    subprocess.run(['sudo', 'nmcli', 'connection', 'down', 'preconfigured'], capture_output=True)
    time.sleep(2)
    subprocess.run(['sudo', 'ip', 'addr', 'add', '192.168.4.1/24', 'dev', 'wlan0'], capture_output=True)
    subprocess.run(['sudo', 'ip', 'link', 'set', 'wlan0', 'up'], capture_output=True)

    hostapd_conf = """interface=wlan0
ssid=MatrixDisplay
hw_mode=g
channel=6
auth_algs=1
wpa=2
wpa_passphrase=matrix123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=CCMP
"""
    with open('/tmp/hostapd.conf', 'w') as f:
        f.write(hostapd_conf)

    subprocess.run(['sudo', 'systemctl', 'stop', 'dnsmasq'], capture_output=True)

    dnsmasq_conf = """interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
address=/#/192.168.4.1
"""
    with open('/tmp/dnsmasq.conf', 'w') as f:
        f.write(dnsmasq_conf)

    subprocess.Popen(['sudo', 'hostapd', '/tmp/hostapd.conf'])
    time.sleep(2)
    subprocess.Popen(['sudo', 'dnsmasq', '-C', '/tmp/dnsmasq.conf', '--no-daemon'])
    time.sleep(2)

    print('Hotspot active, starting portal...')
    os.execv('/usr/bin/python3', ['python3',
              os.path.join(os.path.dirname(__file__), 'portal.py')])

def start_display():
    print('Starting control panel...')
    subprocess.Popen(['sudo', 'python3',
                     os.path.join(os.path.dirname(__file__), 'control.py')])
    time.sleep(2)
    print('Starting display...')
    subprocess.Popen(['sudo', 'python3',
                     os.path.join(os.path.dirname(__file__), 'display.py')])
    # Keep start.py alive so the service doesn't exit
    while True:
        time.sleep(60)

if __name__ == '__main__':
    time.sleep(10)
    if not has_settings():
        start_hotspot()
    else:
        wait_for_connection(timeout=60)
        start_display()
