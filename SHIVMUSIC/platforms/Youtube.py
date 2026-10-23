import asyncio
import os
import re
import time
import yt_dlp
import aiohttp
import logging
import config  
from typing import Union
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch, Playlist

# ----------------- CONFIGURATION -----------------
DOWNLOAD_DIR = "downloads"
LOGGER = logging.getLogger("BETA BOT HUB | 👑 THE SHIV")

# 🟢 Primary API (Shruti)
SHRUTI_API_URL = os.environ.get("SHRUTI_API_URL", "https://shrutibots.site")
SHRUTI_API_KEY = os.environ.get("SHRUTI_API_KEY", "")

# 🟡 Secondary API (MusicSp)
MUSICSP_API_URL = os.environ.get("MusicSp_API_URL", "https://apisparrow.site")
MUSICSP_API_KEY = os.environ.get("MusicSp_API_KEY", "Enter Your Api")

def time_to_seconds(time_str):
    stringt = str(time_str)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))

def get_safe_filename(title: str, default_id: str) -> str:
    if not title:
        return default_id
    return re.sub(r'[\\/*?:"<>|]', "", title).strip()

def extract_video_id(link: str) -> str:
    if "youtu.be/" in link:
        return link.split("youtu.be/")[1].split("?")[0]
    elif "v=" in link:
        return link.split("v=")[1].split("&")[0]
    return link

