import asyncio
import os
import random
import logging
from datetime import datetime, timedelta
from typing import Union

from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode

from pytgcalls import PyTgCalls
from pytgcalls.mtproto.bridged_client import BridgedClient
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality

import config
from SHIVMUSIC import LOGGER, YouTube, app, userbot
from SHIVMUSIC.misc import db
from SHIVMUSIC.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_lang,
    get_loop,
    group_assistant,
    is_autoend,
    music_on,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
    is_autoplay_on,
)
from SHIVMUSIC.utils.autoplay import fetch_autoplay_track, remember_played
from SHIVMUSIC.utils.stream.queue import put_queue
from SHIVMUSIC.utils.logger import play_logs
from SHIVMUSIC.utils.exceptions import AssistantErr
from SHIVMUSIC.utils.formatters import check_duration, seconds_to_min, speed_converter
from SHIVMUSIC.utils.inline.play import stream_markup, telegram_markup
from SHIVMUSIC.utils.stream.autoclear import auto_clean
from strings import get_string
from SHIVMUSIC.utils.thumbnails import get_thumb
from SHIVMUSIC.utils.equalizer import (
    get_chat_eq,
    get_chat_eq_filter,
    get_chat_volume,
    get_chat_volume_filter,
    get_eq_name,
)
from SHIVMUSIC.error_logger import report_exception


def _install_pytgcalls_client_compatibility():
    """Make PyTgCalls recognise our wrapped Pyrogram client.

    ErrorLoggingClient is a subclass of pyrogram.Client, but its direct class
    module is SHIVMUSIC.error_logger. Older/current PyTgCalls releases detect
    the MTProto library from only the direct class module and consequently
    raise InvalidMTProtoClient for this perfectly valid client.
    """
    original_package_name = BridgedClient.package_name

    def package_name(client):
        for client_class in type(client).__mro__:
            module = getattr(client_class, "__module__", "")
            root_module = module.split(".", 1)[0]
            if root_module in {"pyrogram", "telethon"}:
                return root_module
        return original_package_name(client)

    BridgedClient.package_name = staticmethod(package_name)


_install_pytgcalls_client_compatibility()


def handle_asyncio_exceptions(loop, context):
    msg = context.get("exception", context.get("message"))
    msg_str = str(msg).lower()

    expected_sync_events = [
        "groupcall_forbidden", 
        "setvideocallstatus", 
        "groupcall_invalid", 
        "no active group call", 
        "group call has already ended"
    ]

    if any(err in msg_str for err in expected_sync_events):
        logging.getLogger("asyncio").info(f"ℹ️ VC State Sync (Harmless): {msg}")
    else:
        logging.getLogger("asyncio").error(f"❌ Unhandled Asyncio Error: {msg}")

autoend = {}
counter = {}


def _audio_status_html(chat_id):
    return (
        "\n<blockquote>"
        "<b>✦ AUDIO SETTINGS ✦</b>\n\n"
        "<b>FEATURE          DETAILS</b>\n"
        "──────────────────────\n"
        "<tg-emoji emoji-id=\"5217933090483098080\">🎚</tg-emoji> <b>MOOD / EQ</b>     "
        f"<code>{get_eq_name(get_chat_eq(chat_id))}</code>\n"
        "<tg-emoji emoji-id=\"5258389041006518073\">🔊</tg-emoji> <b>VOLUME</b>        "
        f"<code>{get_chat_volume(chat_id)}%</code>"
        "</blockquote>\n"
        f"<a href=\"{config.SUPPORT_CHAT}\">Support ↗</a>  "
        f"<a href=\"{config.SUPPORT_CHANNEL}\">Updates ↗</a>"
    )

FORCE_JOIN_LINKS = [
    "https://t.me/betabot_hub",
    "https://t.me/betabot_support",
    "https://t.me/sukoon_s",
]

def get_random_img(img_list):
    if img_list:
        if isinstance(img_list, list):
            return random.choice(img_list)
        return img_list
    return "https://telegra.ph/file/2e3d368e77c449c287430.jpg" 

async def _clear_(chat_id):
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)

