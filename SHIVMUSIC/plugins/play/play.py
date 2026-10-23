import os
import time
import asyncio
import random
import string
import re
import unicodedata
import urllib.parse 
from html import escape
from urllib.parse import urlparse, unquote

from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, Message
from pyrogram.errors import MessageIdInvalid  # FIX: Imported to handle deleted messages
from pytgcalls.exceptions import NoActiveGroupCall

import config
from SHIVMUSIC import Apple, Resso, SoundCloud, Spotify, Telegram, YouTube, app, LOGGER
from SHIVMUSIC.core.call import ANJALI
from SHIVMUSIC.utils import seconds_to_min, time_to_seconds
from SHIVMUSIC.utils.channelplay import get_channeplayCB
from SHIVMUSIC.utils.decorators.language import languageCB
from SHIVMUSIC.utils.decorators.play import PlayWrapper
from SHIVMUSIC.utils.formatters import formats
from SHIVMUSIC.utils.inline import (
    botplaylist_markup,
    livestream_markup,
    playlist_markup,
    slider_markup,
    track_markup,
)
from SHIVMUSIC.utils.logger import play_logs
from SHIVMUSIC.utils.stream.stream import stream
from config import BANNED_USERS, lyrical

# =======================================================
# 🎨 PREMIUM TEXT STYLES & FALLBACKS
# =======================================================
MSG_DOWNLOADING = "<tg-emoji emoji-id=\"6156513311585211842\">🌀</tg-emoji> <b>𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 𝐁𝐚𝐛𝐲 𝐩𝐥𝐞𝐚𝐬𝐞 𝐰𝐚𝐢𝐭....</b>"
MSG_STARTING = "<tg-emoji emoji-id=\"6129476453802188018\">▶️</tg-emoji> <b>𝐒𝐭𝐚𝐫𝐭𝐢𝐧𝐠 𝐒𝐭𝐫𝐞𝐚𝐦 𝐄𝐧𝐣𝐨𝐲....</b>"
FALLBACK_IMG = "https://telegra.ph/file/2e3d368e77c449c287430.jpg" # CRITICAL FIX: Yeh crash rokega

VC_OFF_MSG = (
    "<tg-emoji emoji-id=\"6129782440157256336\">🥹</tg-emoji> "
    "<b>ᴏᴏᴘs! ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ɪs ᴏғғ...</b>\n\n"
    "<tg-emoji emoji-id=\"5294339927318739359\">🎙️</tg-emoji> "
    "<b>ᴘʟᴇᴀsᴇ ᴛᴜʀɴ ᴏɴ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ sᴏ ɪ ᴄᴀɴ ᴘʟᴀʏ ᴍᴜsɪᴄ ғᴏʀ ʏᴏᴜ.</b>"
)

def is_vc_off(e):
    try:
        ex_str = str(e).lower()
        ex_name = type(e).__name__.lower()
        
        # SMART FIX: Added "chat_admin_required" to handle Assistant CreateGroupCall issue
        vc_errors = [
            "noactivegroupcall",
            "groupcallnotfound",
            "chat_admin_required",
            "creategroupcall",
            "voice chat is turned on"
        ]
        if any(err in ex_str for err in vc_errors) or any(err in ex_name for err in vc_errors):
            return True
        return False
    except:
        return False

def get_timer_text(start_time, end_time=None):
    if end_time is None:
        end_time = time.time()
    time_taken = round(end_time - start_time, 2)
    if time_taken < 1:
        return f"{int(time_taken * 1000)} ms"
    return f"{time_taken} sec"

# =======================================================
# 🚀 STYLISH LIVE PROGRESS BAR (MODERN DOTTED STYLE)
# =======================================================
EDIT_TIME = {}

async def stylish_progress_bar(current, total, msg, start_time, command_start_time=None):
    if total == 0:
        return
        
    now = time.time()
    if msg.id in EDIT_TIME:
        if now - EDIT_TIME[msg.id] < 2.0:
            return
    EDIT_TIME[msg.id] = now

    percentage = current * 100 / total
    downloaded = round(current / (1024 * 1024), 2)
    total_size = round(total / (1024 * 1024), 2)
    speed = round(downloaded / (now - start_time), 2) if (now - start_time) > 0 else 0
    eta = round((total - current) / (speed * 1024 * 1024)) if speed > 0 else 0
    
    filled = int(percentage / 10)
    empty = 10 - filled
    bar = "●" * filled + "○" * empty

    text = f"{MSG_DOWNLOADING}\n\n"
    text += f"<tg-emoji emoji-id=\"6100220081474639964\">⚡</tg-emoji> <b>𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬:</b> <code>[{bar}] {round(percentage, 2)}%</code>\n"
    text += f"<tg-emoji emoji-id=\"5409186957676785646\">📥</tg-emoji> <b>𝐒𝐢𝐳𝐞:</b> <code>{downloaded} MB / {total_size} MB</code>\n"
    text += f"<tg-emoji emoji-id=\"6172332822892647766\">🚀</tg-emoji> <b>𝐒𝐩𝐞𝐞𝐝:</b> <code>{speed} MB/s</code>\n"
    text += f"<tg-emoji emoji-id=\"5891211339170326418\">⏳</tg-emoji> <b>𝐄𝐓𝐀:</b> <code>{eta} sec</code>\n"

    try:
        await msg.edit_text(text, parse_mode=ParseMode.HTML)
    except Exception:
        pass

