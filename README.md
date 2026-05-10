# Matrix Display

<img width="4000" height="3000" alt="matrixdisplay" src="https://github.com/user-attachments/assets/d300ecee-5b15-49f3-ad7e-20171c16a028" />

A Raspberry Pi Zero W RGB LED matrix display that shows the current Spotify track's album art via Last.fm scrobbling. No Spotify API setup required — just a free Last.fm account connected to Spotify. Includes a web control panel accessible from any device on the same network.

## Hardware
- Raspberry Pi Zero W
- Adafruit RGB Matrix Bonnet
- 32x32 RGB LED Matrix Panel
- 5V 4A Power Supply
- MicroSD Card

## How It Works
- On first boot with no settings, the Pi creates a WiFi hotspot called **MatrixDisplay** (password: matrix123)
- Connect to it and a setup page appears automatically
- Enter your home WiFi credentials and Last.fm username
- The Pi reboots and starts displaying album art automatically
- If internet drops, the Pi waits and retries without going into hotspot mode
- After 2 minutes of nothing playing, the display dims automatically as a screensaver
- When a track starts playing again, the display restores to full brightness automatically

## Project Structure
matrixdisplay/
├── python/
│   ├── start.py              # Entry point, decides hotspot or display mode
│   ├── display.py            # Main display loop, fetches Last.fm and shows album art
│   ├── portal.py             # Flask web portal for WiFi and Last.fm setup
│   └── control.py            # Web control panel served on port 8080
├── config/
│   ├── options.ini           # RGB matrix hardware configuration
│   └── settings.json         # WiFi and Last.fm settings (created after setup)
├── images/
│   └── default.png           # Default image shown when nothing is playing
└── README.md

## Dependencies
- Python 3
- flask
- requests
- Pillow (PIL)
- hostapd
- dnsmasq
- rpi-rgb-led-matrix (Adafruit fork)

## Web Control Panel
Once the display is running, access the control panel from any device on the same network:
http://matrixdisplay.local:8080
Or via IP address:
http://192.168.x.x:8080

### Control Panel Features
- **Now Playing** — shows current track and artist updated every 5 seconds
- **Refresh Now Playing** — force refresh the current track
- **Brightness Slider** — adjust display brightness from 1 to 100
- **Set Brightness** — apply the selected brightness to the display
- **Last.fm Username** — change the Last.fm username without reconfiguring
- **Restart Display** — restart the display service
- **Safe Shutdown** — safely power off the Pi

### macOS Note
If the control panel is unreachable on Mac, check **System Settings → Privacy & Security → Local Network** and allow your browser access. Alternatively use the IP address directly or use Safari.

## Screensaver
The display automatically dims after 2 minutes of no playback to a very low brightness. When a track starts playing again the display restores to full brightness and shows the new album art automatically.

## Fresh Install / Recovery Steps

### 1. Flash SD Card
- Use Raspberry Pi Imager
- Choose Raspberry Pi OS Legacy Lite 32-bit
- Set hostname: `matrixdisplay`, username, password, WiFi and enable SSH in settings
- Country: AU

### 2. SSH In and Update
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3-pip python3-flask hostapd dnsmasq libopenjp2-7 python3-pil
sudo pip install requests flask --break-system-packages
```

### 3. Install RGB Matrix Library
```bash
curl https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/rgb-matrix.sh > rgb-matrix.sh
sudo bash rgb-matrix.sh
```
Choose **Convenience** and **Adafruit HAT/Bonnet** when prompted. Reboot after.

### 4. Install Python Bindings
```bash
cd ~/rpi-rgb-led-matrix/bindings/python
sudo python3 setup.py install
```

### 5. Clone This Repo
```bash
git clone https://github.com/Smisugi/spotifymatrixdisplay.git ~/matrixdisplay
```

### 6. Set Up Systemd Service
```bash
cat > /tmp/matrixdisplay.service << 'SERVICE'
[Unit]
Description=Matrix Display Service
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=python3 /home/pi/matrixdisplay/python/start.py
WorkingDirectory=/home/pi/matrixdisplay
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
User=root

[Install]
WantedBy=multi-user.target
SERVICE
sudo cp /tmp/matrixdisplay.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable matrixdisplay
sudo systemctl start matrixdisplay
```

### 7. Fix Permissions
```bash
sudo chmod 755 /home/pi
sudo chmod -R 777 /home/pi/matrixdisplay
```

## Configuration

### RGB Matrix (config/options.ini)
```ini
[DEFAULT]
rows = 32
columns = 32
chain_length = 1
parallel = 1
hardware_mapping = adafruit-hat
gpio_slowdown = 2
brightness = 70
refresh_rate = 60
default_image = ../images/default.png
```

### Settings (config/settings.json)
Created automatically after portal setup, or manually:
```json
{
    "lastfm_username": "their_lastfm_username",
    "wifi_ssid": "their_wifi_network"
}
```


## Setup Instructions
1. Plug in the display
2. On your phone connect to WiFi network called **MatrixDisplay** (password: `matrix123`)
3. A setup page will appear — enter your home WiFi and Last.fm username
4. Wait 2-3 minutes for the display to restart and connect
5. Play something on Spotify — album art appears within 30-60 seconds
6. Access the control panel from any device on your network at `http://matrixdisplay.local:8080`

## Control Panel Usage
- Open `http://matrixdisplay.local:8080` in your browser
- Adjust brightness using the slider and click **Set Brightness**
- Change Last.fm username if needed and click **Save Username**
- Use **Restart Display** if the display stops responding
- Use **Safe Shutdown** before unplugging to prevent SD card corruption

## Notes
- The display is designed to run 24/7 — safe to leave on
- Power consumption is approximately 1-2W for the Pi plus the matrix panel
- Album art updates within 30-60 seconds of a track change on Spotify
- Last.fm scrobbling must be connected to Spotify at last.fm/settings/applications
- If WiFi changes, delete settings.json and restart to trigger setup portal again
- Always use Safe Shutdown or `sudo shutdown -h now` before unplugging
- If SD card corrupts, use this repo to recover — see Fresh Install steps above
