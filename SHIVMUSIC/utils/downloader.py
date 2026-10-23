from os import path
import yt_dlp
from yt_dlp.utils import DownloadError

# Global instance (Optional usage)
ytdl = yt_dlp.YoutubeDL(
    {
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "format": "bestaudio[ext=m4a]",
        "geo_bypass": True,
        "nocheckcertificate": True,
    }
)

def download(url: str, my_hook) -> str:        
    ydl_optssx = {
        'format' : 'bestaudio[ext=m4a]',
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "geo_bypass": True,
        "nocheckcertificate": True,
        'quiet': True,
        'no_warnings': True,
        # --- NEW ANTI-LAG SETTINGS (Ye zaruri hai) ---
        'http_chunk_size': 10485760,  # 10MB ka Buffer (Hichki rokega)
        'socket_timeout': 10,         # Agar net slow ho to jaldi retry karega
        'retries': 10,                # Fail hone par 10 baar koshish karega
        'noprogress': True,           # Logs kam karega taaki CPU bache
    }
    
    # Song ki info nikaal rahe hain taaki ID aur EXT mil sake
    info = ytdl.extract_info(url, False)
    
    try:
        x = yt_dlp.YoutubeDL(ydl_optssx)
        x.add_progress_hook(my_hook)
        x.download([url])
    except Exception as y_e:
        print(y_e)
        return None # Error aane par None return karega
    
    # File path bana rahe hain
    xyz = path.join("downloads", f"{info['id']}.{info['ext']}")
    return xyz