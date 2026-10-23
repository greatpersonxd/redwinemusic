import asyncio
import random
import math
from pyrogram.types import CallbackQuery, InputMediaPhoto, InputMediaVideo, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import filters
from pyrogram.errors import WebpageMediaEmpty
from pyrogram.enums import ButtonStyle, ChatMemberStatus, ParseMode

from SHIVMUSIC import YouTube, app
from SHIVMUSIC.core.call import ANJALI
from SHIVMUSIC.misc import SUDOERS, db
from SHIVMUSIC.utils.database import (
    get_active_chats, get_lang, get_upvote_count, is_active_chat,
    is_music_playing, is_nonadmin_chat, music_off, music_on, set_loop, get_assistant,
    is_autoplay_on, autoplay_on, autoplay_off
)

from SHIVMUSIC.utils.decorators.language import languageCB
from SHIVMUSIC.utils.formatters import seconds_to_min
from SHIVMUSIC.utils.inline import close_markup, stream_markup, stream_markup_timer
from SHIVMUSIC.utils.stream.autoclear import auto_clean
from SHIVMUSIC.utils.thumbnails import get_thumb
import config
from config import (
    BANNED_USERS, SOUNCLOUD_IMG_URL, STREAM_IMG_URL, TELEGRAM_AUDIO_URL,
    TELEGRAM_VIDEO_URL, START_IMG_URL, adminlist, confirmer, votemode
)
from strings import get_string
from SHIVMUSIC.utils.inline.start import private_panel
from SHIVMUSIC.utils.html_builder import build_welcome_html

checker = {}
upvoters = {}

# 💎 Premium Emojis ID List
PREMIUM_EMOJIS = [
    5258362837411045098, 6102938383456146362, 5463274047771000031, 6100397162976252509,
    5373310679241466020, 5408916593780470262, 5776182936638329359, 5258389041006518073,
    6280269890821558384, 5936143551854285132, 6172332822892647766, 5891211339170326418,
    5409368076447657845, 6172312314423808834, 6082387600599944892, 6271537028307881531
]

# 🎨 Dynamic Color Generator
def get_style_map():
    styles = [ButtonStyle.PRIMARY, ButtonStyle.SUCCESS, ButtonStyle.DANGER]
    random.shuffle(styles)
    return {1: styles[0], 2: styles[1], 3: styles[2], 4: styles[0]}

# 🔘 Smart Button Creator
def create_btn(text, cb=None, url=None, style=ButtonStyle.PRIMARY, emoji_id=None, no_emoji=False):
    kwargs = {"text": text, "style": style}
    if cb: kwargs["callback_data"] = cb
    if url: kwargs["url"] = url
    
    # Premium Emoji Logic
    if emoji_id:
        kwargs["icon_custom_emoji_id"] = int(emoji_id)
    elif not no_emoji:
        kwargs["icon_custom_emoji_id"] = int(random.choice(PREMIUM_EMOJIS))
        
    return InlineKeyboardButton(**kwargs)

@app.on_callback_query(filters.regex("settingsback_helper") & ~BANNED_USERS)
@languageCB
async def settings_back_helper(client, CallbackQuery, _):
    try:
        await CallbackQuery.answer()
    except:
        pass

    if isinstance(START_IMG_URL, list):
        img = random.choice(START_IMG_URL)
    else:
        img = START_IMG_URL

    await CallbackQuery.edit_message_media(
        media=InputMediaPhoto(
            media=img,
            caption=build_welcome_html(
                CallbackQuery.from_user.mention, app.mention, app.username
            ),
            parse_mode=ParseMode.HTML,
        ),
        reply_markup=InlineKeyboardMarkup(private_panel(_))
    )

