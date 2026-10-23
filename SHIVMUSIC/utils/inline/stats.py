from pyrogram.types import InlineKeyboardMarkup

# Yahan styled_button aur ButtonStyle import kiya gaya hai
from button import styled_button, ButtonStyle


def stats_buttons(_, status):
    not_sudo = [
        styled_button(
            text=_["SA_B_1"],
            callback_data="TopOverall",
            style=ButtonStyle.PRIMARY
        )
    ]
    sudo = [
        styled_button(
            text=_["SA_B_2"],
            callback_data="bot_stats_sudo",
            style=ButtonStyle.PRIMARY
        ),
        styled_button(
            text=_["SA_B_3"],
            callback_data="TopOverall",
            style=ButtonStyle.PRIMARY
        ),
    ]
    upl = InlineKeyboardMarkup(
        [
            sudo if status else not_sudo,
            [
                styled_button(
                    text=_["CLOSE_BUTTON"],
                    callback_data="close",
                    style=ButtonStyle.DANGER
                ),
            ],
        ]
    )
    return upl


def back_stats_buttons(_):
    upl = InlineKeyboardMarkup(
        [
            [
                styled_button(
                    text=_["BACK_BUTTON"],
                    callback_data="stats_back",
                    style=ButtonStyle.PRIMARY
                ),
                styled_button(
                    text=_["CLOSE_BUTTON"],
                    callback_data="close",
                    style=ButtonStyle.DANGER
                ),
            ],
        ]
    )
    return upl
