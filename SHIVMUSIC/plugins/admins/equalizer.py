"""
🎚 Equalizer plugin — DJ Bass, 8D, Lo-Fi, Clear Audio and more.

Opened from the middle button of the 5 playback controls (old replay button)
or with /eq | /equalizer in the group.
"""

import asyncio

from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus

from SHIVMUSIC import app
from SHIVMUSIC.core.call import ANJALI
from SHIVMUSIC.misc import SUDOERS, db
from SHIVMUSIC.utils import AdminRightsCheck
from SHIVMUSIC.utils.database import is_active_chat, is_music_playing, is_nonadmin_chat
from SHIVMUSIC.utils.decorators.language import languageCB
from SHIVMUSIC.utils.equalizer import (
    equalizer_markup,
    get_chat_eq,
    get_chat_volume,
    get_eq_name,
    reset_chat_audio,
    set_chat_eq,
    set_chat_volume,
    volume_markup,
)
from SHIVMUSIC.utils.inline import close_markup
from config import BANNED_USERS, adminlist

busy = []
FEEDBACK_TTL = 30


async def _delete_later(message, delay=FEEDBACK_TTL):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass


async def _send_feedback(callback, text, _, *, alert_text=None):
    """Show both a Telegram alert and a temporary in-chat confirmation."""
    if alert_text:
        try:
            await callback.answer(alert_text, show_alert=True)
        except Exception:
            pass
    try:
        reply = await callback.message.reply_text(text, reply_markup=close_markup(_))
        asyncio.create_task(_delete_later(reply))
        return reply
    except Exception:
        return None


def panel_text(chat_id) -> str:
    return (
        "<blockquote><b><tg-emoji emoji-id=\"5217933090483098080\">🎚</tg-emoji> "
        "єǫυᴧʟɪᴢєʀ ᴘᴧηєʟ</b>\n│\n"
        f"├ <b>ᴄυʀʀєηᴛ :</b> <code>{get_eq_name(get_chat_eq(chat_id))}</code>\n"
        "└ <b>ᴘɪᴄᴋ ᴧη єғғєᴄᴛ — ᴛʀᴧᴄᴋ ᴋєєᴘs ᴘʟᴧʏɪηɢ ғʀσϻ ᴛʜє sᴧϻє ᴛɪϻє-sᴛᴧϻᴘ, ησ ʀєsᴛᴧʀᴛ.</b></blockquote>"
    )


def volume_panel_text(chat_id) -> str:
    return (
        "<blockquote><b>🔊 ᴠᴏʟᴜᴍᴇ ᴘᴀɴᴇʟ</b>\n│\n"
        f"├ <b>ᴄᴜʀʀᴇɴᴛ :</b> <code>{get_chat_volume(chat_id)}%</code>\n"
        "└ <b>+50 / -25 controls · boost +500 · maximum 1000%</b></blockquote>"
    )


async def _is_allowed(CallbackQuery) -> bool:
    """Admins / sudoers only (unless the chat runs in non-admin mode)."""
    if await is_nonadmin_chat(CallbackQuery.message.chat.id):
        return True
    if CallbackQuery.from_user.id in SUDOERS:
        return True
    admins = adminlist.get(CallbackQuery.message.chat.id)
    if admins and CallbackQuery.from_user.id in admins:
        return True
    try:
        member = await app.get_chat_member(
            CallbackQuery.message.chat.id, CallbackQuery.from_user.id
        )
        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
    except Exception:
        return False


@app.on_message(
    filters.command(["eq", "equalizer", "ceq", "cequalizer"], prefixes=["/", "!", "#"])
    & filters.group
    & ~BANNED_USERS
)
@AdminRightsCheck
async def equalizer_command(cli, message: Message, _, chat_id):
    if not db.get(chat_id):
        return await message.reply_text(_["queue_2"])
    return await message.reply_text(
        text=panel_text(chat_id),
        reply_markup=equalizer_markup(_, chat_id),
    )


# 🎚 Middle player button -> open equalizer panel
@app.on_callback_query(filters.regex("EqPanel") & ~BANNED_USERS)
@languageCB
async def equalizer_panel_cb(client, CallbackQuery, _):
    chat = CallbackQuery.data.strip().split(None, 1)[1]
    chat_id = int(chat)

    if not await is_active_chat(chat_id):
        return await CallbackQuery.answer(_["general_5"], show_alert=True)
    if not await _is_allowed(CallbackQuery):
        return await CallbackQuery.answer(_["admin_14"], show_alert=True)

    await CallbackQuery.answer("🎚 єǫυᴧʟɪᴢєʀ σᴘєηєᴅ !")
    await CallbackQuery.message.reply_text(
        text=panel_text(chat_id),
        reply_markup=equalizer_markup(_, chat_id),
    )


