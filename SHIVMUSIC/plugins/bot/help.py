import random
from typing import Union
from pyrogram import filters, types, enums
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, Message, InlineKeyboardButton
from SHIVMUSIC import app
from SHIVMUSIC.utils import help_pannel
from SHIVMUSIC.utils.database import get_lang
from SHIVMUSIC.utils.decorators.language import LanguageStart, languageCB
from SHIVMUSIC.utils.inline.help import help_back_markup, private_help_panel
from config import BANNED_USERS, START_IMG_URL, SUPPORT_CHAT
from strings import get_string, helpers
from SHIVMUSIC.utils.stuffs.helper import Helper

# ✅ Helper to safe get Random Image
def get_random_start_img():
    if START_IMG_URL:
        if isinstance(START_IMG_URL, list):
            return random.choice(START_IMG_URL)
        return START_IMG_URL
    return "https://telegra.ph/file/2e3d368e77c449c287430.jpg" # Fallback

@app.on_message(filters.command(["help"]) & filters.private & ~BANNED_USERS)
@app.on_callback_query(filters.regex("^help_home$") & ~BANNED_USERS)
async def helper_private(
    client: app, update: Union[types.Message, types.CallbackQuery]
):
    is_callback = isinstance(update, types.CallbackQuery)
    if is_callback:
        try:
            await update.answer()
        except:
            pass
        chat_id = update.message.chat.id
        language = await get_lang(chat_id)
        _ = get_string(language)
        keyboard = help_pannel(_, True)
        
        # Callback just edits text, no spoiler needed here
        await update.edit_message_caption(
            _["help_1"].format(SUPPORT_CHAT),
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
    else:
        try:
            await update.delete()
        except:
            pass
        language = await get_lang(update.chat.id)
        _ = get_string(language)
        keyboard = help_pannel(_)
        
        # ✅ Random Photo + Spoiler Logic
        await update.reply_photo(
            photo=get_random_start_img(),
            caption=_["help_1"].format(SUPPORT_CHAT),
            reply_markup=keyboard,
            has_spoiler=True, # ✨ Spoiler Added
            parse_mode=ParseMode.HTML,
        )


@app.on_message(filters.command(["help"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def help_com_group(client, message: Message, _):
    keyboard = private_help_panel(_)
    # ✅ FIX: Removed the redundant InlineKeyboardMarkup() wrapper
    await message.reply_text(_["help_2"], reply_markup=keyboard)


@app.on_callback_query(filters.regex("help_callback") & ~BANNED_USERS)
@languageCB
async def helper_cb(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    cb = callback_data.split(None, 1)[1]
    keyboard = help_back_markup(_)
    
    if cb == "hb1":
        await CallbackQuery.edit_message_caption(helpers.HELP_1, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif cb == "hb2":
        await CallbackQuery.edit_message_caption(helpers.HELP_2, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif cb == "hb3":
        await CallbackQuery.edit_message_caption(helpers.HELP_3, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif cb == "hb4":
        await CallbackQuery.edit_message_caption(helpers.HELP_4, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif cb == "hb5":
        await CallbackQuery.edit_message_caption(helpers.HELP_5, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif cb == "hb6":
        await CallbackQuery.edit_message_caption(helpers.HELP_6, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif cb == "hb7":
        await CallbackQuery.edit_message_caption(helpers.HELP_7, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif cb == "hb8":
        await CallbackQuery.edit_message_caption(helpers.HELP_8, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif cb == "hb9":
        await CallbackQuery.edit_message_caption(helpers.HELP_9, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif cb == "hb10":
        await CallbackQuery.edit_message_caption(helpers.HELP_10, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif cb == "hb11":
        await CallbackQuery.edit_message_caption(helpers.HELP_11, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif cb == "hb12":
        await CallbackQuery.edit_message_caption(helpers.HELP_12, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif cb == "hb13":
        await CallbackQuery.edit_message_caption(helpers.HELP_13, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif cb == "hb14":
        await CallbackQuery.edit_message_caption(helpers.HELP_14, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    elif cb == "hb15":
        await CallbackQuery.edit_message_caption(helpers.HELP_15, reply_markup=keyboard, parse_mode=ParseMode.HTML)


@app.on_callback_query(filters.regex('managebot123'))
async def on_back_button(client, CallbackQuery):
    callback_data = CallbackQuery.data.strip()
    cb = callback_data.split(None, 1)[1]
    
    # We need to get language here to pass to help_pannel
    language = await get_lang(CallbackQuery.message.chat.id)
    _ = get_string(language)
    
    keyboard = help_pannel(_, True)
    if cb == "settings_back_helper":
        await CallbackQuery.edit_message_text(
            _["help_1"].format(SUPPORT_CHAT),
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )

@app.on_callback_query(filters.regex('mplus'))      
async def mb_plugin_button(client, CallbackQuery):
    callback_data = CallbackQuery.data.strip()
    cb = callback_data.split(None, 1)[1]
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("ʙᴀᴄᴋ", callback_data=f"mbot_cb")]])
    if cb == "Okieeeeee":
        await CallbackQuery.edit_message_text(
            "<code>Something went wrong.</code>",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
    else:
        await CallbackQuery.edit_message_text(getattr(Helper, cb), reply_markup=keyboard)
