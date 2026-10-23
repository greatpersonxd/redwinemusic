import os
import time
import asyncio
import gc
import shutil
import config
from config import autoclean
from SHIVMUSIC import LOGGER, app
from pyrogram import filters
from pyrogram.types import Message

# Settings
WEEK_IN_SECONDS = 7 * 24 * 60 * 60
ONE_DAY_IN_SECONDS = 24 * 60 * 60
ONE_MIN_IN_SECONDS = 60  # Welcome images ke liye 1 minute
MAX_CACHE_SIZE = 5 * 1024 * 1024 * 1024  # 5 GB Total Cache
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB Max File

# Advanced Autoclean Thresholds
AVG_SONG_SIZE = 10 * 1024 * 1024  # Maan lijiye 1 song approx 10MB ka hai
BUFFER_SPACE = 15 * AVG_SONG_SIZE  # 15 songs ka space (~150MB)
ADVANCED_THRESHOLD = MAX_CACHE_SIZE - BUFFER_SPACE  # Jab cache yahan tak pahuchega, cleaning shuru hogi

async def auto_clean(popped):
    current_time = time.time()
    
    # ==========================================
    # 1. IMAGE CLEANUP (Welcome Image 1-Minute Auto Delete)
    # ==========================================
    try:
        image_directory = "./downloads"
        if os.path.exists(image_directory):
            for img_file in os.listdir(image_directory):
                if img_file.lower().endswith((".png", ".jpg", ".jpeg")):
                    img_path = os.path.join(image_directory, img_file)
                    
                    if os.path.exists(img_path):
                        try:
                            img_age = current_time - os.path.getctime(img_path)
                            # Image ko 1 min (60 seconds) ke baad delete karna
                            if img_age > ONE_MIN_IN_SECONDS:
                                os.remove(img_path)
                                LOGGER(__name__).info(f"🗑️ Auto-deleted old image (1 min passed): {img_file}")
                        except Exception:
                            pass
                await asyncio.sleep(0) 
    except Exception as e:
        LOGGER(__name__).error(f"Image Auto-Clean Error: {e}")

    # ==========================================
    # 2. ADVANCED SONG CACHE CLEANUP
    # ==========================================
    if not popped:
        return
        
    try:
        rem = popped.get("file")
        if not rem:
            return

        try:
            if rem in autoclean:
                autoclean.remove(rem)
        except Exception:
            pass
            
        if not os.path.exists(rem):
            return

        directory = os.path.dirname(rem)
        if not directory or not os.path.exists(directory):
            return

        deleted_files = []
        deleted_large_files = []
        all_files = []
        current_cache_size = 0
        
        # Check and DELETE > 500MB file immediately
        try:
            rem_size = os.path.getsize(rem)
            if rem_size > MAX_FILE_SIZE:
                os.remove(rem)
                deleted_large_files.append(os.path.basename(rem))
                LOGGER(__name__).info(f"🗑️ Deleted >500MB file immediately: {rem}")
        except Exception:
            pass

        # Gather all files safely
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                if "live_" not in filepath and "index_" not in filepath:
                    try:
                        f_size = os.path.getsize(filepath)
                        f_age = current_time - os.path.getctime(filepath)
                        
                        all_files.append({
                            "path": filepath, 
                            "name": filename, 
                            "size": f_size, 
                            "age": f_age
                        })
                        current_cache_size += f_size
                    except Exception:
                        pass
            await asyncio.sleep(0)
                
        # Age ke hisaab se sort karein (Oldest first)
        all_files.sort(key=lambda x: x["age"], reverse=True)
        
        deleted_in_adv_clean = 0
        
        # Delete old/extra files
        for f in all_files:
            filepath = f["path"]
            if not os.path.exists(filepath):
                continue
                
            # 🚀 ADVANCED AUTOCLEAN: Jab storage full hone wali ho (15 songs limit)
            if current_cache_size > ADVANCED_THRESHOLD and deleted_in_adv_clean < 10:
                if filepath not in autoclean:
                    try:
                        os.remove(filepath)
                        deleted_files.append(f["name"])
                        current_cache_size -= f["size"] 
                        deleted_in_adv_clean += 1
                        LOGGER(__name__).info(f"🗑️ Adv Clean - Deleted oldest song: {filepath}")
                    except Exception:
                        pass
                    continue
            
            # Normal Weekly Auto-Clean Backup
            if (f["age"] > WEEK_IN_SECONDS or current_cache_size > MAX_CACHE_SIZE) and filepath not in autoclean:
                try:
                    os.remove(filepath)
                    deleted_files.append(f["name"])
                    current_cache_size -= f["size"] 
                    LOGGER(__name__).info(f"🗑️ Cleaned cached file: {filepath}")
                except Exception:
                    pass
            await asyncio.sleep(0)
                
        # Send Notification
        logger_id = getattr(config, "LOG_GROUP_ID", getattr(config, "LOGGER_ID", None))
        if logger_id and (deleted_large_files or deleted_files):
            log_text = ""
            
            if deleted_large_files:
                formatted_large = "\n".join([f"> `{name}`" for name in deleted_large_files])
                log_text += f"🚨 **Big File Auto-Cleaned (>500MB)**\n{formatted_large}\n\n"
                
            if deleted_files:
                formatted_songs = "\n".join([f"> `{name}`" for name in deleted_files])
                if len(formatted_songs) > 3000:
                    formatted_songs = formatted_songs[:3000] + "\n> `...aur baaki files.`"
                log_text += (
                    "🗑️ **Storage Cache Cleaned**\n\n"
                    "**Neeche diye gaye purane songs space free karne ke liye delete kiye gaye hain:**\n"
                    f"{formatted_songs}"
                )
                
            if log_text:
                try:
                    await app.send_message(int(logger_id), log_text)
                except Exception:
                    pass

    except Exception as e:
        LOGGER(__name__).error(f"Song Auto-Clean Error: {e}")


