import asyncio
import time
from pyrogram import filters
from pyrogram.enums import ChatMembersFilter
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from motor.motor_asyncio import AsyncIOMotorClient
from config import adminlist, MONGO_DB_URI, LOGGER_ID

from SHIVMUSIC import app
from SHIVMUSIC.misc import SUDOERS
from SHIVMUSIC.utils.database import (
    get_active_chats,
    get_authuser_names,
    get_client,
    get_served_chats,
    get_served_users,
)
from SHIVMUSIC.utils.decorators.language import language
from SHIVMUSIC.utils.formatters import alpha_to_int

IS_BROADCASTING = False

# ==========================================
# PROGRESS BAR HELPER
# ==========================================
def get_progress_bar(current, total, length=20):
    if total == 0:
        return "▱" * length
    percent = current / total
    filled_len = int(length * percent)
    bar = "▰" * filled_len + "▱" * (length - filled_len)
    return bar

# ==========================================
# SELF PROMO DATABASE SETUP
# ==========================================
dbclient = AsyncIOMotorClient(MONGO_DB_URI)
db = dbclient.MahiMusic
promo_msgs_db = db.promo_messages
promo_toggle_db = db.promo_settings
broadcast_time_db = db.promo_time

async def is_promo_on() -> bool:
    chat = await promo_toggle_db.find_one({"_id": "promo_toggle"})
    if not chat:
        return False
    return chat.get("status", False)

async def set_promo_status(status: bool):
    await promo_toggle_db.update_one({"_id": "promo_toggle"}, {"$set": {"status": status}}, upsert=True)

async def save_promo_msg(chat_id: int, message_id: int):
    await promo_msgs_db.insert_one({"chat_id": chat_id, "message_id": message_id, "timestamp": int(time.time())})

async def get_old_promo_msgs():
    time_limit = int(time.time()) - 172800 # 48 hours
    return promo_msgs_db.find({"timestamp": {"$lt": time_limit}})

async def delete_promo_record(chat_id: int, message_id: int):
    await promo_msgs_db.delete_one({"chat_id": chat_id, "message_id": message_id})

# ==========================================
# SELF PROMO ASSETS
# ==========================================
PROMO_IMAGE = "https://files.catbox.moe/etdhlr.jpg"
PROMO_TEXT = """
<tg-emoji emoji-id="6172312314423808834">✨</tg-emoji> ᴛʜɪꜱ ɪꜱ [✶ 🎀 ᴍᴜꜱɪᴄ ʙᴏᴛ 🎀 ✶](https://t.me/betabot_hub)

<tg-emoji emoji-id="6271537028307881531">💎</tg-emoji> ᴧ ᴘʀєᴍɪᴜᴍ ᴅєꜱɪɢηєᴅ ϻᴜꜱɪᴄ ᴘʟᴧʏєʀ ʙσᴛ ꜰσʀ ᴛєʟєɢʀᴧϻ ɢʀσᴜᴘ & ᴄʜᴧηηєʟ. 
<tg-emoji emoji-id="6082387600599944892">🎧</tg-emoji> 24x7 ᴍᴜꜱɪᴄ • ꜱᴍᴏᴏᴛʜ ᴀɴᴅ ꜰᴀꜱᴛ ᴘʟᴀʏʙᴀᴄᴋ

<tg-emoji emoji-id="6100220081474639964">⚡️</tg-emoji> ᴇɴᴊᴏʏ ᴜɴʟɪᴍɪᴛᴇᴅ ꜱᴏɴɢꜱ, qᴜɪᴄᴋ ʀᴇꜱᴘᴏɴꜱᴇ, ᴀɴᴅ ᴄʟᴇᴀʀ ᴀᴜᴅɪᴏ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ.

<tg-emoji emoji-id="6100424015111787987">📌</tg-emoji> ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ, ᴍᴀᴋᴇ ᴍᴇ ᴀᴅᴍɪɴ, ᴀɴᴅ ꜱᴇɴᴅ /play song name ᴛᴏ ꜱᴛᴀʀᴛ ᴛʜᴇ ᴍᴜꜱɪᴄ.
"""
PROMO_BUTTON = InlineKeyboardMarkup(
    [[InlineKeyboardButton("✨ Aᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ ✨", url="https://t.me/betabot_hub")]]
)


