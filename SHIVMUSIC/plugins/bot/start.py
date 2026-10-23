import time
import random
import asyncio
from html import escape
from pyrogram import filters
from pyrogram.enums import ChatType, ChatAction, ButtonStyle, ParseMode
from pyrogram.types import InlineKeyboardMarkup, Message, InlineKeyboardButton
# 👇 Nayi library yahan update kar di gayi hai
from youtubesearchpython.__future__ import VideosSearch

import config
from SHIVMUSIC import app
from SHIVMUSIC.misc import _boot_
from SHIVMUSIC.plugins.sudo.sudoers import sudoers_list
from SHIVMUSIC.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
)
from SHIVMUSIC.utils.decorators.language import LanguageStart
from SHIVMUSIC.utils.formatters import get_readable_time
from SHIVMUSIC.utils.inline import help_pannel, private_panel, start_panel
from SHIVMUSIC.utils.html_builder import build_welcome_html
from SHIVMUSIC.utils.progress import stream_typewriter_rich_message
from config import BANNED_USERS, START_IMG_URL, CMBOT
from strings import get_string

# 💎 Premium Emojis List for Buttons (icon_custom_emoji_id)
PREMIUM_EMOJIS = [
    "5258362837411045098", "6102938383456146362", "5463274047771000031", "6100397162976252509",
    "5373310679241466020", "5408916593780470262", "5776182936638329359", "5258389041006518073",
    "6280269890821558384", "5936143551854285132", "6172332822892647766", "5891211339170326418",
    "5409368076447657845", "6172312314423808834", "6082387600599944892", "6271537028307881531"
]

# 🎨 Dynamic Color Generator (Random Styles)
def get_style_map():
    styles = [ButtonStyle.PRIMARY, ButtonStyle.SUCCESS, ButtonStyle.DANGER]
    random.shuffle(styles)
    # Row me buttons ke hisaab se random color assign hoga
    return {1: styles[0], 2: styles[1], 3: styles[2]}

# 🔘 Smart Button Creator
def create_btn(text, cb=None, url=None, user_id=None, style=ButtonStyle.PRIMARY, no_emoji=False):
    kwargs = {"text": text, "style": style}
    if cb: kwargs["callback_data"] = cb
    if url: kwargs["url"] = url
    if user_id: kwargs["user_id"] = user_id
    if not no_emoji: kwargs["icon_custom_emoji_id"] = int(random.choice(PREMIUM_EMOJIS))
    return InlineKeyboardButton(**kwargs)

# Telegram Message Effect IDs
EFFECT_ID = [
    5046509860389126442,
    5107584321108051014,
    5104841245755180586,
    5159385139981059251,
]


