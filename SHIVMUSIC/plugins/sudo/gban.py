import asyncio
import random
from pyrogram import filters
from pyrogram.errors import FloodWait
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from SHIVMUSIC import app
from SHIVMUSIC.misc import SUDOERS
from SHIVMUSIC.utils import get_readable_time
from SHIVMUSIC.utils.database import (
    add_banned_user,
    get_banned_count,
    get_banned_users,
    get_served_chats,
    is_banned_user,
    remove_banned_user,
)
from SHIVMUSIC.utils.decorators.language import language
from SHIVMUSIC.utils.extraction import extract_user
# ✅ FIXED: Changed LOG_GROUP_ID to LOGGER_ID
from config import BANNED_USERS, START_IMG_URL, LOGGER_ID

# ✅ Helper for Random Image
def get_random_gban_img():
    if START_IMG_URL:
        if isinstance(START_IMG_URL, list):
            return random.choice(START_IMG_URL)
        return START_IMG_URL
    return "https://telegra.ph/file/2e3d368e77c449c287430.jpg" # Fallback

@app.on_message(filters.command(["gban", "globalban"]) & SUDOERS)
@language
async def global_ban(client, message: Message, _):
    if not message.reply_to_message:
        if len(message.command) != 2:
            return await message.reply_text(_["general_1"])
    
    user = await extract_user(message)
    
    # --- 🛡️ SAFETY CHECKS ---
    if user.id == message.from_user.id:
        return await message.reply_text(_["gban_1"])
    elif user.id == app.id:
        return await message.reply_text(_["gban_2"])
    elif user.id in SUDOERS:
        return await message.reply_text(_["gban_3"])
    
    is_gbanned = await is_banned_user(user.id)
    if is_gbanned:
        return await message.reply_text(_["gban_4"].format(user.mention))
    
    if user.id not in BANNED_USERS:
        BANNED_USERS.add(user.id)
    
    served_chats = []
    chats = await get_served_chats()
    for chat in chats:
        served_chats.append(int(chat["chat_id"]))
    
    time_expected = get_readable_time(len(served_chats))
    
    # ✅ Random Image + Spoiler
    mystic = await message.reply_photo(
        photo=get_random_gban_img(),
        caption=_["gban_5"].format(user.mention, time_expected),
        has_spoiler=True
    )
    
    number_of_chats = 0
    for chat_id in served_chats:
        try:
            await app.ban_chat_member(chat_id, user.id)
            number_of_chats += 1
            await asyncio.sleep(0.5) # Floodwait Protection
        except FloodWait as fw:
            await asyncio.sleep(int(fw.value))
        except:
            continue
            
    await add_banned_user(user.id)
    
    # Final Message
    await message.reply_text(
        _["gban_6"].format(
            app.mention,
            message.chat.title,
            message.chat.id,
            user.mention,
            user.id,
            message.from_user.mention,
            number_of_chats,
        )
    )
    await mystic.delete()
    
    # ✅ FIXED: Use LOGGER_ID for logs
    if LOGGER_ID:
        try:
            await app.send_message(
                LOGGER_ID,
                f"**🚨 #GLOBAL_BAN**\n\n**Origin:** {message.chat.title} [`{message.chat.id}`]\n**Admin:** {message.from_user.mention}\n**Banned:** {user.mention} [`{user.id}`]\n**Chats Affected:** {number_of_chats}"
            )
        except:
            pass


@app.on_message(filters.command(["ungban"]) & SUDOERS)
@language
async def global_un(client, message: Message, _):
    if not message.reply_to_message:
        if len(message.command) != 2:
            return await message.reply_text(_["general_1"])
    
    user = await extract_user(message)
    is_gbanned = await is_banned_user(user.id)
    
    if not is_gbanned:
        return await message.reply_text(_["gban_7"].format(user.mention))
    
    if user.id in BANNED_USERS:
        BANNED_USERS.remove(user.id)
    
    served_chats = []
    chats = await get_served_chats()
    for chat in chats:
        served_chats.append(int(chat["chat_id"]))
    
    time_expected = get_readable_time(len(served_chats))
    
    # ✅ Random Image + Spoiler
    mystic = await message.reply_photo(
        photo=get_random_gban_img(),
        caption=_["gban_8"].format(user.mention, time_expected),
        has_spoiler=True
    )
    
    number_of_chats = 0
    for chat_id in served_chats:
        try:
            await app.unban_chat_member(chat_id, user.id)
            number_of_chats += 1
            await asyncio.sleep(0.5)
        except FloodWait as fw:
            await asyncio.sleep(int(fw.value))
        except:
            continue
            
    await remove_banned_user(user.id)
    await message.reply_text(_["gban_9"].format(user.mention, number_of_chats))
    await mystic.delete()


@app.on_message(filters.command(["gbannedusers", "gbanlist"]) & SUDOERS)
@language
async def gbanned_list(client, message: Message, _):
    counts = await get_banned_count()
    if counts == 0:
        return await message.reply_text(_["gban_10"])
    
    mystic = await message.reply_text(_["gban_11"])
    msg = _["gban_12"]
    count = 0
    users = await get_banned_users()
    
    for user_id in users:
        count += 1
        try:
            user = await app.get_users(user_id)
            user = user.first_name if not user.mention else user.mention
            msg += f"{count}➤ {user}\n"
        except Exception:
            msg += f"{count}➤ {user_id}\n"
            continue
            
    if count == 0:
        return await mystic.edit_text(_["gban_10"])
    else:
        return await mystic.edit_text(msg)