# ==========================================
# EXISTING BROADCAST COMMAND
# ==========================================
@app.on_message(filters.command("broadcast") & SUDOERS)
@language
async def braodcast_message(client, message, _):
    global IS_BROADCASTING
    if message.reply_to_message:
        x = message.reply_to_message.id
        y = message.chat.id
    else:
        if len(message.command) < 2:
            return await message.reply_text(_["broad_2"])
        query = message.text.split(None, 1)[1]
        if "-pin" in query:
            query = query.replace("-pin", "")
        if "-nobot" in query:
            query = query.replace("-nobot", "")
        if "-pinloud" in query:
            query = query.replace("-pinloud", "")
        if "-assistant" in query:
            query = query.replace("-assistant", "")
        if "-user" in query:
            query = query.replace("-user", "")
        if query == "":
            return await message.reply_text(_["broad_8"])

    IS_BROADCASTING = True
    await message.reply_text(_["broad_1"])

    if "-nobot" not in message.text:
        sent = 0
        pin = 0
        chats = []
        schats = await get_served_chats()
        for chat in schats:
            chats.append(int(chat["chat_id"]))
        for i in chats:
            try:
                m = (
                    await app.forward_messages(i, y, x)
                    if message.reply_to_message
                    else await app.send_message(i, text=query)
                )
                if "-pin" in message.text:
                    try:
                        await m.pin(disable_notification=True)
                        pin += 1
                    except:
                        continue
                elif "-pinloud" in message.text:
                    try:
                        await m.pin(disable_notification=False)
                        pin += 1
                    except:
                        continue
                sent += 1
                await asyncio.sleep(0.2)
            except FloodWait as fw:
                flood_time = int(fw.value)
                if flood_time > 200:
                    continue
                await asyncio.sleep(flood_time)
            except:
                continue
        try:
            await message.reply_text(_["broad_3"].format(sent, pin))
        except:
            pass

    if "-user" in message.text:
        susr = 0
        served_users = []
        susers = await get_served_users()
        for user in susers:
            served_users.append(int(user["user_id"]))
        for i in served_users:
            try:
                m = (
                    await app.forward_messages(i, y, x)
                    if message.reply_to_message
                    else await app.send_message(i, text=query)
                )
                susr += 1
                await asyncio.sleep(0.2)
            except FloodWait as fw:
                flood_time = int(fw.value)
                if flood_time > 200:
                    continue
                await asyncio.sleep(flood_time)
            except:
                pass
        try:
            await message.reply_text(_["broad_4"].format(susr))
        except:
            pass

    if "-assistant" in message.text:
        aw = await message.reply_text(_["broad_5"])
        text = _["broad_6"]
        from SHIVMUSIC.core.userbot import assistants

        for num in assistants:
            sent = 0
            client = await get_client(num)
            async for dialog in client.get_dialogs():
                try:
                    await client.forward_messages(
                        dialog.chat.id, y, x
                    ) if message.reply_to_message else await client.send_message(
                        dialog.chat.id, text=query
                    )
                    sent += 1
                    await asyncio.sleep(3)
                except FloodWait as fw:
                    flood_time = int(fw.value)
                    if flood_time > 200:
                        continue
                    await asyncio.sleep(flood_time)
                except:
                    continue
            text += _["broad_7"].format(num, sent)
        try:
            await aw.edit_text(text)
        except:
            pass
    IS_BROADCASTING = False


# ==========================================
# UPDATED: SELF PROMO BROADCAST LOGIC
# ==========================================
async def run_promo_broadcast(status_message=None):
    await broadcast_time_db.update_one({"_id": "last_run"}, {"$set": {"time": int(time.time())}}, upsert=True)
    
    users = await get_served_users()
    chats = await get_served_chats()

    total_users = len(users)
    total_chats = len(chats)
    total_targets = total_users + total_chats

    u_success, u_failed = 0, 0
    g_success, g_failed = 0, 0
    completed = 0

    async def update_progress():
        if status_message and completed % 10 == 0:  # Update message every 10 sends to avoid floodwait
            bar = get_progress_bar(completed, total_targets)
            percent = int((completed / total_targets) * 100) if total_targets else 100
            text = (
                f"<tg-emoji emoji-id=\"5373310679241466020\">🌀</tg-emoji> **Live Promo Broadcasting...**\n\n"
                f"[{bar}] **{percent}%**\n\n"
                f"<tg-emoji emoji-id=\"6032609071373226027\">👥</tg-emoji> **Users:** <tg-emoji emoji-id=\"6280269890821558384\">✅</tg-emoji> {u_success} | <tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> {u_failed}\n"
                f"<tg-emoji emoji-id=\"6021618194228187816\">💬</tg-emoji> **Groups:** <tg-emoji emoji-id=\"6280269890821558384\">✅</tg-emoji> {g_success} | <tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> {g_failed}"
            )
            try:
                await status_message.edit_text(text)
            except Exception:
                pass

    for user in users:
        user_id = user["user_id"] if isinstance(user, dict) else user
        try:
            msg = await app.send_photo(chat_id=int(user_id), photo=PROMO_IMAGE, caption=PROMO_TEXT, reply_markup=PROMO_BUTTON)
            await save_promo_msg(int(user_id), msg.id)
            u_success += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            u_failed += 1
        
        completed += 1
        await update_progress()
        await asyncio.sleep(0.5)

    for chat in chats:
        chat_id = chat["chat_id"] if isinstance(chat, dict) else chat
        try:
            msg = await app.send_photo(chat_id=int(chat_id), photo=PROMO_IMAGE, caption=PROMO_TEXT, reply_markup=PROMO_BUTTON)
            await save_promo_msg(int(chat_id), msg.id)
            g_success += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            g_failed += 1
        
        completed += 1
        await update_progress()
        await asyncio.sleep(0.5)

    return u_success, u_failed, g_success, g_failed