# 🎚 Apply the selected preset
@app.on_callback_query(filters.regex("EqSet") & ~BANNED_USERS)
@languageCB
async def equalizer_set_cb(client, CallbackQuery, _):
    callback_request = CallbackQuery.data.strip().split(None, 1)[1]
    chat, preset = callback_request.split("|")
    chat_id = int(chat)

    if not await is_active_chat(chat_id):
        return await CallbackQuery.answer(_["general_5"], show_alert=True)
    if not await _is_allowed(CallbackQuery):
        return await CallbackQuery.answer(_["admin_14"], show_alert=True)
    if not db.get(chat_id):
        return await CallbackQuery.answer(_["queue_2"], show_alert=True)
    if chat_id in busy:
        return await CallbackQuery.answer("⏳ ᴡᴀɪᴛ, ᴀɴᴏᴛʜᴇʀ ᴇғғᴇᴄᴛ ɪs ʙᴇɪɴɢ ᴀᴘᴘʟɪᴇᴅ...", show_alert=True)

    # Paused stream: just remember the preset, it will kick in on resume.
    if not await is_music_playing(chat_id):
        set_chat_eq(chat_id, preset)
        try:
            await CallbackQuery.edit_message_text(
                panel_text(chat_id), reply_markup=equalizer_markup(_, chat_id)
            )
        except Exception:
            pass
        return await _send_feedback(
            CallbackQuery,
            f"<blockquote><b>🎚 {get_eq_name(preset)} sᴧᴠєᴅ.</b>\n"
            "└ <i>It will apply when playback resumes.</i></blockquote>",
            _,
            alert_text=f"🎚 {get_eq_name(preset)} saved.",
        )

    busy.append(chat_id)

    try:
        await ANJALI.equalizer_stream(chat_id, preset)
    except Exception:
        if chat_id in busy:
            busy.remove(chat_id)
        return await _send_feedback(
            CallbackQuery,
            "<blockquote><b>✘ єǫυᴧʟɪᴢєʀ ᴧᴘᴘʟʏ ғᴧɪʟєᴅ, ᴘʟєᴧsє ᴛʀʏ ᴧɢᴧɪη.</b></blockquote>",
            _,
            alert_text="❌ Equalizer apply failed.",
        )

    if chat_id in busy:
        busy.remove(chat_id)

    try:
        await CallbackQuery.edit_message_text(
            panel_text(chat_id), reply_markup=equalizer_markup(_, chat_id)
        )
    except Exception:
        pass

    await _send_feedback(
        CallbackQuery,
        "<blockquote><b><tg-emoji emoji-id=\"5217933090483098080\">🎚</tg-emoji> "
        f"єǫυᴧʟɪᴢєʀ sєᴛ ᴛσ :</b> <code>{get_eq_name(preset)}</code>\n│\n"
        f"└ <b>ʙʏ :</b> {CallbackQuery.from_user.mention}</blockquote>",
        _,
        alert_text=f"🎚 {get_eq_name(preset)} applied.",
    )


@app.on_callback_query(filters.regex("VolumePanel") & ~BANNED_USERS)
@languageCB
async def volume_panel_cb(client, CallbackQuery, _):
    try:
        chat_id = int(CallbackQuery.data.strip().split(None, 1)[1])
    except (IndexError, ValueError):
        return await CallbackQuery.answer("❌ Invalid volume panel.", show_alert=True)

    if not await is_active_chat(chat_id):
        return await CallbackQuery.answer(_["general_5"], show_alert=True)
    if not await _is_allowed(CallbackQuery):
        return await CallbackQuery.answer(_["admin_14"], show_alert=True)

    await CallbackQuery.answer("🔊 Volume panel opened.")
    try:
        await CallbackQuery.edit_message_text(
            volume_panel_text(chat_id), reply_markup=volume_markup(_, chat_id)
        )
    except Exception:
        pass


@app.on_callback_query(filters.regex("VolumeBack") & ~BANNED_USERS)
@languageCB
async def volume_back_cb(client, CallbackQuery, _):
    try:
        chat_id = int(CallbackQuery.data.strip().split(None, 1)[1])
    except (IndexError, ValueError):
        return await CallbackQuery.answer("❌ Invalid volume panel.", show_alert=True)

    if not await _is_allowed(CallbackQuery):
        return await CallbackQuery.answer(_["admin_14"], show_alert=True)
    await CallbackQuery.answer("↩️ Back to equalizer.")
    try:
        await CallbackQuery.edit_message_text(
            panel_text(chat_id), reply_markup=equalizer_markup(_, chat_id)
        )
    except Exception:
        pass


