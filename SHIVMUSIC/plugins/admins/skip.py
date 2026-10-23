import random
from pyrogram import filters
from pyrogram.types import Message

import config
from SHIVMUSIC import app
from SHIVMUSIC.core.call import ANJALI
from SHIVMUSIC.misc import db

# ✅ Sirf jo zaroori hai wahi import kiya
from SHIVMUSIC.utils.database import get_loop
from SHIVMUSIC.utils.decorators import AdminRightsCheck
from SHIVMUSIC.utils.inline import close_markup
from SHIVMUSIC.utils.stream.autoclear import auto_clean
from config import BANNED_USERS


@app.on_message(
    filters.command(["skip", "cskip", "next", "cnext"], prefixes=["/", "!"]) & filters.group & ~BANNED_USERS
)
@AdminRightsCheck
async def skip(cli, message: Message, _, chat_id):
    # Queue check karte hain
    check = db.get(chat_id)
    if not check:
        return await message.reply_text(_["queue_2"])
        
    # Loop on/off check
    loop = await get_loop(chat_id)
    if loop != 0:
        return await message.reply_text(_["admin_8"])

    # Multi-skip logic (jaise /skip 3)
    if len(message.command) > 1:
        state = message.text.split(None, 1)[1].strip()
        if state.isnumeric():
            state = int(state)
            count = len(check)
            if count > 2:
                count = int(count - 1)
                if 1 <= state <= count:
                    for x in range(state - 1): # (state-1) elements pop karenge
                        try:
                            popped = check.pop(0)
                            if popped:
                                await auto_clean(popped)
                        except:
                            pass
                else:
                    return await message.reply_text(_["admin_11"].format(count))
            else:
                return await message.reply_text(_["admin_10"])
        else:
            return await message.reply_text(_["admin_11"].format(len(check)-1))

    # 🟢 THE REAL FIX FOR THE SCREENSHOT ERROR 🟢
    try:
        # Sahi PyTgCalls client (assistant) nikalte hain taaki internal error na aaye
        pytgcalls_client = ANJALI.one
        if chat_id in ANJALI.active_clients:
            val = ANJALI.active_clients[chat_id]
            if isinstance(val, list) and len(val) > 0:
                pytgcalls_client = val[0]
            elif val and not isinstance(val, list):
                pytgcalls_client = val
                
        # 🔥 Pura lamba code replace karke seedha change_stream call
        # Yeh khud current track pop karega, agla play karega aur message bhejega.
        # Queue khali hui toh automatically Autoplay handle kar lega.
        await ANJALI.change_stream(pytgcalls_client, chat_id)
        
    except Exception as e:
        # Agar koi error aata hai toh gracefully stop kar denge
        try:
            await message.reply_text(
                text=_["admin_6"].format(message.from_user.mention, message.chat.title),
                reply_markup=close_markup(_)
            )
            await ANJALI.stop_stream(chat_id)
        except:
            pass
