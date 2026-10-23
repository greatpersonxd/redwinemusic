from pyrogram import filters, Client
from pyrogram.types import Message
from SHIVMUSIC.core.call import ANJALI
from SHIVMUSIC.utils.database import is_music_playing, music_off
from SHIVMUSIC.utils.decorators import AdminRightsCheck
from SHIVMUSIC.utils.inline import close_markup
from config import BANNED_USERS

# 🟢 THE FIX 1: @app ki jagah @Client use kiya, taaki Main aur Clone dono kaam karein
@Client.on_message(filters.command(["pause", "cpause"]) & filters.group & ~BANNED_USERS)
@AdminRightsCheck
async def pause_admin(cli: Client, message: Message, _, chat_id):
    # Queue status check
    if not await is_music_playing(chat_id):
        return await message.reply_text(_["admin_1"])
        
    await ANJALI.pause_stream(chat_id)
    await music_off(chat_id)
    
    # Success message
    await message.reply_text(
        _["admin_2"].format(message.from_user.mention), reply_markup=close_markup(_)
    )
