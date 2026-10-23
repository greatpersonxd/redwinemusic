from SHIVMUSIC.core.bot import ANJALI
from SHIVMUSIC.core.dir import dirr
from SHIVMUSIC.core.git import git
from SHIVMUSIC.core.userbot import Userbot
from SHIVMUSIC.misc import dbb, heroku
from pyrogram import Client
from SafoneAPI import SafoneAPI
from .logging import LOGGER

dirr()
git()
dbb()
heroku()

app = ANJALI()
api = SafoneAPI()
userbot = Userbot()

from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()