class Call:
    def __init__(self):
        # Reuse the assistant clients that Userbot owns. Creating another
        # client for every session doubled Telegram connections and memory.
        self.userbot1 = userbot.one
        self.one = PyTgCalls(self.userbot1, cache_duration=100)

        self.two = None
        if getattr(config, "STRING2", None):
            self.userbot2 = userbot.two
            self.two = PyTgCalls(self.userbot2, cache_duration=100)

        self.three = None
        if getattr(config, "STRING3", None):
            self.userbot3 = userbot.three
            self.three = PyTgCalls(self.userbot3, cache_duration=100)

        self.four = None
        if getattr(config, "STRING4", None):
            self.userbot4 = userbot.four
            self.four = PyTgCalls(self.userbot4, cache_duration=100)

        self.five = None
        if getattr(config, "STRING5", None):
            self.userbot5 = getattr(userbot, "five", None)
            if self.userbot5:
                self.five = PyTgCalls(self.userbot5, cache_duration=100)

        self.custom_assistants = {} 
        self.active_clients = {} 
        self._started_calls = []
        self._setup_event_handlers()

    def _telegram_client_for_call(self, call_client):
        """Map a PyTgCalls instance back to its Telegram assistant client."""
        for call_instance, telegram_client in (
            (self.one, self.userbot1),
            (self.two, getattr(self, "userbot2", None)),
            (self.three, getattr(self, "userbot3", None)),
            (self.four, getattr(self, "userbot4", None)),
            (self.five, getattr(self, "userbot5", None)),
        ):
            if call_instance is call_client and telegram_client is not None:
                return telegram_client
        return self.userbot1

    def _setup_event_handlers(self):
        clients = [self.one, self.two, self.three, self.four, self.five]
        for client in clients:
            if not client:
                continue

            @client.on_update()
            async def stream_handler(c, update, call_instance=client):
                try:
                    c_id = getattr(update, "chat_id", None)
                    if not c_id: return

                    t_name = type(update).__name__
                    if "ChatUpdate" in t_name:
                        status = str(getattr(update, "status", "")).upper()
                        if "KICKED" in status or "LEFT" in status or "CLOSED" in status:
                            await self.stop_stream(c_id)
                    elif "StreamEnd" in t_name or "StreamAudioEnded" in t_name or "StreamVideoEnded" in t_name:
                        await self.change_stream(c, c_id)
                except Exception as exception:
                    await report_exception(
                        self._telegram_client_for_call(call_instance),
                        exception,
                        context="PyTgCalls stream update handler",
                        callback=stream_handler,
                        update=update,
                    )

    def _with_eq(self, chat_id, extra_args=""):
        """Append the chat's EQ and volume filters to the ffmpeg args."""
        extra_args = extra_args or ""
        filters = []
        try:
            audio_filter = get_chat_eq_filter(chat_id)
            if audio_filter:
                filters.append(audio_filter)
        except Exception:
            pass
        try:
            volume_filter = get_chat_volume_filter(chat_id)
            if volume_filter:
                filters.append(volume_filter)
        except Exception:
            pass
        if not filters or "-af" in extra_args:
            return extra_args
        # py-tgcalls syntax: "--audio" -> audio process only,
        # "---mid" -> place the option AFTER the input (-af is an output option).
        filter_chain = ",".join(filters)
        return (extra_args + " " if extra_args else "") + f"--audio ---mid -af {filter_chain}"

    async def _safe_change_stream(self, client, chat_id, file_path, video=False, extra_args=""):
        extra_args = self._with_eq(chat_id, extra_args)
        if not video:
            stream = MediaStream(file_path, audio_parameters=AudioQuality.HIGH, ffmpeg_parameters=extra_args)
            await client.play(chat_id, stream)
            return

        try: 
            stream = MediaStream(
                file_path, 
                audio_parameters=AudioQuality.HIGH, 
                video_parameters=VideoQuality.HD_720p, 
                ffmpeg_parameters=extra_args
            )
            await client.play(chat_id, stream)
        except Exception as e:
            LOGGER(__name__).warning(f"720p Change Stream failed, auto-switching to 480p: {e}")
            stream = MediaStream(
                file_path, 
                audio_parameters=AudioQuality.HIGH, 
                video_parameters=VideoQuality.SD_480p, 
                ffmpeg_parameters=extra_args
            )
            await client.play(chat_id, stream)

    async def _safe_join_call(self, assistant_to_join, chat_id, file_path, video=False):
        extra_args = self._with_eq(chat_id)
        if not video:
            stream = MediaStream(file_path, audio_parameters=AudioQuality.HIGH, ffmpeg_parameters=extra_args)
            return await assistant_to_join.play(chat_id, stream)

        try: 
            stream = MediaStream(
                file_path, 
                audio_parameters=AudioQuality.HIGH, 
                video_parameters=VideoQuality.HD_720p,
                ffmpeg_parameters=extra_args
            )
            await assistant_to_join.play(chat_id, stream)
        except Exception as e:
            LOGGER(__name__).warning(f"720p Join Call failed, auto-switching to 480p: {e}")
            stream = MediaStream(
                file_path, 
                audio_parameters=AudioQuality.HIGH, 
                video_parameters=VideoQuality.SD_480p,
                ffmpeg_parameters=extra_args
            )
            await assistant_to_join.play(chat_id, stream)

    async def get_active_clients(self, chat_id):
        try: chat_id = int(chat_id)
        except: pass
        clients = []
        if chat_id in self.active_clients:
            val = self.active_clients[chat_id]
            if isinstance(val, list):
                clients.extend(val)
            else:
                clients.append(val)
        if not clients:
            try:
                main_ass = await group_assistant(self, chat_id)
                clients.append(main_ass)
            except:
                clients.append(self.one)
        return list(set(clients))

    async def pause_stream(self, chat_id: int, assistant_type=None):
        try: chat_id = int(chat_id)
        except: pass
        assistants = await self.get_active_clients(chat_id)
        paused = False
        last_error = None
        for assistant in assistants:
            try:
                await assistant.pause_stream(chat_id)
                paused = True
            except Exception as e:
                last_error = e
                LOGGER(__name__).error(f"Pause error: {e}")
        if not paused and last_error:
            raise last_error
        return paused

    async def resume_stream(self, chat_id: int, assistant_type=None):
        try: chat_id = int(chat_id)
        except: pass
        assistants = await self.get_active_clients(chat_id)
        resumed = False
        last_error = None
        for assistant in assistants:
            try:
                await assistant.resume_stream(chat_id)
                resumed = True
            except Exception as e:
                last_error = e
                LOGGER(__name__).error(f"Resume error: {e}")
        if not resumed and last_error:
            raise last_error
        return resumed

    async def stop_stream(self, chat_id: int, assistant_type=None):
        try: chat_id = int(chat_id)
        except: pass

        try: await _clear_(chat_id)
        except: pass

        active_assistants = await self.get_active_clients(chat_id)
        for assistant in active_assistants:
            if assistant:
                try: 
                    await assistant.leave_call(chat_id)
                    LOGGER(__name__).info(f"✅ Assistant left VC successfully in chat {chat_id}.")
                except Exception as e: 
                    error_msg = str(e).lower()
                    ignore_list = ["no active group call", "already ended", "not in a call", "groupcall_forbidden", "groupcall_invalid"]
                    if any(ign in error_msg for ign in ignore_list):
                        LOGGER(__name__).info(f"ℹ️ Assistant State Sync: VC already closed in {chat_id}.")
                    else:
                        LOGGER(__name__).error(f"❌ Assistant failed to leave VC in {chat_id}: {e}")

        if chat_id in self.active_clients: 
            del self.active_clients[chat_id]

    async def stop_stream_force(self, chat_id: int):
        try: chat_id = int(chat_id)
        except: pass

        active_assistants = await self.get_active_clients(chat_id)
        for assistant in active_assistants:
            if assistant:
                try: 
                    await assistant.leave_call(chat_id)
                except Exception as e: 
                    error_msg = str(e).lower()
                    ignore_list = ["no active group call", "already ended", "not in a call", "groupcall_forbidden", "groupcall_invalid"]
                    if any(ign in error_msg for ign in ignore_list):
                        LOGGER(__name__).info(f"ℹ️ Assistant State Sync: VC already closed in {chat_id} (Force).")
                    else:
                        LOGGER(__name__).error(f"❌ Assistant force-leave failed in {chat_id}: {e}")

        if chat_id in self.active_clients: 
            del self.active_clients[chat_id]

        try: await _clear_(chat_id)
        except: pass

    async def force_stop_stream(self, chat_id: int):
        """Compatibility name used by the play handlers."""
        return await self.stop_stream_force(chat_id)

    async def speedup_stream(self, chat_id: int, file_path, speed, playing):
        try: chat_id = int(chat_id)
        except: pass
        assistants = await self.get_active_clients(chat_id)
        assistant = assistants[0] if assistants else self.one
        if str(speed) != str("1.0"):
            base = os.path.basename(file_path)
            chatdir = os.path.join(os.getcwd(), "playback", str(speed))
            if not os.path.isdir(chatdir):
                os.makedirs(chatdir)
            out = os.path.join(chatdir, base)
            if not os.path.isfile(out):
                if str(speed) == str("0.5"): vs = 2.0
                if str(speed) == str("0.75"): vs = 1.35
                if str(speed) == str("1.5"): vs = 0.68
                if str(speed) == str("2.0"): vs = 0.5
                proc = await asyncio.create_subprocess_shell(
                    cmd=(f"ffmpeg -i {file_path} -filter:v setpts={vs}*PTS -filter:a atempo={speed} {out}"),
                    stdin=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
        else:
            out = file_path

        loop = asyncio.get_running_loop()

        dur = await loop.run_in_executor(None, check_duration, out)
        dur = int(dur)
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        duration = seconds_to_min(dur)

        is_video = playing[0]["streamtype"] == "video"
        extra_args = f"-ss {played} -to {duration}"

        if str(db[chat_id][0]["file"]) == str(file_path):
            for assistant in assistants:
                try: await self._safe_change_stream(assistant, chat_id, out, is_video, extra_args)
                except: pass
        else: raise AssistantErr("Umm")

        if str(db[chat_id][0]["file"]) == str(file_path):
            exis = (playing[0]).get("old_dur")
            if not exis:
                db[chat_id][0]["old_dur"] = db[chat_id][0]["dur"]
                db[chat_id][0]["old_second"] = db[chat_id][0]["seconds"]
            db[chat_id][0]["played"] = con_seconds
            db[chat_id][0]["dur"] = duration
            db[chat_id][0]["seconds"] = dur
            db[chat_id][0]["speed_path"] = out
            db[chat_id][0]["speed"] = speed

    async def equalizer_stream(self, chat_id: int, preset: str):
        """Re-start the current track from the same position with a new EQ preset."""
        from SHIVMUSIC.utils.equalizer import set_chat_eq

        try: chat_id = int(chat_id)
        except: pass

        playing = db.get(chat_id)
        if not playing:
            raise AssistantErr("Nothing is playing right now.")

        set_chat_eq(chat_id, preset)

        file_path = playing[0].get("speed_path") or playing[0]["file"]
        is_video = str(playing[0].get("streamtype")) == "video"
        played = int(playing[0].get("played") or 0)

        extra_args = ""
        seekable = str(file_path).startswith("/") or "downloads" in str(file_path) or "playback" in str(file_path)
        if seekable and played > 0:
            extra_args = f"-ss {seconds_to_min(played)}"

        assistants = await self.get_active_clients(chat_id)
        done = False
        last_error = None
        for assistant in assistants:
            try:
                await self._safe_change_stream(assistant, chat_id, file_path, is_video, extra_args)
                done = True
            except Exception as exc:
                last_error = exc
        if not done:
            raise AssistantErr(f"Equalizer failed: {last_error}")
        db[chat_id][0]["eq"] = preset

    async def volume_stream(self, chat_id: int):
        """Restart the current track at the same position with its new volume."""
        try:
            chat_id = int(chat_id)
        except Exception:
            pass

        playing = db.get(chat_id)
        if not playing:
            raise AssistantErr("Nothing is playing right now.")

        file_path = playing[0].get("speed_path") or playing[0]["file"]
        is_video = str(playing[0].get("streamtype")) == "video"
        played = int(playing[0].get("played") or 0)

        extra_args = ""
        seekable = str(file_path).startswith("/") or "downloads" in str(file_path) or "playback" in str(file_path)
        if seekable and played > 0:
            extra_args = f"-ss {seconds_to_min(played)}"

        assistants = await self.get_active_clients(chat_id)
        done = False
        last_error = None
        for assistant in assistants:
            try:
                await self._safe_change_stream(assistant, chat_id, file_path, is_video, extra_args)
                done = True
            except Exception as exc:
                last_error = exc
        if not done:
            raise AssistantErr(f"Volume change failed: {last_error}")

        from SHIVMUSIC.utils.equalizer import get_chat_volume
        db[chat_id][0]["volume"] = get_chat_volume(chat_id)

    async def skip_stream(self, chat_id: int, link: str, video: Union[bool, str] = None, image: Union[bool, str] = None, assistant_type=None):
        try: chat_id = int(chat_id)
        except: pass
        assistants = await self.get_active_clients(chat_id)
        for assistant in assistants:
            try: await self._safe_change_stream(assistant, chat_id, link, video)
            except: pass

    async def seek_stream(self, chat_id, file_path, to_seek, duration, mode):
        try: chat_id = int(chat_id)
        except: pass
        assistants = await self.get_active_clients(chat_id)
        is_video = mode == "video"
        extra_args = f"-ss {to_seek} -to {duration}"
        for assistant in assistants:
            try: await self._safe_change_stream(assistant, chat_id, file_path, is_video, extra_args)
            except: pass

    async def autoplay_start(self, chat_id: int, original_chat_id: int, seed_title: str, seed_vidid: str = None, client: PyTgCalls = None, bot_client = None) -> bool:
        if seed_vidid:
            remember_played(chat_id, seed_vidid)

        chat_client = bot_client or app 
        
        status_msg = None
        try:
            status_msg = await chat_client.send_message(original_chat_id, "ʜσʟᴅ ση...\n\nᴅσᴡηʟσᴧᴅɪηɢ ηєxᴛ ϻєᴅɪᴧ ғʀσϻ ᴛʜє ǫυєυє.")
        except Exception:
            pass

        async def _fail() -> bool:
            if status_msg:
                try: await status_msg.delete()
                except: pass
            return False

        track = await fetch_autoplay_track(chat_id, seed_title, seed_vidid)
        if not track:
            return await _fail()

        try:
            language = await get_lang(chat_id)
            _ = get_string(language)
        except:
            _ = get_string("en")

        try:
            file_path, direct = await YouTube.download(track["vidid"], None, videoid=True)
        except Exception:
            return await _fail()

        if not file_path:
            return await _fail()

        remember_played(chat_id, track["vidid"])
        title = track["title"].title()
        duration_min = track["duration_min"]

        await put_queue(
            chat_id,
            original_chat_id,
            file_path if direct else f"vid_{track['vidid']}",
            title,
            duration_min,
            "🔁 ᴀᴜᴛᴏᴘʟᴀʏ",
            track["vidid"],
            1,
            "audio",
            forceplay=True,
        )

        if db.get(chat_id):
            db[chat_id][-1]["client"] = chat_client

        active_assistants = await self.get_active_clients(chat_id)
        assistant = client if client else (active_assistants[0] if active_assistants else self.one)

        try:
            await self._safe_change_stream(assistant, chat_id, file_path, video=False)
        except Exception:
            return await _fail()

        try:
            bot_username = chat_client.me.username if chat_client.me else app.username
        except:
            bot_username = app.username

        try:
            img = await get_thumb(track["vidid"], 0, chat_client) or get_random_img(config.PLAYLIST_IMG_URL)
            
            button = stream_markup(_, chat_id)
            
            run = await chat_client.send_photo(
                chat_id=original_chat_id,
                photo=img,
                caption=_["stream_1"].format(
                    f"https://t.me/{bot_username}?start=info_{track['vidid']}",
                    title[:23],
                    duration_min,
                    "ᴀᴜᴛᴏᴘʟᴀʏ 🎧",
                ) + _audio_status_html(chat_id),
                reply_markup=InlineKeyboardMarkup(button),
            )
            if db.get(chat_id):
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
        except Exception as e:
            LOGGER(__name__).error(f"Autoplay Send Photo Error: {e}")
            pass

        if status_msg:
            try: await status_msg.delete()
            except Exception: pass

        try:
            await play_logs(original_chat_id, title)
        except Exception:
            pass

        return True

    async def join_call(self, chat_id: int, original_chat_id: int, link, video: Union[bool, str] = None, image: Union[bool, str] = None, userbot=None):
        assistant_to_join = None
        if userbot:
            if FORCE_JOIN_LINKS:
                for link_join in FORCE_JOIN_LINKS:
                    try:
                        await userbot.join_chat(link_join)
                        await asyncio.sleep(0.5) 
                    except: pass
            user_id = userbot.me.id
            if user_id in self.custom_assistants:
                assistant_to_join = self.custom_assistants[user_id]
            else:
                assistant_to_join = PyTgCalls(userbot, cache_duration=100)

                @assistant_to_join.on_update()
                async def assistant_stream_handler(client, update):
                    try:
                        c_id = getattr(update, "chat_id", None)
                        if not c_id: return

                        t_name = type(update).__name__
                        if "ChatUpdate" in t_name:
                            status = str(getattr(update, "status", "")).upper()
                            if "KICKED" in status or "LEFT" in status or "CLOSED" in status:
                                await self.stop_stream(c_id)
                        elif "StreamEnd" in t_name or "StreamAudioEnded" in t_name or "StreamVideoEnded" in t_name:
                            await self.change_stream(client, c_id)
                    except Exception as e:
                        await report_exception(
                            userbot,
                            e,
                            context="Assistant PyTgCalls stream update handler",
                            callback=assistant_stream_handler,
                            update=update,
                        )

                await assistant_to_join.start()
                self.custom_assistants[user_id] = assistant_to_join
        else:
            assistant_to_join = await group_assistant(self, chat_id)

        if chat_id not in self.active_clients:
            self.active_clients[chat_id] = []
        if assistant_to_join not in self.active_clients[chat_id]:
            self.active_clients[chat_id].append(assistant_to_join)

        candidates = []
        for candidate in [assistant_to_join, self.one, self.two, self.three, self.four, self.five]:
            if candidate and candidate not in candidates:
                candidates.append(candidate)

        last_error = None
        for candidate in candidates:
            try:
                await self._safe_join_call(candidate, chat_id, link, video)
                assistant_to_join = candidate
                break
            except Exception as exc:
                last_error = exc
                LOGGER(__name__).warning(
                    "Assistant could not join VC %s; trying another assistant: %s",
                    chat_id,
                    exc,
                )
        else:
            raise AssistantErr(
                f"VC Error: {last_error} - (Please check if Voice Chat is turned on in the group)"
            )

        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video: await add_active_video_chat(chat_id)

        if await is_autoend(chat_id):
            counter[chat_id] = {}
            try:
                users = len(await assistant_to_join.get_participants(chat_id))
                if users == 1:
                    autoend[chat_id] = datetime.now() + timedelta(minutes=1)
            except: pass

    async def change_stream(self, client, chat_id):
        active_assistants = await self.get_active_clients(chat_id)
        client = active_assistants[0] if active_assistants else client

        check = db.get(chat_id)
        popped = None
        loop = await get_loop(chat_id)

        try:
            if loop == 0:
                if check: popped = check.pop(0)
            else:
                loop = loop - 1
                await set_loop(chat_id, loop)

            if popped: await auto_clean(popped)

            if not db.get(chat_id): 
                if popped and await is_autoplay_on(chat_id):
                    started = await self.autoplay_start(
                        chat_id,
                        popped.get("chat_id", chat_id),
                        popped.get("title"),
                        popped.get("vidid"),
                        client=client,
                        bot_client=popped.get("client", app)
                    )
                    if started:
                        return

                # ✨ FULLY BOLD AND QUOTE FORMATTED LEAVE MESSAGE
                try:
                    bot_to_send = popped.get("client", app) if popped else app
                    original_chat_id = popped.get("chat_id", chat_id) if popped else chat_id
                    
                    leave_msg = (
                        "> **<tg-emoji emoji-id=\"6102493171441209843\">😲</tg-emoji> ᴏᴏᴘs! ᴛʜᴇ ᴍᴜsɪᴄ ǫᴜᴇᴜᴇ ɪs ᴇᴍᴘᴛʏ...**\n"
                        "> ****\n"
                        "> **<tg-emoji emoji-id=\"5217933090483098080\">🎶</tg-emoji> ᴀᴜᴛᴏᴘʟᴀʏ ɪs ᴄᴜʀʀᴇɴᴛʟʏ ᴏғғ, ᴀɴᴅ ɪ ʜᴀᴠᴇ ɴᴏ ᴍᴏʀᴇ sᴏɴɢs ᴛᴏ ᴘʟᴀʏ.**\n"
                        "> **<tg-emoji emoji-id=\"5298590020796429445\">👋</tg-emoji> ɪ'ᴍ ʟᴇᴀᴠɪɴɢ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ɴᴏᴡ. ᴛʜᴀɴᴋs ғᴏʀ ʟɪsᴛᴇɴɪɴɢ! <tg-emoji emoji-id=\"6127558265573218459\">❤️</tg-emoji>**"
                    )
                    await bot_to_send.send_message(original_chat_id, leave_msg)
                except Exception as e:
                    LOGGER(__name__).error(f"Failed to send leave message: {e}")

                await _clear_(chat_id)
                if chat_id in self.active_clients: del self.active_clients[chat_id]
                try: await client.leave_call(chat_id) 
                except: pass
                return

        except Exception as e:
            LOGGER(__name__).error(f"❌ Error inside change_stream execution framework: {e}")
            await _clear_(chat_id)
            if chat_id in self.active_clients: del self.active_clients[chat_id]
            try: await client.leave_call(chat_id) 
            except: pass
            return

        if db.get(chat_id):
            queued = db[chat_id][0]["file"]
            original_chat_id = db[chat_id][0]["chat_id"]
            streamtype = db[chat_id][0]["streamtype"]
            videoid = db[chat_id][0]["vidid"]
            chat_client = db[chat_id][0].get("client") or app

            db[chat_id][0]["played"] = 0
            exis = db[chat_id][0].get("old_dur")
            if exis:
                db[chat_id][0]["dur"] = exis
                db[chat_id][0]["seconds"] = db[chat_id][0]["old_second"]
                db[chat_id][0]["speed_path"] = None
                db[chat_id][0]["speed"] = 1.0
            video = True if str(streamtype) == "video" else False

            try:
                language = await get_lang(chat_id)
                _ = get_string(language)
            except:
                _ = get_string("en")

            if not db.get(chat_id): return

            raw_title = db[chat_id][0].get("title")
            title = str(raw_title).title() if raw_title else "Unknown Title"
            raw_user = db[chat_id][0].get("by")
            user = str(raw_user) if raw_user and str(raw_user).strip() else "Unknown User"
            duration_str = db[chat_id][0].get("dur", "0:00")
            user_id = db[chat_id][0].get("user_id", 0) 
            
            try:
                bot_username = chat_client.me.username if chat_client.me else app.username
            except:
                bot_username = app.username

            if "live_" in queued:
                n, link = await YouTube.video(videoid, True)
                if n == 0: return await chat_client.send_message(original_chat_id, text=_["call_6"])

                try: await self._safe_change_stream(client, chat_id, link, video)
                except: return await chat_client.send_message(original_chat_id, text=_["call_6"])

                button = telegram_markup(_, chat_id)
                try:
                    run = await chat_client.send_photo(
                        chat_id=original_chat_id, photo=get_random_img(config.STREAM_IMG_URL),
                        caption=_["stream_1"].format(f"https://t.me/{bot_username}?start=info_{videoid}", title[:23], duration_str, user) + _audio_status_html(chat_id),
                        reply_markup=InlineKeyboardMarkup(button)
                    )
                    if db.get(chat_id):
                        db[chat_id][0]["mystic"] = run
                        db[chat_id][0]["markup"] = "tg"
                except: pass

            elif "vid_" in queued:
                mystic = await chat_client.send_message(original_chat_id, _["call_7"])

                try:
                    file_path, direct = await YouTube.download(videoid, mystic, videoid=True, video=video)
                except:
                    try: file_path, direct = await YouTube.download(videoid, mystic, videoid=True, video=video)
                    except:
                        try: await mystic.edit_text("⚠️ **YouTube Timeout! Skipping...**", disable_web_page_preview=True)
                        except: pass
                        await asyncio.sleep(2)
                        return await self.change_stream(client, chat_id)

                if not file_path or str(file_path) == "None":
                    try: await mystic.edit_text("❌ **Error:** Download failed. Skipping track...")
                    except: pass
                    await asyncio.sleep(2)
                    return await self.change_stream(client, chat_id)

                try: await self._safe_change_stream(client, chat_id, file_path, video)
                except: return await chat_client.send_message(original_chat_id, text=_["call_6"])

                img = await get_thumb(videoid, user_id, chat_client) or get_random_img(config.PLAYLIST_IMG_URL)
                
                button = stream_markup(_, chat_id)

                try: await mystic.delete()
                except: pass

                try:
                    run = await chat_client.send_photo(
                        chat_id=original_chat_id, photo=img,
                        caption=_["stream_1"].format(f"https://t.me/{bot_username}?start=info_{videoid}", title[:23], duration_str, user) + _audio_status_html(chat_id),
                        reply_markup=InlineKeyboardMarkup(button)
                    )
                    if db.get(chat_id):
                        db[chat_id][0]["mystic"] = run
                        db[chat_id][0]["markup"] = "stream"
                except: pass

            elif "index_" in queued:
                try: await self._safe_change_stream(client, chat_id, videoid, video)
                except: return await chat_client.send_message(original_chat_id, text=_["call_6"])

                button = telegram_markup(_, chat_id)
                try:
                    run = await chat_client.send_photo(
                        chat_id=original_chat_id, photo=get_random_img(config.STREAM_IMG_URL),
                        caption=_["stream_2"].format(user) + _audio_status_html(chat_id), reply_markup=InlineKeyboardMarkup(button)
                    )
                    if db.get(chat_id):
                        db[chat_id][0]["mystic"] = run
                        db[chat_id][0]["markup"] = "tg"
                except: pass

            else:
                try: await self._safe_change_stream(client, chat_id, queued, video)
                except: return await chat_client.send_message(original_chat_id, text=_["call_6"])

                if videoid == "telegram":
                    button = telegram_markup(_, chat_id)
                    tg_img = get_random_img(config.TELEGRAM_AUDIO_URL) if not video else get_random_img(config.TELEGRAM_VIDEO_URL)
                    try:
                        run = await chat_client.send_photo(
                            chat_id=original_chat_id, photo=tg_img,
                            caption=_["stream_1"].format(config.SUPPORT_CHAT, title[:23], duration_str, user) + _audio_status_html(chat_id),
                            reply_markup=InlineKeyboardMarkup(button)
                        )
                        if db.get(chat_id):
                            db[chat_id][0]["mystic"] = run
                            db[chat_id][0]["markup"] = "tg"
                    except: pass

                elif videoid in ["soundcloud", "spotify", "apple", "jiosaavn"]:
                    button = telegram_markup(_, chat_id)
                    try:
                        run = await chat_client.send_photo(
                            chat_id=original_chat_id, photo=get_random_img(config.SOUNCLOUD_IMG_URL),
                            caption=_["stream_1"].format(config.SUPPORT_CHAT, title[:23], duration_str, user) + _audio_status_html(chat_id),
                            reply_markup=InlineKeyboardMarkup(button)
                        )
                        if db.get(chat_id):
                            db[chat_id][0]["mystic"] = run
                            db[chat_id][0]["markup"] = "tg"
                    except: pass

                else:
                    img = await get_thumb(videoid, user_id, chat_client) or get_random_img(config.PLAYLIST_IMG_URL)
                    
                    button = stream_markup(_, chat_id)
                        
                    try:
                        run = await chat_client.send_photo(
                            chat_id=original_chat_id, photo=img,
                            caption=_["stream_1"].format(f"https://t.me/{bot_username}?start=info_{videoid}", title[:23], duration_str, user) + _audio_status_html(chat_id),
                            reply_markup=InlineKeyboardMarkup(button)
                        )
                        if db.get(chat_id):
                            db[chat_id][0]["mystic"] = run
                            db[chat_id][0]["markup"] = "stream"
                    except: pass

    async def ping(self):
        pings = []
        if getattr(config, "STRING1", None): pings.append(self.one.ping)
        if getattr(config, "STRING2", None): pings.append(self.two.ping)
        if getattr(config, "STRING3", None): pings.append(self.three.ping)
        if getattr(config, "STRING4", None): pings.append(self.four.ping)
        if getattr(config, "STRING5", None): pings.append(self.five.ping)
        return pings

    async def start(self):
        LOGGER(__name__).info("Starting PyTgCalls Client...\n")
        for client in [self.one, self.two, self.three, self.four, self.five]:
            if not client:
                continue
            try:
                await client.start()
                self._started_calls.append(client)
            except Exception:
                LOGGER(__name__).exception("Failed to start one PyTgCalls assistant")
        if not self._started_calls:
            raise RuntimeError("No PyTgCalls assistant could be started")

    async def stop(self):
        for client in reversed(self._started_calls):
            try:
                await client.stop()
            except Exception:
                LOGGER(__name__).warning(
                    "Failed to stop one PyTgCalls assistant", exc_info=True
                )
        self._started_calls.clear()

ANJALI = Call()
