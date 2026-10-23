from pyrogram import Client, filters, enums
from pyrogram.enums import ParseMode, ButtonStyle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated
import random

# Make sure config se LOGGER_2_ID import ho raha hai
from SHIVMUSIC import app
from SHIVMUSIC.utils.database import is_on_off
from config import LOGGER_ID, LOGGER_2_ID

# 🔥 PREMIUM EMOJIS LIST 🔥
PREMIUM_EMOJIS = [
    "5422831825178206894", 
    "5368324170673489600",
    "5206607081334906820",
    "5206380668048496464"
]

# ====================================================
# HELPER FUNCTION: To Fetch Group Owner
# ====================================================
async def get_owner(client, chat_id):
    try:
        async for member in client.get_chat_members(chat_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
            if member.status == enums.ChatMemberStatus.OWNER:
                return member.user.mention
    except:
        pass
    return "Unknown"


# ====================================================
# PLAY LOGS
# ====================================================
async def play_logs(message, streamtype):
    if await is_on_off(2):
        try:
            query = message.text.split(None, 1)[1]
        except:
            query = "Link/File or Reply"

        try:
            members_count = await app.get_chat_members_count(message.chat.id)
        except:
            members_count = "Unknown"
            
        owner = await get_owner(app, message.chat.id)

        chat_link = None
        if message.chat.username:
            chat_link = f"https://t.me/{message.chat.username}"
        else:
            try:
                chat_link = await app.export_chat_invite_link(message.chat.id)
            except:
                pass

        logger_text = f"""
<blockquote><b>{app.mention} ᴘʟᴀʏ ʟᴏɢ</b>

<b>• ʀᴇǫᴜᴇsᴛ ʙʏ : {message.from_user.mention}</b>
<b>• ǫᴜᴇʀʏ : {query}</b>
<b>• ᴄʜᴀᴛ : {message.chat.title} [<code>{message.chat.id}</code>]</b>
<b>• ᴏᴡɴᴇʀ : {owner}</b>
<b>• ᴍᴇᴍʙᴇʀs : {members_count}</b></blockquote>
"""
        buttons = []
        if chat_link:
            buttons.append([InlineKeyboardButton("ɢʀᴏᴜᴘ ʟɪɴᴋ", url=chat_link, style=ButtonStyle.PRIMARY, icon_custom_emoji_id=random.choice(PREMIUM_EMOJIS))])
        buttons.append([InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ", url="https://t.me/betabot_support")])
        
        reply_markup = InlineKeyboardMarkup(buttons)

        if message.chat.id != LOGGER_ID:
            try:
                await app.send_message(
                    chat_id=LOGGER_ID,
                    text=logger_text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    reply_markup=reply_markup
                )
            except:
                pass
        return


# ====================================================
# AUTO GROUP ADD/REMOVE EVENT LOGGER
# ====================================================
@app.on_chat_member_updated(filters.group, group=1)
async def auto_group_logger(client: Client, message: ChatMemberUpdated):
    try:
        bot = await client.get_me()
        
        # Sirf tabhi trigger hoga jab bot khud add/remove ho
        if not message.new_chat_member or message.new_chat_member.user.id != bot.id:
            return

        target_logger = LOGGER_ID
        
        if not target_logger:
            return

        chat = message.chat
        action_by = message.from_user
        
        try:
            members_count = await client.get_chat_members_count(chat.id)
        except:
            members_count = "Unknown"

        owner = await get_owner(client, chat.id)
        action_by_mention = action_by.mention if action_by else "<b>Unknown User</b>"
        bot_details = app.mention
        
        # Image URL
        log_image = "https://files.catbox.moe/10zwqs.jpg"

        # Group Link Fetching Logic for Button
        chat_link = None
        if chat.username:
            chat_link = f"https://t.me/{chat.username}"
        elif message.new_chat_member.status == enums.ChatMemberStatus.ADMINISTRATOR:
            try:
                chat_link = await client.export_chat_invite_link(chat.id)
            except:
                pass

        # Button Setup
        reply_markup = None
        if chat_link:
            buttons = [
                [InlineKeyboardButton("🔗 ɢʀᴏᴜᴘ ʟɪɴᴋ", url=chat_link)]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)

        # 🟢 CONDITION 1: Added to Group
        if message.new_chat_member.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR]:
            log_caption = f"""
#Added
<blockquote><b>✅ ʙᴏᴛ ᴀᴅᴅᴇᴅ ᴛᴏ ɢʀᴏᴜᴘ</b>

<b>• ʙᴏᴛ : {bot_details}</b>
<b>• ᴀᴅᴅᴇᴅ ʙʏ : {action_by_mention}</b>
<b>• ᴄʜᴀᴛ : {chat.title} [<code>{chat.id}</code>]</b>
<b>• ᴏᴡɴᴇʀ : {owner}</b>
<b>• ᴍᴇᴍʙᴇʀs : {members_count}</b></blockquote>
"""
            await client.send_photo(
                chat_id=target_logger,
                photo=log_image,
                caption=log_caption,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )

        # 🔴 CONDITION 2: Removed from Group
        elif message.new_chat_member.status in [enums.ChatMemberStatus.BANNED, enums.ChatMemberStatus.LEFT]:
            log_caption = f"""
#Removed
<blockquote><b>❌ ʙᴏᴛ ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ ɢʀᴏᴜᴘ</b>

<b>• ʙᴏᴛ : {bot_details}</b>
<b>• ʀᴇᴍᴏᴠᴇᴅ ʙʏ : {action_by_mention}</b>
<b>• ᴄʜᴀᴛ : {chat.title} [<code>{chat.id}</code>]</b>
<b>• ᴏᴡɴᴇʀ : {owner}</b>
<b>• ᴍᴇᴍʙᴇʀs : {members_count}</b></blockquote>
"""
            await client.send_photo(
                chat_id=target_logger,
                photo=log_image,
                caption=log_caption,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )

    except Exception as e:
        print(f"[ERROR] Auto Group Logger Failed: {e}")


# ====================================================
# AUTOPLAY LOGS 
# ====================================================
async def autoplay_log(client, chat_id, query, vibe="Unknown"):
    if not await is_on_off(2):
        return
        
    try:
        bot = await client.get_me()
        bot_mention = bot.mention
    except:
        return

    try:
        chat = await client.get_chat(chat_id)
        chat_title = chat.title
        chat_username = chat.username
    except:
        chat_title = "Unknown Chat"
        chat_username = None

    try:
        members_count = await client.get_chat_members_count(chat_id)
    except:
        members_count = "Unknown"
        
    owner = await get_owner(client, chat_id)

    chat_link = None
    if chat_username:
        chat_link = f"https://t.me/{chat_username}"
    else:
        try:
            chat_link = await client.export_chat_invite_link(chat_id)
        except:
            pass

    header_text = f"<b>{bot_mention} ᴀᴜᴛᴏᴘʟᴀʏ ʟᴏɢ</b>"

    logger_text = f"""
<blockquote>{header_text}

<b>• ᴀᴄᴛɪᴏɴ : ᴀᴜᴛᴏᴘʟᴀʏ ᴛʀɪɢɢᴇʀᴇᴅ 🔄</b>
<b>• ᴛʀᴀᴄᴋ : {query}</b>
<b>• ᴠɪʙᴇ : {vibe}</b>
<b>• ᴄʜᴀᴛ : {chat_title} [<code>{chat_id}</code>]</b>
<b>• ᴏᴡɴᴇʀ : {owner}</b>
<b>• ᴍᴇᴍʙᴇʀs : {members_count}</b></blockquote>
"""
    buttons = []
    if chat_link:
        buttons.append([InlineKeyboardButton("ɢʀᴏᴜᴘ ʟɪɴᴋ", url=chat_link, style=ButtonStyle.SUCCESS, icon_custom_emoji_id=random.choice(PREMIUM_EMOJIS))])
    buttons.append([InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ", url="https://t.me/betabot_support")])
    
    reply_markup = InlineKeyboardMarkup(buttons)

    if chat_id != LOGGER_ID:
        try:
            await app.send_message(
                chat_id=LOGGER_ID,
                text=logger_text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"[ERROR] Sending Autoplay Log Failed: {e}")
