import asyncio

from SHIVMUSIC.misc import db
from SHIVMUSIC.utils.database import get_active_chats, is_music_playing

async def timer():
    # 'while True' is cleaner and standard practice for background loops
    while True:
        await asyncio.sleep(1)
        try:
            active_chats = await get_active_chats()
            for chat_id in active_chats:
                # 🟢 THE FIX: Inner try-except taaki ek group ka error baaki groups ka timer na roke
                try:
                    if not await is_music_playing(chat_id):
                        continue
                        
                    playing = db.get(chat_id)
                    # Safe check for empty lists as well
                    if not playing or len(playing) == 0:
                        continue
                        
                    duration = int(playing[0].get("seconds", 0))
                    if duration == 0:
                        continue
                        
                    # 🚀 Safe get and type cast to prevent math errors
                    current_played = int(playing[0].get("played", 0))
                    
                    if current_played >= duration:
                        continue
                        
                    # Safely increment the 'played' value
                    db[chat_id][0]["played"] = current_played + 1
                    
                except Exception:
                    # Ignore the error for this specific chat and move to the next one
                    continue
                    
        except Exception:
            # Main task crash na ho uske liye safety
            pass

asyncio.create_task(timer())