@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    loading_1 = await message.reply_text(random.choice(CMBOT))
    await add_served_user(message.from_user.id)
    
    await loading_1.edit_text("<b><tg-emoji emoji-id='5373310679241466020'>🌀</tg-emoji> ᴌᴏᴀᴅɪɴɢ....</b>")
    await asyncio.sleep(0.3)

    await loading_1.edit_text("<b><tg-emoji emoji-id='5891211339170326418'>⌛️</tg-emoji> ꜱᴛᴀʀᴛɪɴɢ..ʙᴀʙʏ.❤️❤️</b>")
    await asyncio.sleep(0.3)

    await loading_1.edit_text("<b><tg-emoji emoji-id='5355051922862653659'>🤖</tg-emoji> ɪ ᴀᴍ ᴀʟɪᴠᴇ ʙᴀʙʏ❤️😌🫣🫣</b>")
    await asyncio.sleep(0.5)

    await loading_1.edit_text("<b><tg-emoji emoji-id='6172312314423808834'>✨</tg-emoji> BETA ʙᴏᴛs🫣🫣.</b>")
    await asyncio.sleep(0.5)

    await loading_1.delete()
    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]
        if name[0:4] == "help":
            keyboard = help_pannel(_)
            await app.send_chat_action(message.chat.id, ChatAction.TYPING)
            # Sticker Before Image in /start help
            await message.reply_sticker("CAACAgUAAxkBAAFJgZ1qBGwx9Z9vW5BhG3dw0l1A5j4CyQACXRYAAuc-wVWs4--9DGlDKzsE")
            return await message.reply_photo(
                random.choice(START_IMG_URL),
                caption=_["help_1"].format(config.SUPPORT_CHAT),
                reply_markup=keyboard,
            )
        if name[0:3] == "sud":
            await sudoers_list(client=client, message=message, _=_)
            if await is_on_off(2):
                return await app.send_message(
                    chat_id=config.LOGGER_ID,
                    text=f"<tg-emoji emoji-id='6172312314423808834'>✨</tg-emoji> {message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ <b>sᴜᴅᴏʟɪsᴛ</b>.\n\n<tg-emoji emoji-id='5258362837411045098'>👤</tg-emoji> <b>ᴜsᴇʀ ɪᴅ ➠</b> <code>{message.from_user.id}</code>\n<tg-emoji emoji-id='6235576525563895420'>📍</tg-emoji> <b>ᴜsᴇʀɴᴀᴍᴇ ➠</b> @{message.from_user.username}",
                )
            return
        if name[0:3] == "inf":
            m = await message.reply_text("<tg-emoji emoji-id='5429571366384842791'>🔎</tg-emoji>")
            query = (str(name)).replace("info_", "", 1)
            query = f"https://www.youtube.com/watch?v={query}"
            
            # --- FIX APPLIED HERE ---
            try:
                results = VideosSearch(query, limit=1)
                search_data = await results.next()
                
                if not search_data or not search_data.get("result"):
                    return await m.edit_text("<tg-emoji emoji-id='6271611232457855630'>❌</tg-emoji> Track details not found. The video might be restricted or deleted.")

                # Getting the first result safely
                result = search_data["result"][0]
                
                title = result.get("title", "Unknown Title")
                duration = result.get("duration", "Unknown Duration")
                views = result.get("viewCount", {}).get("short", "0")
                
                # Handle thumbnail safely
                thumbnails = result.get("thumbnails", [])
                thumbnail = thumbnails[0]["url"].split("?")[0] if thumbnails else random.choice(START_IMG_URL)
                
                channellink = result.get("channel", {}).get("link", "")
                channel = result.get("channel", {}).get("name", "Unknown Channel")
                link = result.get("link", query)
                published = result.get("publishedTime", "Unknown Date")

                searched_text = _["start_6"].format(
                    title, duration, views, published, channellink, channel, app.mention
                )
                
                # ✅ Random Colors applied to track info buttons
                s_map = get_style_map()
                key = InlineKeyboardMarkup(
                    [
                        [
                            create_btn(text=_["S_B_8"], url=link, style=s_map[2]),
                            create_btn(text=_["S_B_9"], url=config.SUPPORT_CHAT, style=s_map[2]),
                        ],
                    ]
                )
                await m.delete()
                await app.send_photo(
                    chat_id=message.chat.id,
                    photo=thumbnail,
                    caption=searched_text,
                    reply_markup=key,
                )
                if await is_on_off(2):
                    return await app.send_message(
                        chat_id=config.LOGGER_ID,
                        text=f"<tg-emoji emoji-id='6172312314423808834'>✨</tg-emoji> {message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ <b>ᴛʀᴀᴄᴋ ɪɴғᴏʀᴍᴀᴛɪᴏɴ</b>.\n\n<tg-emoji emoji-id='5258362837411045098'>👤</tg-emoji> <b>ᴜsᴇʀ ɪᴅ ➠</b> <code>{message.from_user.id}</code>\n<tg-emoji emoji-id='6235576525563895420'>📍</tg-emoji> <b>ᴜsᴇʀɴᴀᴍᴇ ➠</b> @{message.from_user.username}",
                    )
            except Exception as e:
                return await m.edit_text(
                    f"<tg-emoji emoji-id='6271611232457855630'>❌</tg-emoji> <b>Track information unavailable</b>\n\n<code>{escape(str(e))}</code>",
                    parse_mode=ParseMode.HTML,
                )
            # --- FIX ENDS HERE ---

    else:
        out = private_panel(_)
        await app.send_chat_action(message.chat.id, ChatAction.TYPING)
        
        # 👉 Yahan Sticker Send Hoga (Start Image se pehle)
        await message.reply_sticker("CAACAgUAAxkBAAFJgZ1qBGwx9Z9vW5BhG3dw0l1A5j4CyQACXRYAAuc-wVWs4--9DGlDKzsE")
        
        await stream_typewriter_rich_message(
            client=app,
            chat_id=message.chat.id,
            full_html=build_welcome_html(
                message.from_user.mention, app.mention, app.username
            ),
            chunk_delay=0.08,
            reply_markup=InlineKeyboardMarkup(out),
            photo=random.choice(START_IMG_URL),
        )
        if await is_on_off(2):
            return await app.send_message(
                chat_id=config.LOGGER_ID,
                text=f"<tg-emoji emoji-id='6172312314423808834'>✨</tg-emoji> {message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ.\n\n<tg-emoji emoji-id='5258362837411045098'>👤</tg-emoji> <b>ᴜsᴇʀ ɪᴅ ➠</b> <code>{message.from_user.id}</code>\n<tg-emoji emoji-id='6235576525563895420'>📍</tg-emoji> <b>ᴜsᴇʀɴᴀᴍᴇ ➠</b> @{message.from_user.username}",
            )


@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    out = start_panel(_)
    uptime = int(time.time() - _boot_)
    await message.reply_photo(
        random.choice(START_IMG_URL),
        caption=build_welcome_html(
            message.from_user.mention, app.mention, app.username
        ),
        reply_markup=InlineKeyboardMarkup(out),
        parse_mode=ParseMode.HTML,
    )
    return await add_served_chat(message.chat.id)


@app.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    for member in message.new_chat_members:
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)
            if await is_banned_user(member.id):
                try:
                    await message.chat.ban_member(member.id)
                except:
                    pass
            if member.id == app.id:
                if message.chat.type != ChatType.SUPERGROUP:
                    await message.reply_text(_["start_4"])
                    return await app.leave_chat(message.chat.id)
                if message.chat.id in await blacklisted_chats():
                    await message.reply_text(
                        _["start_5"].format(
                            app.mention,
                            f"https://t.me/{app.username}?start=sudolist",
                            config.SUPPORT_CHAT,
                        ),
                        disable_web_page_preview=True,
                    )
                    return await app.leave_chat(message.chat.id)

                out = start_panel(_)
                await message.reply_text(
                    text=build_welcome_html(
                        message.from_user.mention, app.mention, app.username
                    ),
                    reply_markup=InlineKeyboardMarkup(out),
                    parse_mode=ParseMode.HTML,
                )
                await add_served_chat(message.chat.id)
                await message.stop_propagation()
        except Exception as ex:
            print(ex)
