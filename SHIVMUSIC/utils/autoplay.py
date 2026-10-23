import asyncio
import glob
import os
import random

import yt_dlp
from py_yt import VideosSearch

# =========================================================
# PER-CHAT PLAY HISTORY (in-memory, session based)
# Used only to make sure autoplay never repeats a song it
# already played for that chat.
# =========================================================
_HISTORY_LIMIT = 50
_played_history: dict[int, list[str]] = {}


def remember_played(chat_id: int, vidid: str):
    if not vidid:
        return
    hist = _played_history.setdefault(chat_id, [])
    if vidid in hist:
        hist.remove(vidid)
    hist.append(vidid)
    if len(hist) > _HISTORY_LIMIT:
        del hist[: len(hist) - _HISTORY_LIMIT]


def _history(chat_id: int) -> list:
    return _played_history.get(chat_id, [])


def clear_history(chat_id: int):
    _played_history.pop(chat_id, None)


def _extract_candidates(results, chat_id: int, skip_history: bool):
    candidates = []
    played = [] if skip_history else _history(chat_id)
    for video in results:
        vidid = video.get("id")
        title = video.get("title")
        link = video.get("link")
        duration = video.get("duration")
        if not (vidid and title and link and duration):
            continue
        if vidid in played:
            continue
        thumbs = video.get("thumbnails") or []
        thumb = thumbs[0].get("url", "").split("?")[0] if thumbs else None
        candidates.append(
            {
                "vidid": vidid,
                "title": title,
                "link": link,
                "duration_min": duration,
                "thumb": thumb,
            }
        )
    return candidates


# =========================================================
# ASHOK-STYLE: YouTube Mix playlist ("RD" + videoID)
# Genuinely YouTube's own "related songs" algorithm — much
# better variety than a plain title-text search, which often
# just returns covers/remixes of the same song.
# =========================================================

def _cookie_file():
    folder = os.path.join(os.getcwd(), "ShiviMusic", "assets")
    txt_files = glob.glob(os.path.join(folder, "*.txt"))
    if not txt_files:
        return None
    return random.choice(txt_files)


def _fetch_mix_sync(video_id: str, limit: int = 20) -> list:
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
        "playlistend": limit,
        "no_warnings": True,
    }
    cookiefile = _cookie_file()
    if cookiefile:
        ydl_opts["cookiefile"] = cookiefile
    url = f"https://www.youtube.com/watch?v={video_id}&list=RD{video_id}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return (info or {}).get("entries") or []


def _extract_mix_candidates(entries, chat_id: int, skip_history: bool):
    candidates = []
    played = [] if skip_history else _history(chat_id)
    for e in entries or []:
        if not e:
            continue
        vidid = e.get("id")
        title = e.get("title")
        if not (vidid and title):
            continue
        if vidid in played:
            continue
        duration = e.get("duration")
        if isinstance(duration, (int, float)):
            m, s = divmod(int(duration), 60)
            duration_min = f"{m}:{s:02d}"
        else:
            duration_min = str(duration) if duration else "Live"
        candidates.append(
            {
                "vidid": vidid,
                "title": title,
                "link": f"https://www.youtube.com/watch?v={vidid}",
                "duration_min": duration_min,
                "thumb": e.get("thumbnail")
                or f"https://i.ytimg.com/vi/{vidid}/hqdefault.jpg",
            }
        )
    return candidates


async def _fetch_mix_candidates(chat_id: int, seed_vidid: str) -> list:
    loop = asyncio.get_running_loop()
    try:
        entries = await loop.run_in_executor(None, _fetch_mix_sync, seed_vidid, 20)
    except Exception as e:
        print(f"[AUTOPLAY MIX ERROR] {e}")
        return []

    candidates = _extract_mix_candidates(entries, chat_id, skip_history=False)
    if not candidates:
        # Sab kuch is Mix se already played ho chuka -> history reset karke
        # dobara try karo, taaki autoplay kabhi stall na ho
        clear_history(chat_id)
        candidates = _extract_mix_candidates(entries, chat_id, skip_history=True)
    return candidates


async def fetch_autoplay_track(chat_id: int, seed_title: str, seed_vidid: str = None):
    """
    Primary: Ashok-Go style — seed video ka YouTube "Mix"/radio playlist
    ("RD" + videoID) fetch karta hai, phir un candidates me se random pick.
    Fallback: agar seed_vidid na ho ya Mix fetch fail ho jaaye (network
    issue, video unavailable, etc.), purana title-text search wala
    approach use hota hai — taaki autoplay kabhi silently stall na ho.
    """
    if seed_vidid:
        mix_candidates = await _fetch_mix_candidates(chat_id, seed_vidid)
        if mix_candidates:
            return random.choice(mix_candidates)

    if not seed_title:
        return None

    query = f"{seed_title}"
    try:
        search = VideosSearch(query, limit=20)
        data = await search.next()
        results = data.get("result", []) if isinstance(data, dict) else []
    except Exception as e:
        print(f"[AUTOPLAY SEARCH ERROR] {e}")
        return None

    if not results:
        return None

    candidates = _extract_candidates(results, chat_id, skip_history=False)

    if not candidates:
        # Everything from this search was already played recently.
        # Reset the history for this chat and try again from the same
        # result set so autoplay never just stalls out.
        clear_history(chat_id)
        candidates = _extract_candidates(results, chat_id, skip_history=True)

    if not candidates:
        return None

    return random.choice(candidates)

# ===========================================================
# ©️ 2026-27 All Rights Reserved by Beta Bots  😎
#
# 🧑‍💻 Developer : t.me/SUKOON_s
# 📢 Telegram channel : t.me/BETABOT_HUB
# ===========================================================
