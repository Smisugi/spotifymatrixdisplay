import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from io import BytesIO
from PIL import Image
from rgbmatrix import RGBMatrix, RGBMatrixOptions
import configparser
import os
import json
import subprocess

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../config/options.ini')
SETTINGS_PATH = os.path.join(os.path.dirname(__file__), '../config/settings.json')
DEFAULT_IMAGE = os.path.join(os.path.dirname(__file__), '../images/default.png')
COMMAND_PATH = '/tmp/matrix_command.json'
STATUS_PATH = '/tmp/matrix_status.json'

def load_settings():
    try:
        with open(SETTINGS_PATH, 'r') as f:
            return json.load(f)
    except:
        return None

def save_settings(settings):
    with open(SETTINGS_PATH, 'w') as f:
        json.dump(settings, f)

def config_brightness():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    return int(config['DEFAULT']['brightness'])

def get_matrix():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    options = RGBMatrixOptions()
    options.rows = int(config['DEFAULT']['rows'])
    options.cols = int(config['DEFAULT']['columns'])
    options.chain_length = int(config['DEFAULT']['chain_length'])
    options.parallel = int(config['DEFAULT']['parallel'])
    options.hardware_mapping = config['DEFAULT']['hardware_mapping']
    options.gpio_slowdown = int(config['DEFAULT']['gpio_slowdown'])
    options.brightness = int(config['DEFAULT']['brightness'])
    options.limit_refresh_rate_hz = int(config['DEFAULT']['refresh_rate'])
    options.drop_privileges = False
    return RGBMatrix(options=options)

def get_session():
    session = requests.Session()
    retry = Retry(total=5, backoff_factor=2)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def get_now_playing(username, session):
    api_key = "8ab94dddcc50331f32b1011ae1ee11da"
    url = f'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={username}&api_key={api_key}&format=json&limit=1'
    try:
        response = session.get(url, timeout=10)
        data = response.json()
        tracks = data['recenttracks']['track']
        if not tracks:
            return None
        if isinstance(tracks, dict):
            tracks = [tracks]
        track = tracks[0]
        if '@attr' not in track or track['@attr'].get('nowplaying') != 'true':
            return None
        artist = track['artist']['#text']
        name = track['name']
        image_url = None
        for img in track['image']:
            if img['size'] == 'large' and img['#text']:
                image_url = img['#text']
                break
        return {'artist': artist, 'name': name, 'image_url': image_url}
    except Exception as e:
        print(f'Error fetching now playing: {e}')
        return None

def show_image(matrix, image_url, session):
    try:
        if image_url:
            response = session.get(image_url, timeout=10)
            image = Image.open(BytesIO(response.content))
        else:
            image = Image.open(DEFAULT_IMAGE)
        image = image.resize((matrix.width, matrix.height), Image.Resampling.LANCZOS)
        matrix.SetImage(image.convert('RGB'))
    except Exception as e:
        print(f'Error showing image: {e}')
        image = Image.open(DEFAULT_IMAGE)
        image = image.resize((matrix.width, matrix.height), Image.Resampling.LANCZOS)
        matrix.SetImage(image.convert('RGB'))

def show_default(matrix):
    image = Image.open(DEFAULT_IMAGE)
    image = image.resize((matrix.width, matrix.height), Image.Resampling.LANCZOS)
    matrix.SetImage(image.convert('RGB'))

def write_status(track, artist, dimmed, brightness):
    try:
        with open(STATUS_PATH, 'w') as f:
            json.dump({
                'track': track,
                'artist': artist,
                'dimmed': dimmed,
                'brightness': brightness
            }, f)
    except:
        pass

def read_command():
    try:
        with open(COMMAND_PATH, 'r') as f:
            cmd = json.load(f)
        os.remove(COMMAND_PATH)
        return cmd
    except:
        return None

def main():
    print('Starting matrix display...')
    settings = load_settings()
    if not settings or 'lastfm_username' not in settings:
        print('No settings found, waiting...')
        matrix = get_matrix()
        show_default(matrix)
        while True:
            settings = load_settings()
            if settings and 'lastfm_username' in settings:
                break
            time.sleep(5)

    username = settings['lastfm_username']
    print(f'Using Last.fm username: {username}')
    matrix = get_matrix()
    session = get_session()
    prev_track = None
    not_playing_since = None
    dimmed = False
    current_brightness = config_brightness()
    DIM_AFTER_SECONDS = 120
    DIM_BRIGHTNESS = 5

    while True:
        try:
            # Check for commands from control panel
            cmd = read_command()
            if cmd:
                command = cmd.get('command')
                print(f'Received command: {command}')

                if command == 'dim':
                    matrix.brightness = DIM_BRIGHTNESS
                    dimmed = True
                    show_default(matrix)

                elif command == 'undim':
                    matrix.brightness = current_brightness
                    dimmed = False
                    prev_track = None

                elif command == 'brightness':
                    current_brightness = cmd.get('value', 70)
                    if not dimmed:
                        matrix.brightness = current_brightness
                        if prev_track is not None:
                            track = get_now_playing(username, session)
                            if track:
                                show_image(matrix, track['image_url'], session)
                            else:
                                show_default(matrix)
                        else:
                            show_default(matrix)

                elif command == 'refresh':
                    prev_track = None

                elif command == 'set_username':
                    username = cmd.get('username', username)
                    settings['lastfm_username'] = username
                    save_settings(settings)
                    prev_track = None

            # Get now playing
            track = get_now_playing(username, session)
            if track:
                track_id = f"{track['artist']}-{track['name']}"
                if dimmed:
                    matrix.brightness = current_brightness
                    dimmed = False
                    prev_track = None
                not_playing_since = None
                if track_id != prev_track:
                    print(f"Now playing: {track['name']} by {track['artist']}")
                    show_image(matrix, track['image_url'], session)
                    prev_track = track_id
                write_status(track['name'], track['artist'], dimmed, current_brightness)
            else:
                if prev_track is not None:
                    print('Nothing playing')
                    show_default(matrix)
                    prev_track = None
                    not_playing_since = time.time()
                if not_playing_since and not dimmed:
                    elapsed = time.time() - not_playing_since
                    if elapsed >= DIM_AFTER_SECONDS:
                        print('Dimming display...')
                        matrix.brightness = DIM_BRIGHTNESS
                        show_default(matrix)
                        dimmed = True
                write_status(None, None, dimmed, current_brightness)

        except Exception as e:
            print(f'Error: {e}')
        time.sleep(5)

if __name__ == '__main__':
    main()