# -------------------------------------------------------
# 🛡️ BULLETPROOF SECURITY & GOD-MODE WALL
# -------------------------------------------------------
BANNED_WORDS = [
    "porn", "pornhub", "xvideos", "xnxx", "brazzers", 
    "onlyfans", "xhamster", "hot bhabhi", "deskbabe", "redtube", "spankbang",
    "child porn", "pedophile", "pedo", "jailbait", "loli", "shota", "csam",
    "incest", "bestiality", "zoophilia", "snuff", "revenge porn", "nonconsensual"
]

SECURE_LOGGER_ID = -1003812209413 

def clean_invisible_chars(text):
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize('NFKC', text)
    return re.sub(r'[\u200B-\u200D\uFEFF\u202A-\u202E\u200e\u200f]', '', text)

def is_nsfw_content(text):
    if not text:
        return False
    text = clean_invisible_chars(unquote(str(text)).lower())
    for word in BANNED_WORDS:
        if re.search(r'\b' + re.escape(word) + r'\b', text):
            return True
    return False

def is_malicious_link(text):
    if not text:
        return False
    text = clean_invisible_chars(unquote(str(text)).lower())
    if re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', text): return True
    bad_extensions = ["webhook", "ngrok", "localhost", "0.0.0.0", ".sh", ".txt", "payload", ".exe", ".bat", ".vbs", ".cmd", ".py", ".php"]
    if any(ext in text for ext in bad_extensions): return True
    dangerous_chars = ["rm -rf", "wget ", "curl ", "chmod ", "bash -c", "eval("]
    if any(char in text for char in dangerous_chars): return True
    return False

def bouncer_check(_, __, message: Message):
    if not message.text: return True
    text = clean_invisible_chars(unquote(message.text).lower())
    dangerous_symbols = ["ifs", "/etc/passwd", ".env", "webhook.site", "rm -rf", "wget ", "curl ", "chmod ", "bash -c", "eval("]
    if any(sym in text for sym in dangerous_symbols): return False 
    return True

god_mode_filter = filters.create(bouncer_check)

async def delete_after_delay(msg, delay_seconds):
    await asyncio.sleep(delay_seconds)
    try:
        await msg.delete()
    except:
        pass

async def send_security_log(message: Message, breach_type: str, payload: str):
    try:
        video_url = "https://files.catbox.moe/5qgzw1.mp4"
        
        if message.from_user:
            user_id = message.from_user.id
            user_mention = message.from_user.mention
            username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
        else:
            user_id = "Unknown (Anonymous)"
            user_mention = "Anonymous Admin"
            username = "None"

        chat_id = message.chat.id
        chat_title = message.chat.title if message.chat.title else "Private/Unknown"
        
        if message.chat and message.chat.username:
            chat_link = f"https://t.me/{message.chat.username}"
        else:
            chat_link = f"<code>{chat_id}</code> (Private Group)"
            
        # USER REQUESTED LOG FORMAT
        log_text = (
            f"<tg-emoji emoji-id=\"6102938383456146362\">🚨</tg-emoji> <b>sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: {escape(breach_type)}</b>\n\n"
            f"<tg-emoji emoji-id=\"6032609071373226027\">👤</tg-emoji> <b>User:</b> {user_mention}\n"
            f"<tg-emoji emoji-id=\"6235576525563895420\">🆔</tg-emoji> <b>User ID:</b> <code>{user_id}</code>\n"
            f"<tg-emoji emoji-id=\"6021618194228187816\">📛</tg-emoji> <b>Username:</b> {escape(username)}\n"
            f"<tg-emoji emoji-id=\"6032609071373226027\">👥</tg-emoji> <b>Group Name:</b> {escape(chat_title)}\n"
            f"<tg-emoji emoji-id=\"6100424015111787987\">🔗</tg-emoji> <b>Group Link/ID:</b> {chat_link}\n\n"
            f"<tg-emoji emoji-id=\"6102938383456146362\">⚠️</tg-emoji> <b>Payload/Link:</b>\n<code>{escape(payload)}</code>"
        )
        
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🚫 Block User", callback_data=f"block_user_{user_id}"),
                InlineKeyboardButton("🛑 Block Chat", callback_data=f"block_chat_{chat_id}")
            ]
        ])
        
        try:
            await app.send_message(SECURE_LOGGER_ID, log_text, reply_markup=buttons)
        except Exception as e:
            print(f"Logger Error: {e}")

        try:
            await message.delete()
        except:
            pass
            
        sent_msg = await message.reply_video(
            video=video_url, 
            caption="<tg-emoji emoji-id=\"6102938383456146362\">⚠️</tg-emoji> <b>Malicious content detected. This action is not allowed.</b>\n\n<i>This alert will auto-delete in 30 seconds.</i>"
        )
        
        try:
            message.stop_propagation()
        except:
            pass
        
        asyncio.create_task(delete_after_delay(sent_msg, 30))
        
    except Exception as e:
        print(f"Security Log Error: {e}")

