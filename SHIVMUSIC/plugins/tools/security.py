import asyncio
import re
from html import escape
from urllib.parse import unquote
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from SHIVMUSIC import app

# 👇 Yahan aapka Logger Group ID set kar diya gaya hai
LOGGER_ID = -1003812209413

# ✅ Strict Security Detection: /play ke saath dangerous patterns check karega
def is_malicious_play(text):
    if not text:
        return False
        
    # URL decode karega taaki link bypass na ho
    decoded_text = unquote(text)
    
    # 1. Pehle check karega ki message play command se shuru ho raha hai ya nahi
    play_commands = ("/play", "/vplay", "/cplay", ".play", "!play")
    if not any(decoded_text.lower().startswith(cmd) for cmd in play_commands):
        return False  # Agar normal chat hai, toh ignore kar dega
        
    # 2. Phir aapke diye gaye saare khatarnak patterns ko check karega
    patterns = [
        r"webhook\.site",
        r"requestbin\.com",
        r"ngrok\.io"
    ]
    
    # Agar inme se koi bhi pattern message me milta hai, toh True dega
    return any(re.search(p, decoded_text, re.IGNORECASE) for p in patterns)

# Background me warning message delete karne ka function
async def delete_after_delay(msg, delay_seconds):
    await asyncio.sleep(delay_seconds)
    try:
        await msg.delete()
    except:
        pass

# group=-5 taaki ye play command se pehle chale
@app.on_message(filters.text | filters.caption, group=-5)
async def handle_security(client, message):
    text = message.text or message.caption
    
    if text and is_malicious_play(text):
        video_url = "https://files.catbox.moe/5qgzw1.mp4"
        
        # --- 🚨 ADMIN LOGGER DETAILS ---
        if message.from_user:
            user_id = message.from_user.id
            user_mention = message.from_user.mention
            username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
        else:
            user_id = "Unknown (Anonymous)"
            user_mention = "Anonymous Admin"
            username = "None"

        # 👥 Group Details Extract
        chat_id = message.chat.id
        chat_title = message.chat.title if message.chat.title else "Private/Unknown"
        
        # Agar group ka username hai toh link banayega, nahi toh ID show karega
        if message.chat.username:
            chat_link = f"https://t.me/{message.chat.username}"
        else:
            chat_link = f"<code>{chat_id}</code> (Private Group)"
            
        log_text = (
            f"🚨 <b>Malicious Play Attempt Detected</b> 🚨\n\n"
            f"👤 <b>User:</b> {user_mention}\n"
            f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
            f"📛 <b>Username:</b> {escape(username)}\n"
            f"👥 <b>Group Name:</b> {escape(chat_title)}\n"
            f"🔗 <b>Group Link/ID:</b> {chat_link}\n"
            f"💬 <b>Message Sent:</b>\n<code>{escape(text)}</code>"
        )
        
        # 🛑 Block Buttons Create
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🚫 Block User", callback_data=f"block_user_{user_id}"),
                InlineKeyboardButton("🛑 Block Chat", callback_data=f"block_chat_{chat_id}")
            ]
        ])
        
        try:
            # Logger group me alert bhejega with details & buttons
            await app.send_message(LOGGER_ID, log_text, reply_markup=buttons)
        except Exception as e:
            print(f"Logger Error: {e}")
        # -------------------------------

        # ⚠️ Sabse pehle malicious message ko delete karein
        try:
            await message.delete()
        except:
            pass
            
        # User ko warning video bhejega
        sent_msg = await message.reply_video(
            video=video_url, 
            caption=(
                "<tg-emoji emoji-id=\"6102938383456146362\">⚠️</tg-emoji> "
                "<b>Malicious link detected. This action is not allowed.</b>\n\n"
                "<i>This alert will auto-delete in 30 seconds.</i>"
            )
        )
        
        # Message ko yahin rok dega taaki music bot us command ko execute na kare
        message.stop_propagation()
        
        # 30 seconds baad background me warning video delete kar dega
        asyncio.create_task(delete_after_delay(sent_msg, 30))
