import random
from typing import Union

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from SHIVMUSIC import app
from pyrogram.enums import ButtonStyle

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
    # Row me buttons ke hisaab se random color assign hoga
    return {1: styles[0], 2: styles[1], 3: styles[2]}

# 🔘 Smart Button Creator
def create_btn(text, cb=None, url=None, style=ButtonStyle.PRIMARY, no_emoji=False):
    kwargs = {"text": text, "style": style}
    if cb: kwargs["callback_data"] = cb
    if url: kwargs["url"] = url
    if not no_emoji: kwargs["icon_custom_emoji_id"] = random.choice(PREMIUM_EMOJIS)
    return InlineKeyboardButton(**kwargs)


def help_pannel(_, START: Union[bool, int] = None):
    s_map = get_style_map()
    first = [
        [
            create_btn(text=_["H_B_1"], cb="help_callback hb1", style=s_map[3]),
            create_btn(text=_["H_B_2"], cb="help_callback hb2", style=s_map[3]),
            create_btn(text=_["H_B_3"], cb="help_callback hb3", style=s_map[3]),
        ],
        [
            create_btn(text=_["H_B_4"], cb="help_callback hb4", style=s_map[3]),
            create_btn(text=_["H_B_5"], cb="help_callback hb5", style=s_map[3]),
            create_btn(text=_["H_B_6"], cb="help_callback hb6", style=s_map[3]),
        ],
        [
            create_btn(text=_["H_B_7"], cb="help_callback hb7", style=s_map[3]),
            create_btn(text=_["H_B_8"], cb="help_callback hb8", style=s_map[3]),
            create_btn(text=_["H_B_9"], cb="help_callback hb9", style=s_map[3]),
        ],
        [
            create_btn(text=_["H_B_10"], cb="help_callback hb10", style=s_map[3]),
            create_btn(text=_["H_B_11"], cb="help_callback hb11", style=s_map[3]),
            create_btn(text=_["H_B_12"], cb="help_callback hb12", style=s_map[3]),
        ],
        [
            create_btn(text=_["H_B_13"], cb="help_callback hb13", style=s_map[3]),
            create_btn(text=_["H_B_14"], cb="help_callback hb14", style=s_map[3]),
            create_btn(text=_["H_B_15"], cb="help_callback hb15", style=s_map[3]),
        ],
        [
            create_btn(text=_["BACK_BUTTON"], cb="settingsback_helper", style=s_map[1]),
        ],
    ]
    return InlineKeyboardMarkup(first)


def first_page(_, is_owner: bool = False):
    s_map = get_style_map()
    first = [
        [
            create_btn(text=_["H_B_1"], cb="help_callback hb1", style=s_map[3]),
            create_btn(text=_["H_B_2"], cb="help_callback hb2", style=s_map[3]),
            create_btn(text=_["H_B_3"], cb="help_callback hb3", style=s_map[3]),
        ],
        [
            create_btn(text=_["H_B_11"], cb="help_callback hb11", style=s_map[3]),
            create_btn(text=_["H_B_8"], cb="help_callback hb8", style=s_map[3]),
            create_btn(text=_["H_B_6"], cb="help_callback hb6", style=s_map[3]),
        ],
        [
            create_btn(text=_["H_B_13"], cb="help_callback hb13", style=s_map[3]),
            create_btn(text=_["H_B_12"], cb="help_callback hb12", style=s_map[3]),
            create_btn(text=_["H_B_9"], cb="help_callback cloghelp", style=s_map[3]),
        ],
        [
            create_btn(text=_["H_B_10"], cb="help_callback hb10", style=s_map[3]),
            create_btn(text=_["H_B_14"], cb="help_callback hb14", style=s_map[3]),
            create_btn(text=_["H_B_15"], cb="help_callback hb15", style=s_map[3]),
        ],
    ]
    
    first.append([create_btn(text=_["BACK_BUTTON"], cb="settingsback_home", style=s_map[1])])
    return InlineKeyboardMarkup(first)


def help_back_markup(_):
    s_map = get_style_map()
    return InlineKeyboardMarkup([
        [create_btn(text=_["BACK_BUTTON"], cb="help_home", style=s_map[1])]
    ])


def private_help_panel(_):
    s_map = get_style_map()
    return InlineKeyboardMarkup([
        [create_btn(text=_["S_B_4"], url=f"https://t.me/{app.username}?start=help", style=s_map[1])]
    ])