# Helper for Safe Async Execution
async def _async_run(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

# ----------------- DOWNLOADERS -----------------

# Unified Downloader Function for Fast & Smooth API switching
async def external_api_download(api_url: str, api_key: str, video_id: str, download_type: str, title: str = None, api_name: str = "API") -> str:
    if not api_url or not api_key:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    filename = get_safe_filename(title, f"{api_name[:3]}_{video_id}")
    ext = "mp4" if download_type == "video" else "mp3"
    file_path = os.path.join(DOWNLOAD_DIR, f"{filename}.{ext}")

    if os.path.exists(file_path) and os.path.getsize(file_path) > 50000:
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            params = {
                "url": video_id, 
                "type": "audio" if download_type == "audio" else "video", 
                "api_key": api_key
            }
            async with session.get(
                f"{api_url}/download",
                params=params,
                timeout=aiohttp.ClientTimeout(total=600)
            ) as resp:
                if resp.status != 200:
                    LOGGER.error(f"🔴 {api_name} Error: Status {resp.status}")
                    return None

                with open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(131072):
                        f.write(chunk)

        if os.path.exists(file_path) and os.path.getsize(file_path) > 50000:
            LOGGER.info(f"🟢 SOURCE-HOPPING SUCCESS: Downloaded '{title}' from {api_name}!")
            return file_path
        else:
            LOGGER.warning(f"🔴 {api_name} returned corrupted/empty file for '{title}'. Rejecting it.")
            return None
    except Exception as e:
        LOGGER.error(f"{api_name} Download Error: {e}")
        if os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass
        return None

async def download_song(link: str, title: str = None) -> str:
    video_id = extract_video_id(link)
    if not video_id or len(video_id) < 3: return None

    if not title:
        try:
            search = VideosSearch(video_id, limit=1)
            res = await search.next()
            if res and res.get("result"): title = res["result"][0]["title"]
        except Exception: pass

    # 1. Primary API (Shruti)
    shruti_result = await external_api_download(SHRUTI_API_URL, SHRUTI_API_KEY, video_id, "audio", title, "Shruti")
    if shruti_result: return shruti_result

    LOGGER.warning(f"🔴 Shruti API failed for '{title}'. Hopping to MusicSp API...")

    # 2. Secondary API (MusicSp Fallback)
    musicsp_result = await external_api_download(MUSICSP_API_URL, MUSICSP_API_KEY, video_id, "audio", title, "MusicSp")
    if musicsp_result: return musicsp_result
    
    LOGGER.error(f"🔴 Both Shruti and MusicSp APIs failed to download '{title}'.")
    return None

async def download_video(link: str, title: str = None) -> str:
    video_id = extract_video_id(link)
    if not video_id or len(video_id) < 3: return None

    if not title:
        try:
            search = VideosSearch(video_id, limit=1)
            res = await search.next()
            if res and res.get("result"): title = res["result"][0]["title"]
        except: pass

    # 1. Primary API (Shruti)
    shruti_result = await external_api_download(SHRUTI_API_URL, SHRUTI_API_KEY, video_id, "video", title, "Shruti")
    if shruti_result: return shruti_result

    LOGGER.warning(f"🔴 Shruti API failed for '{title}'. Hopping to MusicSp API...")

    # 2. Secondary API (MusicSp Fallback)
    musicsp_result = await external_api_download(MUSICSP_API_URL, MUSICSP_API_KEY, video_id, "video", title, "MusicSp")
    if musicsp_result: return musicsp_result
    
    LOGGER.error(f"🔴 Both Shruti and MusicSp APIs failed to download '{title}'.")
    return None

# ----------------- YOUTUBE API CLASS -----------------

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset: entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]

        try:
            results = VideosSearch(link, limit=1)
            response = await results.next()
            if response and response.get("result"):
                for result in response["result"]:
                    title = result["title"]
                    duration_min = result["duration"]
                    thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                    vidid = result["id"]
                    duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
                    return title, duration_min, duration_sec, thumbnail, vidid
        except Exception:
            pass

        try:
            ydl_opts = {
                "quiet": True, 
                "extract_flat": True, 
                "noplaylist": True,
                "extractor_args": {"youtube": ["player_client=ios,tv_embedded"]} 
            } 
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            search_query = link if "youtube.com" in link or "youtu.be" in link else f"ytsearch1:{link}"

            r = await _async_run(ydl.extract_info, search_query, download=False)
            if r and "entries" in r and len(r["entries"]) > 0:
                entry = r["entries"][0]
                title = entry.get("title")
                vidid = entry.get("id")
                dur_sec = int(entry.get("duration", 0))
                m, s = divmod(dur_sec, 60)
                h, m = divmod(m, 60)
                duration_min = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
                thumbnail = f"https://img.youtube.com/vi/{vidid}/hqdefault.jpg"
                return title, duration_min, dur_sec, thumbnail, vidid
        except Exception as e:
            LOGGER.error(f"yt-dlp search fallback failed in details: {e}")
        return None, None, None, None, None

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]
        try:
            results = VideosSearch(link, limit=1)
            for result in (await results.next())["result"]:
                return result["title"]
        except Exception:
            return "Unknown Title"

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]
        try:
            results = VideosSearch(link, limit=1)
            for result in (await results.next())["result"]:
                return result["duration"]
        except Exception:
            return "0:00"

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        vid_id_str = link if videoid else extract_video_id(link)
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]
        try:
            results = VideosSearch(link, limit=1)
            for result in (await results.next())["result"]:
                return result["thumbnails"][0]["url"].split("?")[0]
        except Exception:
            if vid_id_str and len(vid_id_str) > 5:
                return f"https://img.youtube.com/vi/{vid_id_str}/hqdefault.jpg"
            return "https://telegra.ph/file/2e3d368e77c449c287430.jpg"

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]
        try:
            downloaded_file = await download_video(link)
            if downloaded_file:
                return 1, downloaded_file
            return 0, "Video download failed"
        except Exception as e:
            return 0, f"Video download error: {e}"

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid: link = self.listbase + link
        if "&" in link: link = link.split("&")[0]
        try:
            plist = await _async_run(Playlist.get, link)
        except Exception:
            return []
        videos = plist.get("videos") or []
        ids = []
        for data in videos[:limit]:
            if not data: continue
            vid = data.get("id")
            if not vid: continue
            ids.append(vid)
        return ids

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]

        try:
            results = VideosSearch(link, limit=1)
            response = await results.next()
            if response and response.get("result"):
                result = response["result"][0]
                return {
                    "title": result["title"],
                    "link": result["link"],
                    "vidid": result["id"],
                    "duration_min": result["duration"],
                    "thumb": result["thumbnails"][0]["url"].split("?")[0],
                }, result["id"]
        except Exception:
            pass

        try:
            ydl_opts = {
                "quiet": True, 
                "extract_flat": True, 
                "noplaylist": True,
                "extractor_args": {"youtube": ["player_client=ios,tv_embedded"]} 
            }
            ydl = yt_dlp.YoutubeDL(ydl_opts)
            search_query = link if "youtube.com" in link or "youtu.be" in link else f"ytsearch1:{link}"
            r = await _async_run(ydl.extract_info, search_query, download=False)

            if r and "entries" in r and len(r["entries"]) > 0:
                entry = r["entries"][0]
                vidid = entry.get("id")
                dur_sec = int(entry.get("duration", 0))
                m, s = divmod(dur_sec, 60)
                h, m = divmod(m, 60)

                return {
                    "title": entry.get("title"),
                    "link": f"https://www.youtube.com/watch?v={vidid}",
                    "vidid": vidid,
                    "duration_min": f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}",
                    "thumb": f"https://img.youtube.com/vi/{vidid}/hqdefault.jpg",
                }, vidid
        except Exception as e:
            LOGGER.error(f"yt-dlp search fallback failed in track: {e}")

        return None, None

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]

        ytdl_opts = {
            "quiet": True,
            "extractor_args": {"youtube": ["player_client=ios,tv_embedded"]},
            "external_downloader": "aria2c",
            "external_downloader_args": [
                "-x", "16",            
                "-s", "16",            
                "-k", "1M",            
                "--allow-piece-length-change=true"
            ]
        }

        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        formats_available = []

        try:
            r = await _async_run(ydl.extract_info, link, download=False)
            if r and "formats" in r:
                for format in r["formats"]:
                    try:
                        if "dash" not in str(format.get("format", "")).lower():
                            formats_available.append({
                                "format": format.get("format"),
                                "filesize": format.get("filesize"),
                                "format_id": format.get("format_id"),
                                "ext": format.get("ext"),
                                "format_note": format.get("format_note"),
                                "yturl": link,
                            })
                    except Exception: continue
        except Exception:
            pass

        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        raw_vid_str = link if videoid else extract_video_id(link)
        if videoid: link = self.base + link
        if "&" in link: link = link.split("&")[0]

        try:
            a = VideosSearch(link, limit=10)
            result = (await a.next()).get("result")
            return result[query_type]["title"], result[query_type]["duration"], result[query_type]["thumbnails"][0]["url"].split("?")[0], result[query_type]["id"]
        except Exception:
            fallback_thumb = f"https://img.youtube.com/vi/{raw_vid_str}/hqdefault.jpg" if raw_vid_str and len(raw_vid_str) > 5 else "https://telegra.ph/file/2e3d368e77c449c287430.jpg"
            return "Unknown Title", "0:00", fallback_thumb, "None"

    async def download(
        self, link: str, mystic, video: Union[bool, str] = None, videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None, songvideo: Union[bool, str] = None, format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid: link = self.base + link
        try:
            file_title = title if isinstance(title, str) else None

            if video: downloaded_file = await download_video(link, title=file_title)
            else: downloaded_file = await download_song(link, title=file_title)

            if downloaded_file: return downloaded_file, True
            return None, False
        except Exception as e:
            LOGGER.error(f"Error in YouTubeAPI.download: {e}")
            return None, False

    async def autoplay(self, last_vidid: str, title: str, max_duration: int = None):
        try:
            import random
            search_query = f"{title} official audio"
            valid_choices = []

            try:
                search = VideosSearch(search_query, limit=15)
                result = await search.next()
                if result and result.get("result"):
                    for res in result["result"]:
                        vidid = str(res.get("id") or "")
                        if not vidid or vidid == "None" or vidid == last_vidid: continue

                        dur_str = str(res.get("duration", "0:00"))
                        dur_sec = 0
                        if dur_str and ":" in dur_str:
                            parts = dur_str.split(":")
                            try:
                                if len(parts) == 2: dur_sec = int(parts[0]) * 60 + int(parts[1])
                                elif len(parts) == 3: dur_sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                            except ValueError: pass

                        if dur_sec < 30: continue
                        if max_duration and dur_sec > max_duration: continue

                        valid_choices.append({
                            "vidid": vidid,
                            "title": str(res.get("title", "Unknown Title")).title(),
                            "duration_min": dur_str,
                            "duration_sec": dur_sec
                        })
            except Exception: pass 

            if not valid_choices:
                ytdl_opts = {
                    "quiet": True, 
                    "extract_flat": True, 
                    "noplaylist": True,
                    "extractor_args": {"youtube": ["player_client=ios,tv_embedded"]} 
                } 
                ydl = yt_dlp.YoutubeDL(ytdl_opts)

                r = await _async_run(ydl.extract_info, f"ytsearch10:{search_query}", download=False)
                if r and "entries" in r:
                    for entry in r["entries"]:
                        vidid = entry.get("id")
                        if not vidid or vidid == last_vidid: continue

                        raw_dur = entry.get("duration", 0)
                        try: dur_sec = int(float(raw_dur)) if raw_dur else 0
                        except (ValueError, TypeError): dur_sec = 0

                        if not dur_sec or dur_sec < 30: continue
                        if max_duration and dur_sec > max_duration: continue

                        m, s = divmod(dur_sec, 60)
                        h, m = divmod(m, 60)
                        dur_str = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

                        valid_choices.append({
                            "vidid": vidid,
                            "title": str(entry.get("title", "Unknown Title")).title(),
                            "duration_min": dur_str,
                            "duration_sec": dur_sec
                        })

            if valid_choices: return random.choice(valid_choices)
            return None

        except Exception as e:
            LOGGER.error(f"YouTube Autoplay Function Error: {e}")
            return None

YouTube = YouTubeAPI()
