from pyrogram.types import InlineKeyboardButton
from enum import Enum

# Button ke styles
class ButtonStyle(Enum):
    SUCCESS = "success"
    PRIMARY = "primary"
    DANGER = "danger"
    SECONDARY = "secondary" # ✅ Error fixed: Added SECONDARY
    INFO = "info"           # ✅ Added for future use

def styled_button(
    text: str, 
    callback_data: str = None, 
    url: str = None, 
    user_id: int = None, 
    style: ButtonStyle = ButtonStyle.PRIMARY,
    **kwargs
):
    """
    Styled Button: Yeh function style aur extra arguments 
    (jaise icon_custom_emoji_id) ko support karta hai.
    """
    
    # Base arguments setup
    params = {"text": text}
    
    # Callback, URL ya User ID handle karein
    if url:
        params["url"] = url
    elif user_id:
        params["user_id"] = user_id
    elif callback_data:
        params["callback_data"] = callback_data
    else:
        params["callback_data"] = "none"
        
    # Style aur extra arguments add karein (Emoji, etc.)
    params["style"] = style.value
    params.update(kwargs)
    
    return InlineKeyboardButton(**params)
