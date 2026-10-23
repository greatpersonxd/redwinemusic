import os
import re
import random
import aiofiles
import aiohttp
import math
from PIL import (Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps)
from youtubesearchpython.__future__ import VideosSearch
from SHIVMUSIC import app

# --- HELPER FUNCTIONS ---
def get_glowing_circle(image):
    img = image.convert("RGBA")
    size = min(img.size)
    img = ImageOps.fit(img, (size, size), centering=(0.5, 0.5))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    circular_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    circular_img.paste(img, (0, 0), mask)
    offset = 50
    glow_size = size + (offset * 2)
    glow = Image.new("RGBA", (glow_size, glow_size), (0, 0, 0, 0))
    draw_glow = ImageDraw.Draw(glow)
    draw_glow.ellipse((5, 5, glow_size-5, glow_size-5), fill=(255, 255, 0, 60))
    draw_glow.ellipse((15, 15, glow_size-15, glow_size-15), fill=(255, 255, 255, 80))
    draw_glow.ellipse((25, 25, glow_size-25, glow_size-25), fill=(255, 105, 180, 150))
    draw_glow.ellipse((35, 35, glow_size-35, glow_size-35), fill=(255, 255, 255, 200))
    glow = glow.filter(ImageFilter.GaussianBlur(15))
    draw_border = ImageDraw.Draw(glow)
    draw_border.ellipse((offset - 4, offset - 4, size + offset + 4, size + offset + 4), outline="white", width=8)
    glow.paste(circular_img, (offset, offset), circular_img)
    return glow, offset

def draw_text_with_glow(draw, position, text, font, fill, glow_fill):
    # Safe check for None strings
    safe_text = str(text) if text else "Unknown"
    x, y = position
    for dx, dy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
        draw.text((x + dx, y + dy), safe_text, font=font, fill=glow_fill)
    draw.text((x, y), safe_text, font=font, fill=fill)

async def download_user_photo(user_id):
    try:
        async for photo in app.get_chat_photos(user_id, limit=1):
            return await app.download_media(photo.file_id, file_name=f"cache/{user_id}.jpg")
    except: return None
    return None

