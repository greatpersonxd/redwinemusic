import asyncio
from pyrogram import filters, Client
from pyrogram.types import Message

from SHIVMUSIC import YouTube, app
from SHIVMUSIC.core.call import ANJALI
from SHIVMUSIC.misc import db
from SHIVMUSIC.utils.formatters import seconds_to_min
from SHIVMUSIC.utils import AdminRightsCheck
from SHIVMUSIC.utils.inline import close_markup
from config import BANNED_USERS

@app.on_message(
    # 🟢 THE FIX: Custom prefixes add kar diye hain yahan
    filters.command(["seek", "cseek", "seekback", "cseekback"], prefixes=["/", "!", "#"])
    & filters.group
    & ~BANNED_USERS
)
@AdminRightsCheck
async def seek_comm(cli, message: Message, _, chat_id):
    if len(message.command) == 1:
        return await message.reply_text(_["admin_20"])
        
    query = message.text.split(None, 1)[1].strip()
    if not query.isnumeric():
        return await message.reply_text(_["admin_21"])
    
    # Queue check
    playing = db.get(chat_id)
    if not playing:
        return await message.reply_text(_["queue_2"])
        
    # Duration variables
    duration_seconds = int(playing[0].get("seconds", 0))
    duration_played = int(playing[0].get("played", 0))
    duration_to_skip = int(query)
    duration_str = playing[0].get("dur", "0:00")
    
    if duration_seconds == 0:
        return await message.reply_text(_["admin_22"])
        
    # Command type detection (cseek/cseekback = backward)
    is_backward = message.command[0].startswith("c")
    
    # Calculate target time
    if is_backward:
        to_seek = duration_played - duration_to_skip
        if to_seek < 0: to_seek = 0
    else:
        to_seek = duration_played + duration_to_skip
        if to_seek > duration_seconds: to_seek = duration_seconds - 5
    
    # Safety: Start ya End ke bahut close ho toh skip na karein
    if abs(duration_played - to_seek) < 10:
         return await message.reply_text(
            text=_["admin_23"].format(seconds_to_min(duration_played), duration_str),
            reply_markup=close_markup(_),
        )

    mystic = await message.reply_text(_["admin_24"])
    
    # File path setup
    file_path = playing[0].get("file", "")
    if "vid_" in file_path:
        n, file_path = await YouTube.video(playing[0]["vidid"], True)
        if n == 0: return await message.reply_text(_["admin_22"])
            
    speed_path = playing[0].get("speed_path")
    if speed_path: file_path = speed_path
        
    if "index_" in file_path:
        file_path = playing[0]["vidid"]
        
    try:
        # Seek stream
        await ANJALI.seek_stream(
            chat_id,
            file_path,
            seconds_to_min(to_seek),
            duration_str,
            playing[0]["streamtype"],
        )
    except Exception as e:
        return await mystic.edit_text(_["admin_26"], reply_markup=close_markup(_))
        
    # Database update
    db[chat_id][0]["played"] = to_seek
        
    await mystic.edit_text(
        text=_["admin_25"].format(seconds_to_min(to_seek), message.from_user.mention),
        reply_markup=close_markup(_),
    )
