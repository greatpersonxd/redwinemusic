from pyrogram import filters, Client
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus # 🟢 Zaroori Import

import config
from SHIVMUSIC import app
from SHIVMUSIC.core.call import ANJALI
from SHIVMUSIC.misc import db
from SHIVMUSIC.utils.database import set_loop
from SHIVMUSIC.utils.decorators import AdminRightsCheck
from SHIVMUSIC.utils.inline import close_markup
from config import BANNED_USERS

@app.on_message(
    filters.command(
        ["end", "stop", "cend", "cstop"], 
        # 🟢 THE FIX: Removed the empty string "" to prevent random triggers
        prefixes=["/", "!", "#"]
    ) 
    & filters.group 
    & ~BANNED_USERS
)
@AdminRightsCheck
async def stop_music(cli: Client, message: Message, _, chat_id):
    
    # 🟢 THE FIX 2: BULLETPROOF ADMIN CHECK
    # Agar kisi aam user ne gaana stop karne ki koshish ki, toh yeh usko block kar dega
    if message.from_user.id not in config.SUDOERS:
        try:
            member = await cli.get_chat_member(chat_id, message.from_user.id)
            if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                return await message.reply_text("❌ **Sirf Admins he is command ko use kar sakte hain!**")
        except Exception:
            return await message.reply_text("❌ **Error: Admin rights verify nahi ho paye.**")

    if len(message.command) != 1:
        return
        
    # Stream Stop Karega
    await ANJALI.stop_stream(chat_id)
    
    # Loop Reset Karega
    await set_loop(chat_id, 0)
    
    # 🟢 Queue Empty Karega (Safety ke liye)
    try:
        db[chat_id] = []
    except:
        pass
        
    await message.reply_text(
        _["admin_5"].format(message.from_user.mention), reply_markup=close_markup(_)
    )