@app.on_callback_query(filters.regex("support_page") & ~BANNED_USERS)
@languageCB
async def support_page_cb(client, CallbackQuery, _):
    await CallbackQuery.answer()
    style_map = get_style_map()
    support_text = (
        f"<blockquote><b><tg-emoji emoji-id=\"6172312314423808834\">✨</tg-emoji> ᴡєʟᴄσϻє ᴛσ ᴛʜє sυᴘᴘσʀᴛ ϻєηυ <tg-emoji emoji-id=\"6172312314423808834\">✨</tg-emoji></b>\n\n"
        f"<b>ɪғ ʏσυ ηєєᴅ ᴧηʏ ʜєʟᴘ ʀєɢᴧʀᴅɪηɢ ᴛʜє ʙσᴛ σʀ ᴡᴧηᴛ ᴛσ ʀєᴘσʀᴛ ᴧ ʙυɢ, "
        f"ᴊσɪη συʀ sυᴘᴘσʀᴛ ᴄʜᴧᴛ σʀ ᴄʜᴧηηєʟ ʙєʟσᴡ.</b></blockquote>"
    )

    custom_support_buttons = [
        [
            create_btn(text="υᴘᴅᴧᴛєs", url="https://t.me/betabot_hub", style=style_map[1], emoji_id=6039381989985882045),
            create_btn(text="sυᴘᴘσʀᴛ", url="https://t.me/betabot_support", style=style_map[2], emoji_id=6021618194228187816)
        ],
        [
            create_btn(text="ʙσᴛs", url="https://t.me/betabot_hub/6701", style=style_map[3], emoji_id=5355051922862653659)
        ],
        [
            create_btn(text="ʙᴧᴄᴋ", cb="settingsback_helper", style=style_map[4], emoji_id=5352759161945867747)
        ]
    ]

    await CallbackQuery.edit_message_media(
        media=InputMediaPhoto(
            media="https://files.catbox.moe/4hl7n8.jpg", 
            caption=support_text
        ),
        reply_markup=InlineKeyboardMarkup(custom_support_buttons)
    )

@app.on_callback_query(filters.regex("gib_source"))
async def gib_repo_callback(_, callback_query):
    try:
        image_url = "https://h.uguu.se/eJnvkhyK.jpg"
        style_map = get_style_map()
        await callback_query.edit_message_media(
            media=InputMediaPhoto(
                media=image_url, 
                caption=f"<blockquote><b><tg-emoji emoji-id=\"5258389041006518073\">📂</tg-emoji> ʀєᴘσ = ||ɪsᴛᴋʜᴧʀ ᴧηᴅ ᴅєᴠɪʟ ᴋσ ᴘᴧᴘᴧ ʙσʟ ᴄʜᴧʟ ʙσʟ😎||</b></blockquote>"
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        create_btn(text="ʙᴧᴄᴋ", cb="settingsback_helper", style=style_map[1], emoji_id=5352759161945867747),
                        create_btn(text="ᴄʟσsє", cb="close", style=style_map[2], emoji_id=6271611232457855630)
                    ]
                ]
            ),
        )
    except Exception as e:
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)

@app.on_callback_query(filters.regex("unban_assistant"))
async def unban_assistant(_, callback: CallbackQuery):
    chat_id = callback.message.chat.id
    userbot = await get_assistant(chat_id)
    try:
        await app.unban_chat_member(chat_id, userbot.id)
        await callback.answer("✅ ᴧssɪsᴛᴧηᴛ υηʙᴧηηєᴅ sυᴄᴄєssғυʟʟʏ!", show_alert=True)
    except Exception:
        await callback.answer("❌ ғᴧɪʟєᴅ ᴛσ υηʙᴧη. ɢɪᴠє ϻє ᴧᴅϻɪη ᴘєʀϻɪssɪσηs.", show_alert=True)

