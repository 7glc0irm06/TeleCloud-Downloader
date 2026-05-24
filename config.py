import os
import threading
import telebot
from collections import OrderedDict

# =============================================================
# Paths and constants
# =============================================================
TOKEN           = os.environ.get('DOWNLOADER_BOT_TOKEN')
BOT_PASSWORD    = os.environ.get('BOT_PASSWORD')
DRIVE_FOLDER_ID = '1n-I9Ipd2I5SL27HhFlaPzaMzRtFCHy-I'
DOWNLOAD_DIR    = '/root/downloads'
COOKIES_DIR     = '/root/cookies'
COOKIES_STATE   = '/root/cookies_enabled.json'
USER_LANGS_FILE = '/root/user_langs.json'

MAX_RETRIES  = 3
RETRY_DELAY  = 10

# =============================================================
# Per-user state
# =============================================================
authorized_users = set()
user_state       = {}
tg_upload_mode   = set()
gd_upload_mode   = set()

# Default quality per user (video only)
# Possible values: 'manual', 'best', '1080', '720', '480'
user_quality = {}

# Media mode: True = music (audio), False = video (default)
user_audio_mode = {}

# Download mode per user
# Possible values: 'auto', 'ytdlp', 'torrent', 'direct'
user_download_mode = {}

# Video container format (when media == video)
# Possible values: 'mp4', 'mkv', 'default'
user_video_format = {}

# Audio codec (when media == audio)
# Possible values: 'mp3', 'm4a', 'flac', 'default'
user_audio_format = {}

# Audio bitrate/quality (when media == audio)
# Possible values: '320', '128', 'default'
user_audio_quality = {}

# Subtitle language preference
# Possible values: 'en', 'fa', 'off'
user_subtitle = {}

# Embed chapter metadata in video files
# Possible values: True / False
user_chapters = {}

# =============================================================
# Link cache
# =============================================================
class BoundedCache(OrderedDict):
    def __init__(self, maxsize=2000):
        super().__init__()
        self.maxsize = maxsize

    def __setitem__(self, key, value):
        if key in self:
            self.move_to_end(key)
        super().__setitem__(key, value)
        if len(self) > self.maxsize:
            self.popitem(last=False)

url_cache  = BoundedCache(2000)
cache_lock = threading.Lock()

# =============================================================
# Shared objects
# =============================================================
import telebot.apihelper as apihelper
apihelper.API_URL = "http://localhost:8081/bot{0}/{1}"
apihelper.FILE_URL = "http://localhost:8081"
bot = telebot.TeleBot(TOKEN, parse_mode=None)
pending_queue  = []
queue_lock     = threading.Lock()
current_task   = None
stop_event     = threading.Event()
rclone_process = None

# =============================================================
# Create required directories
# =============================================================
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(COOKIES_DIR,  exist_ok=True)
