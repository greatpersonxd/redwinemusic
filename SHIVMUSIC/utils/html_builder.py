"""Telegram HTML captions used by the modern welcome screen.

Telegram renders the keyboard separately from the caption.  Keeping the
buttons in an InlineKeyboardMarkup (rather than embedding unsupported custom
HTML button tags) makes this work in current Telegram clients and Bot API
versions.
"""

def build_welcome_html(user_mention: str, bot_mention: str, bot_username: str) -> str:
    return (
        f"<tg-emoji emoji-id='5409368076447657845'>🌟</tg-emoji> <b>Greetings, {user_mention}!</b>\n\n"
        f"<tg-emoji emoji-id='5355051922862653659'>🤖</tg-emoji> <b>This is {bot_mention} — your premium music streaming companion.</b>\n\n"
        "<blockquote expandable>"
        "<b>✦ BOT INFORMATION ✦</b>\n\n"
        "<b>FEATURE              DETAILS</b>\n"
        "────────────────────────────\n"
        "<tg-emoji emoji-id='6082387600599944892'>🎧</tg-emoji> <b>Streaming</b>       <i>High-quality, zero lag</i>\n"
        "<tg-emoji emoji-id='6100220081474639964'>⚡️</tg-emoji> <b>Speed</b>           <i>Instant response, always on</i>\n"
        "<tg-emoji emoji-id='5463274047771000031'>🎚</tg-emoji> <b>Equalizer</b>       <i>13 professional presets</i>\n"
        "<tg-emoji emoji-id='5258389041006518073'>📂</tg-emoji> <b>Platforms</b>       <i>YouTube, Spotify, Apple & Telegram</i>\n"
        "<tg-emoji emoji-id='6172332822892647766'>🚀</tg-emoji> <b>Availability</b>    <i>Active 24×7</i>\n"
        "<tg-emoji emoji-id='6271537028307881531'>💎</tg-emoji> <b>VIP Experience</b> <i>Premium controls and effects</i>"
        "</blockquote>\n\n"
        "<tg-emoji emoji-id='5188540541922480562'>❓</tg-emoji> <i>Tap Help to explore all available commands.</i>"
    )