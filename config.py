import re
from os import getenv
from dotenv import load_dotenv
from pyrogram import filters

load_dotenv()

API_ID = int(getenv("API_ID", "0"))
API_HASH = getenv("API_HASH")

BOT_TOKEN = getenv("BOT_TOKEN")
BOT_ID = getenv("BOT_ID")

OWNER_USERNAME = getenv("OWNER_USERNAME", "")
BOT_USERNAME = getenv("BOT_USERNAME", "")
BOT_NAME = getenv("BOT_NAME", "")
ASSUSERNAME = getenv("ASSUSERNAME", "")
BOT_LINK = getenv("BOT_LINK", "https://t.me/royal_musics_bot")

MONGO_DB_URI = getenv("MONGO_DB_URI")

# ----------------- API CONFIGURATION -----------------
# 1. Shruti API (Primary)
SHRUTI_API_URL = getenv("SHRUTI_API_URL", "https://shrutibots.site")
SHRUTI_API_KEY = getenv("SHRUTI_API_KEY", "")

# 2. MusicSp API (Fallback)
MUSICSP_API_URL = getenv("MusicSp_API_URL", "https://apisparrow.site")
MUSICSP_API_KEY = getenv("MusicSp_API_KEY", "sparrowZoBvSEIl6zhvRL4VVn0yql7o")
# -----------------------------------------------------

DURATION_LIMIT_MIN = int(getenv("DURATION_LIMIT", 17000))

LOGGER_ID = int(getenv("LOGGER_ID", "0"))
# All uncaught handler/background errors are sent here. Override with
# ERROR_LOGGER_ID in the environment when deploying a different log group.
ERROR_LOGGER_ID = int(getenv("ERROR_LOGGER_ID", "-1004392214389"))
LOGGER_2_ID = int(getenv("LOGGER_2_ID", "-1003255930328"))

OWNER_ID = int(getenv("OWNER_ID", "8418584090"))

# 🟢 THE FIX: SUDOERS LIST ADDED HERE WITH YOUR IDS
SUDOERS = [8418584090, 8723235165]

HEROKU_APP_NAME = getenv("HEROKU_APP_NAME")
HEROKU_API_KEY = getenv("HEROKU_API_KEY")

UPSTREAM_REPO = getenv(
    "UPSTREAM_REPO",
    "",
)
UPSTREAM_BRANCH = getenv("UPSTREAM_BRANCH", "main")
GIT_TOKEN = getenv("GIT_TOKEN", "")

SUPPORT_CHANNEL = getenv("SUPPORT_CHANNEL", "https://t.me/betabot_hub")
SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/betabot_support")
GITHUB = getenv("GITHUB", "https://t.me/sukoon_s")

AUTO_LEAVING_ASSISTANT = getenv("AUTO_LEAVING_ASSISTANT", "False")
AUTO_LEAVE_ASSISTANT_TIME = int(getenv("ASSISTANT_LEAVE_TIME", "9000"))

SONG_DOWNLOAD_DURATION = int(getenv("SONG_DOWNLOAD_DURATION", "9999999"))
SONG_DOWNLOAD_DURATION_LIMIT = int(getenv("SONG_DOWNLOAD_DURATION_LIMIT", "9999999"))

SPOTIFY_CLIENT_ID = getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = getenv("SPOTIFY_CLIENT_SECRET", "")

PLAYLIST_FETCH_LIMIT = int(getenv("PLAYLIST_FETCH_LIMIT", 25))
PLAYLIST_ID = -1003812209413

TG_AUDIO_FILESIZE_LIMIT = int(getenv("TG_AUDIO_FILESIZE_LIMIT", "5242880000"))
TG_VIDEO_FILESIZE_LIMIT = int(getenv("TG_VIDEO_FILESIZE_LIMIT", "5242880000"))

# 🟢 4 ASSISTANT SESSIONS ADDED HERE
STRING1 = getenv("STRING_SESSION", "")
STRING2 = getenv("STRING_SESSION2", "")
STRING3 = getenv("STRING_SESSION3", "")
STRING4 = getenv("STRING_SESSION4", "")

