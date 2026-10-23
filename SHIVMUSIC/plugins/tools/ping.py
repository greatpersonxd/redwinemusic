import random 
from datetime import datetime

from pyrogram import filters
from pyrogram.types import Message

from SHIVMUSIC import app
from SHIVMUSIC.core.call import ANJALI
from SHIVMUSIC.utils import bot_sys_stats
from SHIVMUSIC.utils.decorators.language import language
from SHIVMUSIC.utils.inline import supp_markup
from config import BANNED_USERS, PING_IMG_URL


@app.on_message(
    filters.command(["ping", "alive"], prefixes=["/", "!", "#"]) 
    & ~BANNED_USERS
)
@language
async def ping_com(client, message: Message, _):
    start = datetime.now()
    
    # --- RANDOM IMAGE LOGIC ---
    if isinstance(PING_IMG_URL, list):
        response_img = random.choice(PING_IMG_URL)
    else:
        response_img = PING_IMG_URL

    # Pehle loading wala photo caption bhejenge
    response = await message.reply_photo(
        photo=response_img, 
        caption=_["ping_1"].format(app.mention),
    )
    
    # Stats calculate kar rahe hain
    pytgping = await ANJALI.ping()
    UP, CPU, RAM, DISK = await bot_sys_stats()
    resp = (datetime.now() - start).microseconds / 1000
    
    # 🟢 THE FIX: Photo ke text ko badalne ke liye 'edit_caption' use hota hai
    await response.edit_caption(
        caption=_["ping_2"].format(resp, app.mention, UP, RAM, CPU, DISK, pytgping),
        reply_markup=supp_markup(_),
    )