@app.on_callback_query(filters.regex("VolumeSet") & ~BANNED_USERS)
@languageCB
async def volume_set_cb(client, CallbackQuery, _):
    try:
        chat, action = CallbackQuery.data.strip().split(None, 1)[1].split("|", 1)
        chat_id = int(chat)
    except (IndexError, ValueError):
        return await CallbackQuery.answer("❌ Invalid volume action.", show_alert=True)

    if not await is_active_chat(chat_id):
        return await CallbackQuery.answer(_["general_5"], show_alert=True)
    if not await _is_allowed(CallbackQuery):
        return await CallbackQuery.answer(_["admin_14"], show_alert=True)
    if not db.get(chat_id):
        return await CallbackQuery.answer(_["queue_2"], show_alert=True)
    if chat_id in busy:
        return await CallbackQuery.answer("⏳ Another audio change is running.", show_alert=True)

    old_volume = get_chat_volume(chat_id)
    if action == "up":
        new_volume = min(1000, old_volume + 50)
    elif action == "down":
        new_volume = max(0, old_volume - 25)
    elif action == "boost":
        new_volume = min(1000, old_volume + 500)
    else:
        return await CallbackQuery.answer("❌ Unknown volume action.", show_alert=True)

    if new_volume == old_volume:
        return await CallbackQuery.answer(
            "🔊 Volume is already at its limit.", show_alert=True
        )

    set_chat_volume(chat_id, new_volume)
    busy.append(chat_id)
    try:
        await ANJALI.volume_stream(chat_id)
    except Exception:
        set_chat_volume(chat_id, old_volume)
        return await _send_feedback(
            CallbackQuery,
            "<blockquote><b>✘ ᴠᴏʟᴜᴍᴇ ᴜᴘᴅᴀᴛᴇ ғᴧɪʟєᴅ, ᴘʟєᴧsє ᴛʀʏ ᴧɢᴧɪη.</b></blockquote>",
            _,
            alert_text="❌ Volume update failed.",
        )
    finally:
        if chat_id in busy:
            busy.remove(chat_id)

    try:
        await CallbackQuery.edit_message_text(
            volume_panel_text(chat_id), reply_markup=volume_markup(_, chat_id)
        )
    except Exception:
        pass

    await _send_feedback(
        CallbackQuery,
        f"<blockquote><b>🔊 ᴠᴏʟᴜᴍᴇ ᴜᴘᴅᴀᴛᴇᴅ :</b> <code>{new_volume}%</code>\n"
        f"└ <b>ʙʏ :</b> {CallbackQuery.from_user.mention}</blockquote>",
        _,
        alert_text=f"🔊 Volume set to {new_volume}%.",
    )


@app.on_callback_query(filters.regex("AudioReset") & ~BANNED_USERS)
@languageCB
async def audio_reset_cb(client, CallbackQuery, _):
    try:
        chat_id = int(CallbackQuery.data.strip().split(None, 1)[1])
    except (IndexError, ValueError):
        return await CallbackQuery.answer("❌ Invalid reset action.", show_alert=True)

    if not await is_active_chat(chat_id):
        return await CallbackQuery.answer(_["general_5"], show_alert=True)
    if not await _is_allowed(CallbackQuery):
        return await CallbackQuery.answer(_["admin_14"], show_alert=True)
    if not db.get(chat_id):
        return await CallbackQuery.answer(_["queue_2"], show_alert=True)
    if chat_id in busy:
        return await CallbackQuery.answer("⏳ Another audio change is running.", show_alert=True)

    old_eq = get_chat_eq(chat_id)
    old_volume = get_chat_volume(chat_id)
    reset_chat_audio(chat_id)
    busy.append(chat_id)
    try:
        await ANJALI.equalizer_stream(chat_id, "off")
    except Exception:
        set_chat_eq(chat_id, old_eq)
        set_chat_volume(chat_id, old_volume)
        return await _send_feedback(
            CallbackQuery,
            "<blockquote><b>✘ ᴀᴜᴅɪᴏ ʀᴇsᴇᴛ ғᴀɪʟᴇᴅ, ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.</b></blockquote>",
            _,
            alert_text="❌ Audio reset failed.",
        )
    finally:
        if chat_id in busy:
            busy.remove(chat_id)

    try:
        await CallbackQuery.edit_message_text(
            volume_panel_text(chat_id), reply_markup=volume_markup(_, chat_id)
        )
    except Exception:
        pass

    await _send_feedback(
        CallbackQuery,
        "<blockquote><b><tg-emoji emoji-id=\"6280269890821558384\">✅</tg-emoji> "
        "ᴀᴜᴅɪᴏ ʀᴇsᴇᴛ ᴄᴏᴍᴘʟᴇᴛᴇ</b>\n│\n"
        "├ <b>ᴇǫ :</b> <code>ɴᴏʀᴍᴀʟ</code>\n"
        "├ <b>ᴠᴏʟᴜᴍᴇ :</b> <code>50%</code>\n"
        f"└ <b>ʙʏ :</b> {CallbackQuery.from_user.mention}</blockquote>",
        _,
        alert_text="✅ EQ Normal · Volume 50%",
    )