START_IMG_URL = getenv("START_IMG_URL", "https://image.zaw-myo.workers.dev/image/fbe45904-8603-4e6d-9d51-2e89104db85b").split()
HELP_IMG_URL = getenv("HELP_IMG_URL", "https://image.zaw-myo.workers.dev/image/fbe45904-8603-4e6d-9d51-2e89104db85b").split()
PING_IMG_URL = getenv("PING_IMG_URL", "https://image.zaw-myo.workers.dev/image/fbe45904-8603-4e6d-9d51-2e89104db85b").split()

PLAYLIST_IMG_URL = getenv("PLAYLIST_IMG_URL", "https://files.catbox.moe/6r97s4.jpg https://files.catbox.moe/huqcbp.jpg https://files.catbox.moe/gbx3h3.jpg https://files.catbox.moe/6f5azl.jpg").split()
STATS_IMG_URL = getenv("STATS_IMG_URL", "https://image.zaw-myo.workers.dev/image/fbe45904-8603-4e6d-9d51-2e89104db85b")
TELEGRAM_AUDIO_URL = getenv("TELEGRAM_AUDIO_URL", "https://files.catbox.moe/6f5azl.jpg").split()
TELEGRAM_VIDEO_URL = getenv("TELEGRAM_VIDEO_URL", "https://files.catbox.moe/6r97s4.jpg").split()
STREAM_IMG_URL = getenv("STREAM_IMG_URL", "https://files.catbox.moe/6r97s4.jpg").split()
SOUNCLOUD_IMG_URL = getenv("SOUNCLOUD_IMG_URL", "https://i.ibb.co/S4sPf3q8/soundcloud.jpg").split()
YOUTUBE_IMG_URL = getenv("YOUTUBE_IMG_URL", "https://files.catbox.moe/6r97s4.jpg").split()
SPOTIFY_ARTIST_IMG_URL = getenv("SPOTIFY_ARTIST_IMG_URL", "https://i.ibb.co/XZfMS8Db/spotify.jpg").split()
SPOTIFY_ALBUM_IMG_URL = getenv("SPOTIFY_ALBUM_IMG_URL", "https://i.ibb.co/XZfMS8Db/spotify.jpg").split()
SPOTIFY_PLAYLIST_IMG_URL = getenv("SPOTIFY_PLAYLIST_IMG_URL", "https://i.ibb.co/XZfMS8Db/spotify.jpg").split()

BANNED_USERS = filters.user()
adminlist = {}
lyrical = {}
votemode = {}
autoclean = []
confirmer = {}

def time_to_seconds(time):
    return sum(int(x) * 60**i for i, x in enumerate(reversed(str(time).split(":"))))

DURATION_LIMIT = int(time_to_seconds(f"{DURATION_LIMIT_MIN}:00"))

if SUPPORT_CHANNEL and not re.match("(?:http|https)://", SUPPORT_CHANNEL):
    raise SystemExit("[ERROR] - SUPPORT_CHANNEL url must start with https://")

if SUPPORT_CHAT and not re.match("(?:http|https)://", SUPPORT_CHAT):
    raise SystemExit("[ERROR] - SUPPORT_CHAT url must start with https://")

CMBOT = [ "💞", "🥂", "🔍", "🧪", "⚡️", "🔥", "🦋", "🎩", "🌈", "🍷",
    "🥃", "🥤", "🕊️", "💌", "🧨", "✨", "💥", "💯", "🌟", "⚡️",
    "❤️", "😍", "🥰", "😘", "😂", "🤣", "😱", "😡", "👏", "🙏",
    "🎉", "🎊", "🎶", "🎵", "🎧", "🎸", "🎹", "🥁", "🎺", "🎷",
    "🔥", "⚡️", "💫", "🌙", "☀️", "🌈", "❄️", "🌸", "🌺", "🌹",
    "🦋", "🕊️", "🐍", "🐯", "🦁", "🐺", "🐉", "🦅", "🦄", "🐎"
    ]

EFFECT_ID = [
    5046509860389126442,
    5107584321108051014,
    5104841245755180586,
    5159385139981059251,
]
