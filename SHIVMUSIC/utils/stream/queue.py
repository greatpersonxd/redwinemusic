import asyncio
from typing import Union

from SHIVMUSIC.misc import db
from SHIVMUSIC.utils.formatters import check_duration, seconds_to_min
from config import autoclean, time_to_seconds


async def put_queue(
    chat_id,
    original_chat_id,
    file,
    title,
    duration,
    user,
    vidid,
    user_id,
    stream,
    forceplay: Union[bool, str] = None,
    source: str = "youtube", # 🟢 PREP: Ready for Spotify/AppleMusic/SoundCloud fallback
):
    title = title.title()
    try:
        duration_in_seconds = time_to_seconds(duration) - 3
    except:
        duration_in_seconds = 0
        
    put = {
        "title": title,
        "dur": duration,
        "streamtype": stream,
        "by": user,
        "user_id": user_id,
        "chat_id": original_chat_id,
        "file": file,
        "vidid": vidid,
        "seconds": duration_in_seconds,
        "played": 0,
        "source": source, 
    }
    
    # 🚀 THE FIX: Prevent KeyError on first song queue
    if chat_id not in db:
        db[chat_id] = []
        
    if forceplay:
        db[chat_id].insert(0, put)
    else:
        db[chat_id].append(put)
        
    autoclean.append(file)


async def put_queue_index(
    chat_id,
    original_chat_id,
    file,
    title,
    duration,
    user,
    vidid,
    stream,
    forceplay: Union[bool, str] = None,
    source: str = "index_url", 
):
    if "20.212.146.162" in vidid:
        try:
            dur = await asyncio.get_running_loop().run_in_executor(
                None, check_duration, vidid
            )
            duration = seconds_to_min(dur)
        except:
            duration = "ᴜʀʟ sᴛʀᴇᴀᴍ"
            dur = 0
    else:
        dur = 0
        
    put = {
        "title": title,
        "dur": duration,
        "streamtype": stream,
        "by": user,
        "user_id": 0, # 🚀 THE FIX: Added fallback user_id to prevent UI crash
        "chat_id": original_chat_id,
        "file": file,
        "vidid": vidid,
        "seconds": dur,
        "played": 0,
        "source": source,
    }
    
    # 🚀 THE FIX: Prevent KeyError on first song queue
    if chat_id not in db:
        db[chat_id] = []
        
    if forceplay:
        db[chat_id].insert(0, put)
    else:
        db[chat_id].append(put)