# 🚀 9. COMMAND: /cdust (Manual cleanup)
@app.on_message(filters.command("cdust") & filters.user(config.OWNER_ID))
async def clean_dust_command(client, message: Message):
    m = await message.reply_text("⏳ `Scanning dust... checking files older than 1 day...`")
    
    directories = ["./downloads", "./music_cache"]
    current_time = time.time()
    deleted_count = 0
    freed_space = 0
    deleted_files_list = []

    try:
        for directory in directories:
            if not os.path.exists(directory):
                continue
                
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    if "live_" not in filepath and "index_" not in filepath:
                        try:
                            f_age = current_time - os.path.getctime(filepath)
                            
                            if f_age > ONE_DAY_IN_SECONDS and filepath not in autoclean:
                                f_size = os.path.getsize(filepath)
                                os.remove(filepath)
                                deleted_count += 1
                                freed_space += f_size
                                deleted_files_list.append(filename)
                        except Exception:
                            pass
                await asyncio.sleep(0)

        gc.collect()

        if deleted_count > 0:
            freed_mb = round(freed_space / (1024 * 1024), 2)
            
            await m.edit_text(
                f"🧹 **Dust Cleaned Successfully!**\n\n"
                f"🗑 **Deleted Files:** `{deleted_count}`\n"
                f"💾 **Freed Space:** `{freed_mb} MB`\n"
                f"📝 **Note:** `Details sent to Logger Group.`"
            )
            
            logger_id = getattr(config, "LOG_GROUP_ID", getattr(config, "LOGGER_ID", None))
            if logger_id and deleted_files_list:
                formatted_dust = "\n".join([f"> `{name}`" for name in deleted_files_list])
                
                if len(formatted_dust) > 3000:
                    formatted_dust = formatted_dust[:3000] + "\n> `...aur baaki files.`"
                    
                log_text = (
                    f"🧹 **Manual Dust Cleaned (/cdust)**\n\n"
                    f"**Total {freed_mb} MB space free kiya gaya.**\n"
                    f"**Neeche diye gaye 1 din se purane files delete kiye gaye hain:**\n"
                    f"{formatted_dust}"
                )
                try:
                    await app.send_message(int(logger_id), log_text)
                except Exception:
                    pass
        else:
            await m.edit_text("✨ `No dusty files found. Storage is already clean! (Kept files from the last 24 hours)`")
            
    except Exception as e:
        await m.edit_text(f"⚠️ **Error occurred:** `{e}`")


# 🚀 10. COMMAND: /downloads (Check total storage usage and file list)
@app.on_message(filters.command("downloads") & filters.user(config.OWNER_ID))
async def check_downloads_command(client, message: Message):
    m = await message.reply_text("⏳ `Checking server storage and downloaded files...`")
    
    directories = ["./downloads", "./music_cache"]
    total_files = 0
    total_size_bytes = 0
    file_list = []
    
    try:
        for directory in directories:
            if not os.path.exists(directory):
                continue
                
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    if "live_" not in filepath and "index_" not in filepath:
                        try:
                            f_size = os.path.getsize(filepath)
                            total_files += 1
                            total_size_bytes += f_size
                            
                            f_size_mb = round(f_size / (1024 * 1024), 2)
                            icon = "🖼️" if filename.lower().endswith((".png", ".jpg", ".jpeg")) else "🎧"
                            file_list.append(f"{icon} `{filename}` ({f_size_mb} MB)")
                        except Exception:
                            pass
                await asyncio.sleep(0)
                    
        disk_info = shutil.disk_usage(".")
        server_free_gb = round(disk_info.free / (1024 * 1024 * 1024), 2)
        server_total_gb = round(disk_info.total / (1024 * 1024 * 1024), 2)
        
        if total_size_bytes >= (1024 * 1024 * 1024):
            size_formatted = f"{round(total_size_bytes / (1024 * 1024 * 1024), 2)} GB"
        else:
            size_formatted = f"{round(total_size_bytes / (1024 * 1024), 2)} MB"
            
        header_text = (
            f"📁 **Server Storage Status**\n\n"
            f"💽 **Server Total Space:** `{server_total_gb} GB`\n"
            f"🟢 **Server Free Space:** `{server_free_gb} GB`\n\n"
            f"🎵 **Total Cached Files:** `{total_files}`\n"
            f"💾 **Space Occupied by Bot:** `{size_formatted}`\n\n"
            f"📑 **Downloaded File List:**\n"
        )
        
        if file_list:
            songs_text = "\n".join(file_list)
        else:
            songs_text = "`No downloaded files found.`"
            
        footer_text = "\n\n💡 _Tip: Storage clean karne ke liye /cdust ka use karein._"
        full_text = header_text + songs_text + footer_text
        
        if len(full_text) > 4000:
            allowed_length = 4000 - len(header_text) - len(footer_text) - 50
            truncated_songs = songs_text[:allowed_length]
            truncated_songs = truncated_songs.rsplit('\n', 1)[0] 
            full_text = header_text + truncated_songs + "\n\n... `aur baaki files (Message too long)`" + footer_text
            
        await m.edit_text(full_text)
        
    except Exception as e:
        await m.edit_text(f"⚠️ **Error occurred:** `{e}`")