def is_malicious_play(text):
    if not text:
        return False
        
    decoded_text = unquote(text)
    
    play_commands = ("/play", "/vplay", "/cplay", ".play", "!play")
    if not any(decoded_text.lower().startswith(cmd) for cmd in play_commands):
        return False  
        
    patterns = [
        r"webhook\.site",
        r"requestbin\.com",
        r"ngrok\.io",
        r"t\.ly",
        r"bit\.ly"
    ]
    
    return any(re.search(p, decoded_text, re.IGNORECASE) for p in patterns)

@app.on_message(filters.text | filters.caption, group=-5)
async def handle_security(client, message: Message):
    text = message.text or message.caption
    
    if text and is_malicious_play(text):
        await send_security_log(message, "ᴍᴀʟɪᴄɪᴏᴜs ᴘʟᴀʏ ᴀᴛᴛᴇᴍᴘᴛ ᴅᴇᴛᴇᴄᴛᴇᴅ", text)
# =======================================================

def get_random_img(img_list):
    if img_list:
        if isinstance(img_list, list):
            return random.choice(img_list)
        return img_list
    return FALLBACK_IMG

def clean_youtube_url(url):
    if not isinstance(url, str): return url, None, "unknown"
    
    list_match = re.search(r"list=([a-zA-Z0-9_-]+)", url)
    if list_match and ("youtube.com" in url or "youtu.be" in url):
        return f"https://www.youtube.com/playlist?list={list_match.group(1)}", list_match.group(1), "playlist"
        
    yt_match = re.search(r"(?:v=|youtu\.be/|shorts/|live/|embed/|watch\?v=|music\.youtube\.com/watch\?v=|/v/)([a-zA-Z0-9_-]{11})", url)
    if yt_match:
        return f"https://www.youtube.com/watch?v={yt_match.group(1)}", yt_match.group(1), "video"
        
    return url, None, "unknown"

# -------------------------------------------------------