@app.on_message(filters.command(["selfpromo", "promo"]) & SUDOERS)
async def promo_toggle_cmd(client, message):
    if len(message.command) != 2:
        return await message.reply_text(
            "<tg-emoji emoji-id=\"5767288287001580715\">💡</tg-emoji> **Usage Options:**\n"
            "`/selfpromo on` - Start auto 24-hour broadcast\n"
            "`/selfpromo off` - Stop auto broadcast\n"
            "`/selfpromo run` - Instantly broadcast right now"
        )
    
    state = message.command[1].lower()
    
    if state == "on":
        await set_promo_status(True)
        await message.reply_text("<tg-emoji emoji-id=\"6280269890821558384\">✅</tg-emoji> **Auto Self Promo Started!**\nBot will broadcast every 24 hours.")
    elif state == "off":
        await set_promo_status(False)
        await message.reply_text("<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> **Auto Self Promo Stopped!**")
    elif state == "run":
        status_msg = await message.reply_text("<tg-emoji emoji-id=\"5373310679241466020\">🌀</tg-emoji> **Calculating stats & initializing broadcast...**")
        try:
            # We pass the status_msg so the function can edit it live
            u_success, u_failed, g_success, g_failed = await run_promo_broadcast(status_message=status_msg)
            
            # Final completion message
            stats_text = (
                f"<tg-emoji emoji-id=\"6039381989985882045\">📢</tg-emoji> **Manual Promo Completed** <tg-emoji emoji-id=\"6280269890821558384\">✅</tg-emoji>\n\n"
                f"<tg-emoji emoji-id=\"6032609071373226027\">👥</tg-emoji> **Users:** <tg-emoji emoji-id=\"6280269890821558384\">✅</tg-emoji> {u_success} | <tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> {u_failed}\n"
                f"<tg-emoji emoji-id=\"6021618194228187816\">💬</tg-emoji> **Groups:** <tg-emoji emoji-id=\"6280269890821558384\">✅</tg-emoji> {g_success} | <tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> {g_failed}"
            )
            await status_msg.edit_text(stats_text)
            if LOGGER_ID:
                await app.send_message(LOGGER_ID, stats_text)
        except Exception as e:
            await status_msg.edit_text(f"<tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> Error: {e}")
    else:
        await message.reply_text("<tg-emoji emoji-id=\"6102938383456146362\">⚠️</tg-emoji> **Invalid argument.** Use `on`, `off`, or `run`.")


# ==========================================
# BACKGROUND TASKS
# ==========================================
async def auto_clean():
    while not await asyncio.sleep(10):
        try:
            served_chats = await get_active_chats()
            for chat_id in served_chats:
                if chat_id not in adminlist:
                    adminlist[chat_id] = []
                    async for user in app.get_chat_members(chat_id, filter=ChatMembersFilter.ADMINISTRATORS):
                        if user.privileges.can_manage_video_chats:
                            adminlist[chat_id].append(user.user.id)
                    authusers = await get_authuser_names(chat_id)
                    for user in authusers:
                        user_id = await alpha_to_int(user)
                        adminlist[chat_id].append(user_id)
        except:
            continue

async def auto_promo_task():
    while True:
        try:
            old_messages = await get_old_promo_msgs()
            async for doc in old_messages:
                try:
                    await app.delete_messages(chat_id=doc["chat_id"], message_ids=doc["message_id"])
                except:
                    pass
                await delete_promo_record(doc["chat_id"], doc["message_id"])
                await asyncio.sleep(1)

            if await is_promo_on():
                last_run_data = await broadcast_time_db.find_one({"_id": "last_run"})
                last_run = last_run_data["time"] if last_run_data else 0
                
                if (int(time.time()) - last_run) >= 86400: # 24 hours
                    u_success, u_failed, g_success, g_failed = await run_promo_broadcast()
                    if LOGGER_ID:
                        stats_text = (
                            f"<tg-emoji emoji-id=\"6039381989985882045\">📢</tg-emoji> **Auto Promo Completed**\n\n"
                            f"<tg-emoji emoji-id=\"6032609071373226027\">👥</tg-emoji> **Users:** <tg-emoji emoji-id=\"6280269890821558384\">✅</tg-emoji> {u_success} | <tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> {u_failed}\n"
                            f"<tg-emoji emoji-id=\"6021618194228187816\">💬</tg-emoji> **Groups:** <tg-emoji emoji-id=\"6280269890821558384\">✅</tg-emoji> {g_success} | <tg-emoji emoji-id=\"6271611232457855630\">❌</tg-emoji> {g_failed}"
                        )
                        await app.send_message(LOGGER_ID, stats_text)
        except:
            pass
        await asyncio.sleep(3600) # Check every 1 hour

# DONO TASKS KO BOT START HOTE HI RUN KARNE KE LIYE
asyncio.create_task(auto_clean())
asyncio.create_task(auto_promo_task())
