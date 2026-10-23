import platform
from sys import version as pyver

import psutil
from pyrogram import __version__ as pyrover
from pyrogram import filters
from pyrogram.errors import MessageIdInvalid
from pyrogram.types import InputMediaPhoto, Message
from pytgcalls.__version__ import __version__ as pytgver

import config
from SHIVMUSIC import app
from SHIVMUSIC.core.userbot import assistants
from SHIVMUSIC.misc import SUDOERS, mongodb
from SHIVMUSIC.plugins import ALL_MODULES
from SHIVMUSIC.utils.database import get_served_chats, get_served_users, get_sudoers
from SHIVMUSIC.utils.decorators.language import language, languageCB
from SHIVMUSIC.utils.inline.stats import back_stats_buttons, stats_buttons
from config import BANNED_USERS


@app.on_message(filters.command(["stats", "gstats"]) & filters.group & ~BANNED_USERS)
@language
async def stats_global(client, message: Message, _):
    upl = stats_buttons(_, True if message.from_user.id in SUDOERS else False)
    await message.reply_photo(
        photo=config.STATS_IMG_URL,
        caption=_["gstats_2"].format(app.mention),
        reply_markup=upl,
    )


@app.on_callback_query(filters.regex("stats_back") & ~BANNED_USERS)
@languageCB
async def home_stats(client, CallbackQuery, _):
    upl = stats_buttons(_, True if CallbackQuery.from_user.id in SUDOERS else False)
    await CallbackQuery.edit_message_text(
        text=_["gstats_2"].format(app.mention),
        reply_markup=upl,
    )


@app.on_callback_query(filters.regex("TopOverall") & ~BANNED_USERS)
@languageCB
async def overall_stats(client, CallbackQuery, _):
    await CallbackQuery.answer()
    upl = back_stats_buttons(_)
    try:
        await CallbackQuery.answer()
    except:
        pass
    await CallbackQuery.edit_message_text(_["gstats_1"].format(app.mention))
    served_chats = len(await get_served_chats())
    served_users = len(await get_served_users())

    text = _["gstats_3"].format(
        app.mention,
        len(assistants),
        len(BANNED_USERS),
        served_chats,
        served_users,
        len(ALL_MODULES),
        len(SUDOERS),
        config.AUTO_LEAVING_ASSISTANT,
        config.DURATION_LIMIT_MIN,
    )
    med = InputMediaPhoto(media=config.STATS_IMG_URL, caption=text)
    try:
        await CallbackQuery.edit_message_media(media=med, reply_markup=upl)
    except MessageIdInvalid:
        await CallbackQuery.message.reply_photo(
            photo=config.STATS_IMG_URL, caption=text, reply_markup=upl
        )


# stats.py में line 76-137 को replace करो:

@app.on_callback_query(filters.regex("bot_stats_sudo"))
@languageCB
async def bot_stats(client, CallbackQuery, _):
    if CallbackQuery.from_user.id not in SUDOERS:
        return await CallbackQuery.answer(_["gstats_4"], show_alert=True)
    
    upl = back_stats_buttons(_)
    try:
        await CallbackQuery.answer()
    except:
        pass
    
    try:
        await CallbackQuery.edit_message_text(_["gstats_1"].format(app.mention))
        
        p_core = psutil.cpu_count(logical=False) or 0
        t_core = psutil.cpu_count(logical=True) or 0
        ram = str(round(psutil.virtual_memory().total / (1024.0**3))) + " ɢʙ"
        
        try:
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                cpu_freq = cpu_freq.current
                if cpu_freq >= 1000:
                    cpu_freq = f"{round(cpu_freq / 1000, 2)}ɢʜᴢ"
                else:
                    cpu_freq = f"{round(cpu_freq, 2)}ᴍʜᴢ"
            else:
                cpu_freq = "ғᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ"
        except:
            cpu_freq = "ғᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ"
        
        hdd = psutil.disk_usage("/")
        total = hdd.total / (1024.0**3)
        used = hdd.used / (1024.0**3)
        free = hdd.free / (1024.0**3)
        
        # ✅ MongoDB error handling
        try:
            call = await mongodb.command("dbstats")
            datasize = call.get("dataSize", 0) / 1024
            storage = call.get("storageSize", 0) / 1024
            collections = call.get("collections", 0)
            objects = call.get("objects", 0)
        except Exception as e:
            datasize = 0
            storage = 0
            collections = 0
            objects = 0
            print(f"MongoDB stats error: {e}")
        
        served_chats = len(await get_served_chats())
        served_users = len(await get_served_users())
        
        text = _["gstats_5"].format(
            app.mention,
            len(ALL_MODULES),
            platform.system(),
            ram,
            p_core,
            t_core,
            cpu_freq,
            pyver.split()[0],
            pyrover,
            pytgver,
            str(total)[:4],
            str(used)[:4],
            str(free)[:4],
            served_chats,
            served_users,
            len(BANNED_USERS),
            len(await get_sudoers()),
            str(datasize)[:6],
            storage,
            collections,
            objects,
        )
        med = InputMediaPhoto(media=config.STATS_IMG_URL, caption=text)
        try:
            await CallbackQuery.edit_message_media(media=med, reply_markup=upl)
        except MessageIdInvalid:
            await CallbackQuery.message.reply_photo(
                photo=config.STATS_IMG_URL, caption=text, reply_markup=upl
            )
    except Exception as e:
        print(f"Stats error: {e}")
        await CallbackQuery.answer("Error loading stats. Check logs.", show_alert=True)