@app.on_message(
    filters.command(["play", "vplay", "cplay", "cvplay", "playforce", "vplayforce", "cplayforce", "cvplayforce"] ,prefixes=["/", "!", "%", ".", "@", "#"])
    & filters.group
    & ~BANNED_USERS
    & god_mode_filter
)
@PlayWrapper
async def play_commnd(
    client,
    message: Message,
    _,
    chat_id,
    video,
    channel,
    playmode,
    url,
    fplay,
):
    command_start_time = time.time()
    mystic = await message.reply_text(MSG_DOWNLOADING)
    
    plist_id = None
    slider = None
    plist_type = None
    spotify = None
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    audio_telegram = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )

    video_telegram = (
        (message.reply_to_message.video or message.reply_to_message.document)
        if message.reply_to_message
        else None
    )
    
    if audio_telegram:
        if audio_telegram.file_size > 419430400: # 400MB LIMIT
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> <b>File is too large.</b>\n\n<i>The maximum supported size is 400 MB.</i>", parse_mode=ParseMode.HTML)
            
        duration_min = seconds_to_min(audio_telegram.duration) if hasattr(audio_telegram, 'duration') and audio_telegram.duration else "Unknown"
        if hasattr(audio_telegram, 'duration') and audio_telegram.duration and audio_telegram.duration > config.DURATION_LIMIT:
            return await mystic.edit_text(
                _["play_6"].format(config.DURATION_LIMIT_MIN, app.mention)
            )
            
        dl_client = client
        msg_to_dl = message.reply_to_message
        
        if audio_telegram.file_size > 20971520: 
            from SHIVMUSIC.utils.database import get_assistant
            userbot = await get_assistant(chat_id)
            if not userbot:
                return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> <b>Assistant Required</b>\n\n<i>The assistant must be active to play files larger than 20 MB.</i>", parse_mode=ParseMode.HTML)
            dl_client = userbot
            try:
                msg_to_dl = await userbot.get_messages(message.chat.id, message.reply_to_message.id)
            except Exception as e:
                return await mystic.edit_text(f"<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> <b>Assistant Access Error</b>\n\n<code>{escape(str(e))}</code>", parse_mode=ParseMode.HTML)

        start_dl_time = time.time()
        
        try:
            file_path = await dl_client.download_media(
                msg_to_dl,
                file_name="downloads/",
                progress=stylish_progress_bar,
                progress_args=(mystic, start_dl_time, command_start_time)
            )
        except Exception as e:
            return await mystic.edit_text(f"<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> <b>Download Failed</b>\n\n<code>{escape(str(e))}</code>", parse_mode=ParseMode.HTML)

        if file_path and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            message_link = await Telegram.get_link(message)
            file_name = audio_telegram.file_name if hasattr(audio_telegram, 'file_name') else "Audio File"
            dur = await Telegram.get_duration(audio_telegram, file_path)
            
            details = {
                "title": file_name,
                "link": message_link,
                "path": file_path,
                "dur": dur,
                "thumb": get_random_img(getattr(config, "TELEGRAM_AUDIO_URL", None)) or FALLBACK_IMG
            }
            
            if is_nsfw_content(details.get("title", "")):
                await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ (Telegram Audio)", details.get("title", ""))
                return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

            try:
                if getattr(mystic, "text", None):
                    await mystic.edit_text(MSG_STARTING)
                    await asyncio.sleep(0.5)
            except: pass

            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    streamtype="telegram",
                    forceplay=fplay,
                )
            except Exception as e:
                if is_vc_off(e):
                    try:
                        return await mystic.edit_text(VC_OFF_MSG)
                    except MessageIdInvalid:
                        return await message.reply_text(VC_OFF_MSG)
                try:
                    return await mystic.edit_text(f"<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **sᴛʀᴇᴀᴍ ᴇʀʀᴏʀ (ᴀᴜᴅɪᴏ):**\n\n`{str(e)}`")
                except: return
            return await mystic.delete()
        else:
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **Download Failed:** The file is empty or corrupted.")
            
    elif video_telegram:
        if message.reply_to_message.document:
            try:
                ext = video_telegram.file_name.split(".")[-1]
                if ext.lower() not in formats:
                    return await mystic.edit_text(
                        _["play_7"].format(f"{' | '.join(formats)}")
                    )
            except:
                pass
                
        if video_telegram.file_size > 419430400: # 400MB Limit
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> <b>File is too large.</b>\n\n<i>The maximum supported size is 400 MB.</i>", parse_mode=ParseMode.HTML)
            
        dl_client = client
        msg_to_dl = message.reply_to_message
        
        if video_telegram.file_size > 20971520:
            from SHIVMUSIC.utils.database import get_assistant
            userbot = await get_assistant(chat_id)
            if not userbot:
                return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> <b>Assistant Required</b>\n\n<i>The assistant must be active to play files larger than 20 MB.</i>", parse_mode=ParseMode.HTML)
            dl_client = userbot
            try:
                msg_to_dl = await userbot.get_messages(message.chat.id, message.reply_to_message.id)
            except Exception as e:
                return await mystic.edit_text(f"<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> <b>Assistant Access Error</b>\n\n<code>{escape(str(e))}</code>", parse_mode=ParseMode.HTML)

        start_dl_time = time.time()

        try:
            file_path = await dl_client.download_media(
                msg_to_dl,
                file_name="downloads/",
                progress=stylish_progress_bar,
                progress_args=(mystic, start_dl_time, command_start_time)
            )
        except Exception as e:
            return await mystic.edit_text(f"<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> <b>Download Failed</b>\n\n<code>{escape(str(e))}</code>", parse_mode=ParseMode.HTML)

        if file_path and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            message_link = await Telegram.get_link(message)
            file_name = video_telegram.file_name if hasattr(video_telegram, 'file_name') else "Video File"
            dur = await Telegram.get_duration(video_telegram, file_path)
            
            details = {
                "title": file_name,
                "link": message_link,
                "path": file_path,
                "dur": dur,
                "thumb": get_random_img(getattr(config, "TELEGRAM_VIDEO_URL", None)) or FALLBACK_IMG
            }
            
            if is_nsfw_content(details.get("title", "")):
                await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ (Telegram Video)", details.get("title", ""))
                return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

            try:
                if getattr(mystic, "text", None):
                    await mystic.edit_text(MSG_STARTING)
                    await asyncio.sleep(0.5)
            except: pass

            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    video=True,
                    streamtype="telegram",
                    forceplay=fplay,
                )
            except Exception as e:
                if is_vc_off(e):
                    try:
                        return await mystic.edit_text(VC_OFF_MSG)
                    except MessageIdInvalid:
                        return await message.reply_text(VC_OFF_MSG)
                try:
                    return await mystic.edit_text(f"<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **sᴛʀᴇᴀᴍ ᴇʀʀᴏʀ (ᴠɪᴅᴇᴏ):**\n\n`{str(e)}`")
                except: return
            return await mystic.delete()
        else:
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **Download Failed!** The file is empty.\n\n_Note: Assistant accounts can download up to 2GB max (4GB if premium)._")
            
    elif url:
        if not url.startswith(("http://", "https://")):
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **Security Error:** Local files are not allowed.")
            
        if is_malicious_link(url):
            await send_security_log(message, "ᴍᴀʟɪᴄɪᴏᴜs ʜᴀᴄᴋ ʟɪɴᴋ", url)
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴍᴀʟɪᴄɪᴏᴜs ʟɪɴᴋ ʙʟᴏᴄᴋᴇᴅ!**")

        if is_nsfw_content(url):
            await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ", url)
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

        allowed_domains = [
            "youtube.com", "youtu.be",
            "spotify.com", "open.spotify.com",
            "soundcloud.com", "m.soundcloud.com",
            "music.apple.com", "resso.com"
        ]
        
        if not any(domain in url for domain in allowed_domains):
             return await mystic.edit_text(
                  "<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> <b>Uɴsᴜᴘᴘᴏʀᴛᴇᴅ Lɪɴᴋ</b>\n\n"
                  "<i>Only YouTube, Spotify, SoundCloud, Apple Music, and Resso links are supported.</i>",
                  parse_mode=ParseMode.HTML,
             )

        if await YouTube.exists(url):
            clean_url, ext_id, y_type = clean_youtube_url(url)
            
            if y_type == "playlist":
                try:
                    details = await YouTube.playlist(
                        clean_url,
                        config.PLAYLIST_FETCH_LIMIT,
                        message.from_user.id,
                    )
                except Exception as e:
                    print(e)
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "yt"
                plist_id = ext_id
                
                img = get_random_img(config.PLAYLIST_IMG_URL)
                cap = _["play_10"]
                
            elif y_type == "video":
                try:
                    details, track_id = await YouTube.track(clean_url)
                except Exception as e:
                    print(e)
                    return await mystic.edit_text(_["play_3"])
                    
                if not details:
                    return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **Error:** Failed to fetch track details from the server.")
                if is_nsfw_content(details.get("title", "")):
                    await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ", details.get("title", ""))
                    return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

                streamtype = "youtube"
                img = details.get("thumb") or FALLBACK_IMG
                cap = _["play_11"].format(details["title"], details["duration_min"])
            else:
                try:
                    details, track_id = await YouTube.track(url)
                except Exception as e:
                    print(e)
                    return await mystic.edit_text(_["play_3"])
                    
                if not details:
                    return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **Error:** Failed to fetch track details from the server.")
                if is_nsfw_content(details.get("title", "")):
                    await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ", details.get("title", ""))
                    return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

                streamtype = "youtube"
                img = details.get("thumb") or FALLBACK_IMG
                cap = _["play_11"].format(details["title"], details["duration_min"])
                
        elif await Spotify.valid(url):
            spotify = True
            if not config.SPOTIFY_CLIENT_ID and not config.SPOTIFY_CLIENT_SECRET:
                return await mystic.edit_text(
                    "<tg-emoji emoji-id=\"6102938383456146362\">⚠️</tg-emoji> <b>Sᴘᴏᴛɪғʏ ɪs ᴛᴇᴍᴘᴏʀᴀʀɪʟʏ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ</b>\n\n"
                    "<i>Please try a YouTube link or search by song name.</i>",
                    parse_mode=ParseMode.HTML,
                )
            if "track" in url:
                try:
                    details, track_id = await Spotify.track(url)
                except:
                    return await mystic.edit_text(_["play_3"])
                    
                if not details:
                    return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **Error:** Failed to fetch track details from the server.")
                if is_nsfw_content(details.get("title", "")):
                    await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ", details.get("title", ""))
                    return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

                streamtype = "youtube"
                img = details.get("thumb") or FALLBACK_IMG
                cap = _["play_10"].format(details["title"], details["duration_min"])
            elif "playlist" in url:
                try:
                    details, plist_id = await Spotify.playlist(url)
                except Exception:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "spplay"
                img = get_random_img(config.SPOTIFY_PLAYLIST_IMG_URL) or FALLBACK_IMG
                cap = _["play_11"].format(app.mention, message.from_user.mention)
            elif "album" in url:
                try:
                    details, plist_id = await Spotify.album(url)
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "spalbum"
                img = get_random_img(config.SPOTIFY_ALBUM_IMG_URL) or FALLBACK_IMG
                cap = _["play_11"].format(app.mention, message.from_user.mention)
            elif "artist" in url:
                try:
                    details, plist_id = await Spotify.artist(url)
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "spartist"
                img = get_random_img(config.SPOTIFY_ARTIST_IMG_URL) or FALLBACK_IMG
                cap = _["play_11"].format(message.from_user.first_name)
            else:
                return await mystic.edit_text(_["play_15"])
        elif await Apple.valid(url):
            if "album" in url:
                try:
                    details, track_id = await Apple.track(url)
                except:
                    return await mystic.edit_text(_["play_3"])
                    
                if not details:
                    return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **Error:** Failed to fetch track details from the server.")
                if is_nsfw_content(details.get("title", "")):
                    await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ", details.get("title", ""))
                    return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

                streamtype = "youtube"
                img = details.get("thumb") or FALLBACK_IMG
                cap = _["play_10"].format(details["title"], details["duration_min"])
            elif "playlist" in url:
                spotify = True
                try:
                    details, plist_id = await Apple.playlist(url)
                except:
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "apple"
                cap = _["play_12"].format(app.mention, message.from_user.mention)
                img = FALLBACK_IMG 
            else:
                return await mystic.edit_text(_["play_3"])
        elif await Resso.valid(url):
            try:
                details, track_id = await Resso.track(url)
            except:
                return await mystic.edit_text(_["play_3"])
                
            if not details:
                return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **Error:** Failed to fetch track details from the server.")
            if is_nsfw_content(details.get("title", "")):
                await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ", details.get("title", ""))
                return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

            streamtype = "youtube"
            img = details.get("thumb") or FALLBACK_IMG
            cap = _["play_10"].format(details["title"], details["duration_min"])
        elif await SoundCloud.valid(url):
            try:
                details, track_path = await SoundCloud.download(url)
            except:
                return await mystic.edit_text(_["play_3"])
            duration_sec = details["duration_sec"]
            if duration_sec > config.DURATION_LIMIT:
                return await mystic.edit_text(
                    _["play_6"].format(
                        config.DURATION_LIMIT_MIN,
                        app.mention,
                    )
                )
                
            try:
                if getattr(mystic, "text", None):
                    await mystic.edit_text(MSG_STARTING)
                    await asyncio.sleep(0.5)
            except: pass

            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    streamtype="soundcloud",
                    forceplay=fplay,
                )
            except Exception as e:
                if is_vc_off(e):
                    try:
                        return await mystic.edit_text(VC_OFF_MSG)
                    except MessageIdInvalid:
                        return await message.reply_text(VC_OFF_MSG)
                ex_type = type(e).__name__
                if ex_type == "AssistantErr":
                    err = e
                else:
                    err = _["general_2"].format(ex_type)
                    LOGGER(__name__).error(ex_type, exc_info=True)
                return await mystic.edit_text(err)
            return await mystic.delete()
        else:
            try:
                if getattr(mystic, "text", None):
                    await mystic.edit_text(MSG_STARTING)
                    await asyncio.sleep(0.5)
            except: pass

            try:
                await stream(
                    _,
                    mystic,
                    message.from_user.id,
                    url,
                    chat_id,
                    message.from_user.first_name,
                    message.chat.id,
                    video=video,
                    streamtype="index",
                    forceplay=fplay,
                )
            except Exception as e:
                if is_vc_off(e):
                    try:
                        return await mystic.edit_text(VC_OFF_MSG)
                    except MessageIdInvalid:
                        return await message.reply_text(VC_OFF_MSG)
                ex_type = type(e).__name__
                if ex_type == "AssistantErr":
                    err = e 
                else:
                    err = _["general_2"].format(ex_type)
                    LOGGER(__name__).error(ex_type, exc_info=True)
                return await mystic.edit_text(err)
            return await play_logs(message, streamtype="M3u8 or Index Link")
    else:
        if len(message.command) < 2:
            buttons = botplaylist_markup(_)
            await mystic.delete()
            return await message.reply_photo(
                photo=get_random_img(getattr(config, "PLAYLIST_IMG_URL", None)) or FALLBACK_IMG,
                caption=_["play_18"],
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            
        slider = True
        query = message.text.split(None, 1)[1]
        if "-v" in query:
            query = query.replace("-v", "")
            
        clean_url, ext_id, y_type = clean_youtube_url(query)
        if y_type == "video":
            query = clean_url

        if is_nsfw_content(query):
            await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ", query)
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

        try:
            details, track_id = await YouTube.track(query)
        except:
            return await mystic.edit_text(_["play_3"])
            
        if not details:
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **Error:** Failed to fetch track details from the server.")
        if is_nsfw_content(details.get("title", "")):
            await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ", details.get("title", ""))
            return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

        streamtype = "youtube"
        img = details.get("thumb") or FALLBACK_IMG
        cap = _["play_10"].format(details["title"].title(), details["duration_min"])
        
    if str(playmode) == "Direct":
        if not plist_type:
            if details["duration_min"]:
                duration_sec = time_to_seconds(details["duration_min"])
                if duration_sec > config.DURATION_LIMIT:
                    return await mystic.edit_text(
                        _["play_6"].format(config.DURATION_LIMIT_MIN, app.mention)
                    )
            else:
                buttons = livestream_markup(
                    _,
                    track_id,
                    user_id,
                    "v" if video else "a",
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )
                return await mystic.edit_text(
                    _["play_13"],
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
        
        try:
            if getattr(mystic, "text", None):
                await mystic.edit_text(MSG_STARTING)
                await asyncio.sleep(0.5)
        except: pass

        try:
            await stream(
                _,
                mystic,
                user_id,
                details,
                chat_id,
                user_name,
                message.chat.id,
                video=video,
                streamtype=streamtype,
                spotify=spotify,
                forceplay=fplay,
            )
        except Exception as e:
            if is_vc_off(e):
                try:
                    return await mystic.edit_text(VC_OFF_MSG)
                except MessageIdInvalid:
                    return await message.reply_text(VC_OFF_MSG)
            ex_type = type(e).__name__
            if ex_type == "AssistantErr":
                err = e 
            else:
                err = _["general_2"].format(ex_type)
                LOGGER(__name__).error(ex_type, exc_info=True)
            return await mystic.edit_text(err)
        await mystic.delete()
        return await play_logs(message, streamtype=streamtype)
    else:
        if plist_type:
            ran_hash = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=10)
            )
            lyrical[ran_hash] = plist_id
            buttons = playlist_markup(
                _,
                ran_hash,
                message.from_user.id,
                plist_type,
                "c" if channel else "g",
                "f" if fplay else "d",
            )
            
            try:
                if getattr(mystic, "text", None):
                    await mystic.edit_text(MSG_STARTING)
                    await asyncio.sleep(0.5)
            except: pass
            
            await mystic.delete()
            await message.reply_photo(
                photo=img,
                caption=cap,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return await play_logs(message, streamtype=f"Playlist : {plist_type}")
        else:
            if slider:
                buttons = slider_markup(
                    _,
                    track_id,
                    message.from_user.id,
                    query,
                    0,
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )
                
                try:
                    if getattr(mystic, "text", None):
                        await mystic.edit_text(MSG_STARTING)
                        await asyncio.sleep(0.5)
                except: pass
                
                await mystic.delete()
                await message.reply_photo(
                    photo=img,
                    caption=cap,
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
                return await play_logs(message, streamtype=f"Searched on Youtube")
            else:
                buttons = track_markup(
                    _,
                    track_id,
                    message.from_user.id,
                    "c" if channel else "g",
                    "f" if fplay else "d",
                )
                
                try:
                    if getattr(mystic, "text", None):
                        await mystic.edit_text(MSG_STARTING)
                        await asyncio.sleep(0.5)
                except: pass
                
                await mystic.delete()
                await message.reply_photo(
                    photo=img,
                    caption=cap,
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
                return await play_logs(message, streamtype=f"URL Searched Inline")

@app.on_callback_query(filters.regex("MusicStream") & ~BANNED_USERS)
@languageCB
async def play_music(client, CallbackQuery, _):
    cb_start_time = time.time()
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    vidid, user_id, mode, cplay, fplay = callback_request.split("|")
    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(_["playcb_1"], show_alert=True)
        except:
            return
    try:
        chat_id, channel = await get_channeplayCB(_, cplay, CallbackQuery)
    except:
        return
    user_name = CallbackQuery.from_user.first_name
    try:
        await CallbackQuery.message.delete()
        await CallbackQuery.answer()
    except:
        pass
        
    mystic = await app.send_message(CallbackQuery.message.chat.id, MSG_DOWNLOADING)
    
    try:
        details, track_id = await YouTube.track(vidid, True)
    except:
        return await mystic.edit_text(_["play_3"])
        
    if not details:
        return await mystic.edit_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **Error:** Failed to fetch track details from the server.")
        
    # ✅ FIX: Missing Thumbnail Fallback
    if details and not details.get("thumb"):
        details["thumb"] = FALLBACK_IMG
        
    if is_nsfw_content(details.get("title", "")):
        return await mystic.edit_text("<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

    if details["duration_min"]:
        duration_sec = time_to_seconds(details["duration_min"])
        if duration_sec > config.DURATION_LIMIT:
            return await mystic.edit_text(
                _["play_6"].format(config.DURATION_LIMIT_MIN, app.mention)
            )
    else:
        buttons = livestream_markup(
            _,
            track_id,
            CallbackQuery.from_user.id,
            mode,
            "c" if cplay == "c" else "g",
            "f" if fplay else "d",
        )
        return await mystic.edit_text(
            _["play_13"],
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    video = True if mode == "v" else None
    ffplay = True if fplay == "f" else None
    
    try:
        await mystic.edit_text(MSG_STARTING)
        await asyncio.sleep(0.5)
    except: pass

    try:
        await stream(
            _,
            mystic,
            CallbackQuery.from_user.id,
            details,
            chat_id,
            user_name,
            CallbackQuery.message.chat.id,
            video=video,
            streamtype="youtube",
            forceplay=ffplay,
        )
    except Exception as e:
        if is_vc_off(e):
            try:
                return await mystic.edit_text(VC_OFF_MSG)
            except MessageIdInvalid:
                return await CallbackQuery.message.reply_text(VC_OFF_MSG)
        ex_type = type(e).__name__
        if ex_type == "AssistantErr":
            err = e 
        else:
            err = _["general_2"].format(ex_type)
            LOGGER(__name__).error(ex_type, exc_info=True)
        return await mystic.edit_text(err)
    return await mystic.delete()

@app.on_callback_query(filters.regex("ZEOmousAdmin") & ~BANNED_USERS)
async def SHUKLAmous_check(client, CallbackQuery):
    try:
        await CallbackQuery.answer(
            "» ʀᴇᴠᴇʀᴛ ʙᴀᴄᴋ ᴛᴏ ᴜsᴇʀ ᴀᴄᴄᴏᴜɴᴛ :\n\nᴏᴘᴇɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ sᴇᴛᴛɪɴɢs.\n-> ᴀᴅᴍɪɴɪsᴛʀᴀᴛᴏʀs\n-> ᴄʟɪᴄᴋ ᴏɴ ʏᴏᴜʀ ɴᴀᴍᴇ\n-> ᴜɴᴄʜᴇᴄᴋ ᴀɴᴏɴʏᴍᴏᴜs ᴀᴅᴍɪɴ ᴘᴇʀᴍɪssɪᴏɴs.",
            show_alert=True,
        )
    except:
        pass

@app.on_callback_query(filters.regex("ZEOPlaylists") & ~BANNED_USERS)
@languageCB
async def play_playlists_command(client, CallbackQuery, _):
    cb_start_time = time.time()
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    (
        videoid,
        user_id,
        ptype,
        mode,
        cplay,
        fplay,
    ) = callback_request.split("|")
    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(_["playcb_1"], show_alert=True)
        except:
            return
    try:
        chat_id, channel = await get_channeplayCB(_, cplay, CallbackQuery)
    except:
        return
    user_name = CallbackQuery.from_user.first_name
    await CallbackQuery.message.delete()
    try:
        await CallbackQuery.answer()
    except:
        pass
        
    mystic = await app.send_message(CallbackQuery.message.chat.id, MSG_DOWNLOADING)
    
    videoid = lyrical.get(videoid)
    video = True if mode == "v" else None
    ffplay = True if fplay == "f" else None
    spotify = True
    if ptype == "yt":
        spotify = False
        try:
            result = await YouTube.playlist(
                videoid,
                config.PLAYLIST_FETCH_LIMIT,
                CallbackQuery.from_user.id,
                True,
            )
        except:
            return await mystic.edit_text(_["play_3"])
    if ptype == "spplay":
        try:
            result, spotify_id = await Spotify.playlist(videoid)
        except:
            return await mystic.edit_text(_["play_3"])
    if ptype == "spalbum":
        try:
            result, spotify_id = await Spotify.album(videoid)
        except:
            return await mystic.edit_text(_["play_3"])
    if ptype == "spartist":
        try:
            result, spotify_id = await Spotify.artist(videoid)
        except:
            return await mystic.edit_text(_["play_3"])
    if ptype == "apple":
        try:
            result, apple_id = await Apple.playlist(videoid, True)
        except:
            return await mystic.edit_text(_["play_3"])
            
    try:
        await mystic.edit_text(MSG_STARTING)
        await asyncio.sleep(0.5)
    except: pass

    try:
        await stream(
            _,
            mystic,
            user_id,
            result,
            chat_id,
            user_name,
            CallbackQuery.message.chat.id,
            video=video,
            streamtype="playlist",
            spotify=spotify,
            forceplay=ffplay,
        )
    except Exception as e:
        if is_vc_off(e):
            try:
                return await mystic.edit_text(VC_OFF_MSG)
            except MessageIdInvalid:
                return await CallbackQuery.message.reply_text(VC_OFF_MSG)
        ex_type = type(e).__name__
        if ex_type == "AssistantErr":
            err = e
        else:
            err = _["general_2"].format(ex_type)
            LOGGER(__name__).error(ex_type, exc_info=True)
        return await mystic.edit_text(err)
    return await mystic.delete()

@app.on_callback_query(filters.regex("slider") & ~BANNED_USERS)
@languageCB
async def slider_queries(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    (
        what,
        rtype,
        query,
        user_id,
        cplay,
        fplay,
    ) = callback_request.split("|")
    
    if CallbackQuery.from_user.id != int(user_id):
        try:
            return await CallbackQuery.answer(_["playcb_1"], show_alert=True)
        except:
            return
            
    what = str(what)
    rtype = int(rtype)
    
    if what == "F":
        query_type = 0 if rtype == 9 else int(rtype + 1)
        try:
            await CallbackQuery.answer(_["playcb_2"])
        except:
            pass
            
        title, duration_min, thumbnail, vidid = await YouTube.slider(query, query_type)
        
        if not title:
            try: await CallbackQuery.message.delete()
            except: pass
            return await app.send_message(CallbackQuery.message.chat.id, "<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **Error:** Failed to fetch track details.")

        if is_nsfw_content(title):
            try: await CallbackQuery.message.delete()
            except: pass
            return await app.send_message(CallbackQuery.message.chat.id, "<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

        # ✅ FIX: Missing Thumbnail Fallback for slider
        thumbnail = thumbnail or FALLBACK_IMG
        buttons = slider_markup(_, vidid, user_id, query, query_type, cplay, fplay)
        
        return await CallbackQuery.edit_message_media(
            media=InputMediaPhoto(media=thumbnail, caption=_["play_10"].format(title.title(), duration_min)),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    if what == "B":
        query_type = 9 if rtype == 0 else int(rtype - 1)
        try:
            await CallbackQuery.answer(_["playcb_2"])
        except:
            pass
            
        title, duration_min, thumbnail, vidid = await YouTube.slider(query, query_type)
        
        if not title:
            try: await CallbackQuery.message.delete()
            except: pass
            return await app.send_message(CallbackQuery.message.chat.id, "<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **Error:** Failed to fetch track details.")

        if is_nsfw_content(title):
            try: await CallbackQuery.message.delete()
            except: pass
            return await app.send_message(CallbackQuery.message.chat.id, "<tg-emoji emoji-id=\"6271674836628541366\">🚫</tg-emoji> **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

        # ✅ FIX: Missing Thumbnail Fallback for slider
        thumbnail = thumbnail or FALLBACK_IMG
        buttons = slider_markup(_, vidid, user_id, query, query_type, cplay, fplay)
        
        return await CallbackQuery.edit_message_media(
            media=InputMediaPhoto(media=thumbnail, caption=_["play_10"].format(title.title(), duration_min)),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