# --- MAIN THUMBNAIL FUNCTION ---
async def get_thumb(videoid, user_id, user_name):
    os.makedirs("cache", exist_ok=True)
    # Bump the cache key whenever the visual treatment changes so old
    # thumbnails do not survive a deployment.
    safe_videoid = re.sub(r"[^a-zA-Z0-9_-]", "_", str(videoid))[:80] or "track"
    final_path = f"cache/{safe_videoid}_{user_id}_v3.png"
    if os.path.exists(final_path): return final_path

    temp_path = f"cache/temp_{safe_videoid}_{user_id}.jpg"
    bg = None

    try:
        results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        data = await results.next()
        result_list = data.get("result", []) if isinstance(data, dict) else []
        result = result_list[0] if result_list else {}
        
        # 🚀 FIX: Prevent NoneType string concatenation error
        raw_title = result.get("title") or "Unknown Title"
        title = re.sub(r"\W+", " ", str(raw_title)).title() if raw_title else "Unknown Title"
        
        duration = str(result.get("duration") or "00:00")
        views = str((result.get("viewCount") or {}).get("short") or "Unknown")
        channel = str((result.get("channel") or {}).get("name") or "Unknown Artist")
        
        # 🚀 FIX: Check if thumbnails exist before downloading
        try:
            if result.get("thumbnails") and len(result["thumbnails"]) > 0:
                thumb_url = result["thumbnails"][0]["url"].split("?")[0]
                async with aiohttp.ClientSession() as session:
                    async with session.get(thumb_url) as resp:
                        if resp.status == 200:
                            f = await aiofiles.open(temp_path, mode="wb")
                            await f.write(await resp.read())
                            await f.close()
        except Exception as e:
            print(f"Failed to fetch thumbnail image from Youtube: {e}")

        # 🚀 FIX: Prevent PIL "Cannot identify image file" error
        try:
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                bg = Image.open(temp_path).convert("RGBA").resize((1920, 1080))
            else:
                bg = Image.new("RGBA", (1920, 1080), (30, 30, 30, 255))
        except Exception as e:
            print(f"PIL Image Read Error: {e} -> Using fallback background.")
            bg = Image.new("RGBA", (1920, 1080), (30, 30, 30, 255))

        background = bg.filter(ImageFilter.GaussianBlur(34))
        shade = Image.new("RGBA", background.size, (5, 9, 16, 172))
        background = Image.alpha_composite(background, shade)
        
        black_card = Image.new("RGBA", background.size, (0, 0, 0, 0))
        draw_card = ImageDraw.Draw(black_card)
        draw_card.rounded_rectangle((55, 55, 1865, 950), radius=42, fill=(8, 12, 20, 238), outline=(255, 255, 255, 42), width=3)
        background = Image.alpha_composite(background, black_card)
        draw = ImageDraw.Draw(background, "RGBA")

        # Shine overlay: a soft diagonal highlight and small specular points
        # give the player card the requested glossy finish.
        shine = Image.new("RGBA", background.size, (0, 0, 0, 0))
        shine_draw = ImageDraw.Draw(shine, "RGBA")
        shine_draw.rounded_rectangle((75, 75, 1845, 930), radius=34, outline=(91, 214, 255, 85), width=2)
        shine_draw.polygon([(80, 80), (520, 80), (1110, 930), (880, 930)], fill=(255, 255, 255, 10))
        shine = shine.filter(ImageFilter.GaussianBlur(8))
        background = Image.alpha_composite(background, shine)
        draw = ImageDraw.Draw(background, "RGBA")
        
        try:
            f1 = ImageFont.truetype("SHIVMUSIC/assets/font.ttf", 65)
            f2 = ImageFont.truetype("SHIVMUSIC/assets/font2.ttf", 45)
            br = ImageFont.truetype("SHIVMUSIC/assets/font2.ttf", 55)
            f_small = ImageFont.truetype("SHIVMUSIC/assets/font2.ttf", 30)
        except:
            f1 = f2 = br = f_small = ImageFont.load_default()

        # Images
        try:
            cover = ImageOps.fit(bg.convert("RGB"), (510, 510), centering=(0.5, 0.5)).convert("RGBA")
            cover_mask = Image.new("L", cover.size, 0)
            ImageDraw.Draw(cover_mask).rounded_rectangle((0, 0, 509, 509), radius=38, fill=255)
            shadow = Image.new("RGBA", (570, 570), (0, 0, 0, 0))
            ImageDraw.Draw(shadow).rounded_rectangle((20, 20, 550, 550), radius=48, fill=(0, 0, 0, 180))
            shadow = shadow.filter(ImageFilter.GaussianBlur(18))
            background.paste(shadow, (85, 220), shadow)
            background.paste(cover, (115, 240), cover_mask)
        except Exception as e:
            print(f"Error drawing YT circle: {e}")
        
        u_photo = await download_user_photo(user_id)
        if u_photo and os.path.exists(u_photo):
            try:
                avatar = ImageOps.fit(Image.open(u_photo).convert("RGB"), (118, 118)).convert("RGBA")
                avatar_mask = Image.new("L", avatar.size, 0)
                ImageDraw.Draw(avatar_mask).ellipse((0, 0, 117, 117), fill=255)
                draw.ellipse((1637, 95, 1771, 229), fill=(91, 214, 255, 80))
                background.paste(avatar, (1645, 103), avatar_mask)
            except Exception as e:
                print(f"Error processing User Photo: {e}")

        # Texts
        safe_title = (title[:28] + "...") if len(title) > 28 else title
        draw.text((700, 285), "NOW PLAYING", fill=(91, 214, 255), font=f_small)
        draw.text((700, 350), safe_title, fill="white", font=f1)
        draw.text((700, 455), channel[:34], fill=(202, 210, 222), font=f2)
        draw.text((700, 535), f"{duration}   •   {views} views", fill=(139, 151, 169), font=f_small)

        # --- UNIFORM DYNAMIC WAVEFORM ---
        bar_count = 72; bar_width = 6; bar_gap = 14
        total_width = bar_count * bar_gap
        start_x = (1920 - total_width) / 2; base_y = 760 
        
        waveform_rng = random.Random(str(videoid))
        for i in range(bar_count):
            h = waveform_rng.randint(15, 45)
            x0 = start_x + (i * bar_gap); x1 = x0 + bar_width
            y0 = base_y - h; y1 = base_y + h
            fill_color = (91, 214, 255, 255) if i < (bar_count // 2) else (104, 116, 135, 190)
            if x1 > x0: draw.rounded_rectangle((x0, y0, x1, y1), radius=3, fill=fill_color)

        # --- PROGRESS LINE & ICONS ---
        line_y = base_y + 55
        draw.line([(start_x, line_y), (start_x + total_width, line_y)], fill=(80, 80, 80), width=1)
        draw.line([(start_x, line_y), (start_x + (total_width // 2), line_y)], fill=(255, 255, 255), width=2)
        draw.ellipse(((start_x + total_width // 2) - 8, line_y - 8, (start_x + total_width // 2) + 8, line_y + 8), fill="white")
        draw.text((start_x, line_y + 20), "00:00", fill="white", font=f_small)
        draw.text((start_x + total_width - 80, line_y + 20), duration, fill="white", font=f_small)

        ctrl_y = line_y + 50 
        mid_x = 960
        
        # Play / Pause Icon
        draw.ellipse((mid_x - 30, ctrl_y - 30, mid_x + 30, ctrl_y + 30), outline="white", width=3)
        draw.polygon([(mid_x - 8, ctrl_y - 12), (mid_x + 14, ctrl_y), (mid_x - 8, ctrl_y + 12)], fill="white")
        
        # Previous / Next Icons
        draw.ellipse((mid_x - 80, ctrl_y - 20, mid_x - 45, ctrl_y + 20), outline="white", width=2)
        draw.ellipse((mid_x + 45, ctrl_y - 20, mid_x + 80, ctrl_y + 20), outline="white", width=2)

        # Branding
        draw_text_with_glow(draw, (80, 985), "BETA BOT HUB", br, (132, 224, 240), (0, 255, 255, 80))
        draw.text((1540, 995), "PREMIUM MUSIC", fill=(190, 198, 210), font=f_small)

        background.convert("RGB").save(final_path, "PNG")
        return final_path
    except Exception as e:
        print(f"Thumbnail General Error: {e}")
        return None
    finally:
        if os.path.exists(temp_path): 
            try: os.remove(temp_path)
            except: pass
        if 'u_photo' in locals() and u_photo and os.path.exists(u_photo): 
            try: os.remove(u_photo)
            except: pass
