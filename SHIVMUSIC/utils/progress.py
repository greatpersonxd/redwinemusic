"""Telegram-safe rich HTML typewriter helpers."""

import asyncio
import re

from pyrogram.enums import ParseMode


_TAG_RE = re.compile(r"(<[^>]+>)")
_OPEN_TAG_RE = re.compile(r"^<([a-zA-Z][\w-]*)(?:\s[^>]*)?>$")
_CLOSE_TAG_RE = re.compile(r"^</([a-zA-Z][\w-]*)>$")
_SELF_CLOSING = {"br", "hr"}


def _typewriter_frames(full_html: str, chunk_size: int = 28):
    """Build valid HTML frames while progressively revealing visible text."""
    frames = []
    rendered = ""
    opened = []
    visible_since_frame = 0

    for token in _TAG_RE.split(full_html):
        if not token:
            continue
        if token.startswith("<"):
            rendered += token
            closing = _CLOSE_TAG_RE.match(token)
            opening = _OPEN_TAG_RE.match(token)
            if closing:
                name = closing.group(1).lower()
                if name in opened:
                    opened.reverse()
                    opened.remove(name)
                    opened.reverse()
            elif opening:
                name = opening.group(1).lower()
                if name not in _SELF_CLOSING and not token.rstrip().endswith("/>"):
                    opened.append(name)
            continue

        for start in range(0, len(token), chunk_size):
            part = token[start : start + chunk_size]
            rendered += part
            visible_since_frame += len(part)
            if visible_since_frame >= chunk_size:
                closing_tags = "".join(f"</{name}>" for name in reversed(opened))
                frames.append(rendered + closing_tags)
                visible_since_frame = 0

    if not frames or frames[-1] != full_html:
        frames.append(full_html)
    return frames


async def stream_typewriter_rich_message(
    client,
    chat_id,
    full_html,
    chunk_delay=0.08,
    *,
    reply_markup=None,
    photo=None,
):
    """Send HTML progressively; optionally animate a photo caption."""
    frames = _typewriter_frames(full_html)
    first = frames[0]
    if photo:
        message = await client.send_photo(
            chat_id,
            photo=photo,
            caption=first,
            parse_mode=ParseMode.HTML,
        )
        edit = message.edit_caption
    else:
        message = await client.send_message(
            chat_id,
            text=first,
            parse_mode=ParseMode.HTML,
        )
        edit = message.edit_text

    for frame in frames[1:]:
        await asyncio.sleep(chunk_delay)
        try:
            await edit(frame, parse_mode=ParseMode.HTML)
        except Exception:
            continue

    if reply_markup:
        try:
            await message.edit_reply_markup(reply_markup=reply_markup)
        except Exception:
            pass
    return message