@app.on_callback_query(filters.regex("ADMIN") & ~BANNED_USERS)
@languageCB
async def del_back_playlist(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    command, chat = callback_request.split("|")
    if "_" in str(chat):
        bet = chat.split("_")
        chat = bet[0]
        counter = bet[1]
    chat_id = int(chat)
    if not await is_active_chat(chat_id):
        return await CallbackQuery.answer(_["general_5"], show_alert=True)
    mention = CallbackQuery.from_user.mention
    style_map = get_style_map()

    if command == "UpVote":
        if chat_id not in votemode: votemode[chat_id] = {}
        if chat_id not in upvoters: upvoters[chat_id] = {}

        voters = (upvoters[chat_id]).get(CallbackQuery.message.id)
        if not voters: upvoters[chat_id][CallbackQuery.message.id] = []

        vote = (votemode[chat_id]).get(CallbackQuery.message.id)
        if not vote: votemode[chat_id][CallbackQuery.message.id] = 0

        if CallbackQuery.from_user.id in upvoters[chat_id][CallbackQuery.message.id]:
            (upvoters[chat_id][CallbackQuery.message.id]).remove(CallbackQuery.from_user.id)
            votemode[chat_id][CallbackQuery.message.id] -= 1
        else:
            (upvoters[chat_id][CallbackQuery.message.id]).append(CallbackQuery.from_user.id)
            votemode[chat_id][CallbackQuery.message.id] += 1

        upvote = await get_upvote_count(chat_id)
        get_upvotes = int(votemode[chat_id][CallbackQuery.message.id])

        if get_upvotes >= upvote:
            votemode[chat_id][CallbackQuery.message.id] = upvote
            try:
                exists = confirmer[chat_id][CallbackQuery.message.id]
                current = db[chat_id][0]
                if current["vidid"] != exists["vidid"] or current["file"] != exists["file"]:
                    return await CallbackQuery.edit_message_text(_["admin_35"])
            except:
                return await CallbackQuery.edit_message_text(_["admin_36"])
            try:
                await CallbackQuery.edit_message_text(_["admin_37"].format(upvote))
            except:
                pass
            command = counter
            mention = "υᴘᴠσᴛєs"
        else:
            if CallbackQuery.from_user.id in upvoters[chat_id][CallbackQuery.message.id]:
                await CallbackQuery.answer(_["admin_38"], show_alert=True)
            else:
                await CallbackQuery.answer(_["admin_39"], show_alert=True)

            upl = InlineKeyboardMarkup([
                [create_btn(text=f"{get_upvotes}", cb=f"ADMIN  UpVote|{chat_id}_{counter}", style=style_map[1], emoji_id=6041720006973067267)]
            ])
            await CallbackQuery.answer(_["admin_40"], show_alert=True)
            return await CallbackQuery.edit_message_reply_markup(reply_markup=upl)
    else:
        is_non_admin = await is_nonadmin_chat(CallbackQuery.message.chat.id)
        if not is_non_admin:
            if CallbackQuery.from_user.id not in SUDOERS:
                admins = adminlist.get(CallbackQuery.message.chat.id)
                allowed = bool(admins and CallbackQuery.from_user.id in admins)
                if not allowed:
                    try:
                        member = await client.get_chat_member(
                            CallbackQuery.message.chat.id,
                            CallbackQuery.from_user.id,
                        )
                        allowed = member.status in (
                            ChatMemberStatus.ADMINISTRATOR,
                            ChatMemberStatus.OWNER,
                        )
                    except Exception:
                        allowed = False
                if not allowed:
                    return await CallbackQuery.answer(_["admin_14"], show_alert=True)

    if command == "Pause":
        if not await is_music_playing(chat_id): return await CallbackQuery.answer(_["admin_1"], show_alert=True)
        await CallbackQuery.answer()
        await ANJALI.pause_stream(chat_id)
        await music_off(chat_id)
        await CallbackQuery.message.reply_text(_["admin_2"].format(mention), reply_markup=close_markup(_))
    elif command == "Resume":
        if await is_music_playing(chat_id): return await CallbackQuery.answer(_["admin_3"], show_alert=True)
        await CallbackQuery.answer()
        await ANJALI.resume_stream(chat_id)
        await music_on(chat_id)
        await CallbackQuery.message.reply_text(_["admin_4"].format(mention), reply_markup=close_markup(_))
    elif command == "Stop" or command == "End":
        await CallbackQuery.answer()
        await ANJALI.stop_stream(chat_id)
        await set_loop(chat_id, 0)
        await CallbackQuery.message.reply_text(_["admin_5"].format(mention), reply_markup=close_markup(_))
        await CallbackQuery.message.delete()
    elif command == "Autoplay":
        state = await is_autoplay_on(chat_id)
        if state:
            await autoplay_off(chat_id)
            await CallbackQuery.answer("🔴 ᴧυᴛσᴘʟᴧʏ ᴅɪsᴧʙʟєᴅ!", show_alert=True)
            await CallbackQuery.message.reply_text(
                f"<blockquote><b><tg-emoji emoji-id=\"5318840353510408444\">🔴</tg-emoji> <tg-emoji emoji-id=\"6082387600599944892\">🎧</tg-emoji> ᴧυᴛσᴘʟᴧʏ sʏsᴛєϻ</b>\n\n<b>ᴧυᴛσᴘʟᴧʏ ғσʀ ᴛʜɪs ɢʀσυᴘ ɪs ησᴡ ᴅɪsᴧʙʟєᴅ <tg-emoji emoji-id=\"5318840353510408444\">🔴</tg-emoji>.</b>\n└ <b>ʙʏ :</b> {mention}</blockquote>",
                 reply_markup=close_markup(_)
            )
        else:
            await autoplay_on(chat_id)
            await CallbackQuery.answer("🟢 ᴧυᴛσᴘʟᴧʏ єηᴧʙʟєᴅ!", show_alert=True)
            await CallbackQuery.message.reply_text(
                f"<blockquote><b><tg-emoji emoji-id=\"6113685078825505075\">🟢</tg-emoji> <tg-emoji emoji-id=\"6082387600599944892\">🎧</tg-emoji> ᴧυᴛσᴘʟᴧʏ sʏsᴛєϻ</b>\n\n<b>ᴧυᴛσᴘʟᴧʏ ғσʀ ᴛʜɪs ɢʀσυᴘ ɪs ησᴡ єηᴧʙʟєᴅ <tg-emoji emoji-id=\"6113685078825505075\">🟢</tg-emoji>.</b>\n└ <b>ʙʏ :</b> {mention}</blockquote>",
                  reply_markup=close_markup(_)
            )
    elif command == "Skip" or command == "Replay":
        check = db.get(chat_id)
        if not check or len(check) == 0:
            return await CallbackQuery.answer("ǫυєυє ɪs єϻᴘᴛʏ σʀ ᴛʜє ᴘʟᴧʏʟɪsᴛ ʜᴧs ʙєєη ᴄʟєᴧʀєᴅ!", show_alert=True)

        if command == "Skip":
            txt = f"<blockquote><b><tg-emoji emoji-id=\"5850346984501680054\">▶️</tg-emoji> ➻ sᴛʀєᴧϻ sᴋɪᴘᴘєᴅ <tg-emoji emoji-id=\"6172273586703700991\">🥀</tg-emoji></b>\n│ \n└<b>ʙʏ :</b> {mention}</blockquote>"
            try:
                popped = check.pop(0)
                if popped: await auto_clean(popped)
                if not check:
                    await CallbackQuery.edit_message_text(txt)
                    await CallbackQuery.message.reply_text(_["admin_6"].format(mention, CallbackQuery.message.chat.title), reply_markup=close_markup(_))
                    return await ANJALI.stop_stream(chat_id)
            except:
                return await ANJALI.stop_stream(chat_id)
        else:
            txt = f"<blockquote><b><tg-emoji emoji-id=\"5960671702059848143\">⬅️</tg-emoji> ➻ sᴛʀєᴧϻ ʀє-ᴘʟᴧʏєᴅ <tg-emoji emoji-id=\"6172273586703700991\">🥀</tg-emoji></b>\n│ \n└<b>ʙʏ :</b> {mention}</blockquote>"

        await CallbackQuery.answer()
        queued = check[0]["file"]
        title = (check[0]["title"]).title()
        user = check[0]["by"]
        duration = check[0]["dur"]
        streamtype = check[0]["streamtype"]
        videoid = check[0]["vidid"]
        status = True if str(streamtype) == "video" else None
        db[chat_id][0]["played"] = 0

        try:
            image = await YouTube.thumbnail(videoid, True)
        except:
            image = None

        try:
            if "live_" in queued:
                n, link = await YouTube.video(videoid, True)
                if n == 0: return await CallbackQuery.message.reply_text(_["admin_7"].format(title))
                await ANJALI.skip_stream(chat_id, link, video=status, image=image)
            elif "vid_" in queued:
                 await ANJALI.skip_stream(chat_id, queued, video=status, image=image)
            else:
                 await ANJALI.skip_stream(chat_id, queued, video=status, image=image)
        except:
            return await CallbackQuery.message.reply_text(_["call_6"])

        button = stream_markup(_, chat_id)
        img = await get_thumb(videoid, CallbackQuery.from_user.id, client)
        run = await CallbackQuery.message.reply_photo(
            photo=img if img else STREAM_IMG_URL,
            caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{videoid}", title[:23], duration, user),
            reply_markup=InlineKeyboardMarkup(button),
        )
        if chat_id in db and len(db[chat_id]) > 0:
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
        await CallbackQuery.edit_message_text(txt, reply_markup=close_markup(_))

async def markup_timer():
    while not await asyncio.sleep(7):
        active_chats = await get_active_chats()
        for chat_id in active_chats:
            try:
                if not await is_music_playing(chat_id): continue
                playing = db.get(chat_id)
                if not playing or int(playing[0]["seconds"]) == 0: continue
                mystic = playing[0]["mystic"]
                try:
                    if checker[chat_id][mystic.id] is False: continue
                except: pass

                try:
                    language = await get_lang(chat_id)
                    _ = get_string(language)
                except: _ = get_string("en")

                try:
                    buttons = stream_markup_timer(_, chat_id, seconds_to_min(playing[0]["played"]), playing[0]["dur"])
                    await mystic.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))
                except: continue
            except: continue

asyncio.create_task(markup_timer()) 

@app.on_message(filters.video & filters.private)
async def get_my_own_file_id(client, message):
    await message.reply_text(f"<blockquote><b><tg-emoji emoji-id=\"5409143496902716934\">🖼</tg-emoji> ϻєʀᴧ ᴠɪᴅєσ ғɪʟє ɪᴅ (ɪsᴋσ ᴄσᴘʏ ᴋᴧʀσ) :</b>\n<code>{message.video.file_id}</code></blockquote>")
