import asyncio
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp

app = FastAPI(title="Video Downloader API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str

async def fetch_tiktok_direct(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0, headers=headers) as client:
        # فك الرابط المختصر إن وجد
        resp = await client.get(url)
        final_url = str(resp.url)
        
        # الاستعانة بـ API مخصص لاستخراج فيديوهات تيك توك بدون علامة مائية
        api_url = f"https://tikwm.com/api/?url={final_url}"
        api_resp = await client.get(api_url)
        data = api_resp.json()
        
        if data.get("code") == 0 and "data" in data:
            v_data = data["data"]
            play_url = v_data.get("play")
            if play_url and not play_url.startswith("http"):
                play_url = "https://tikwm.com" + play_url
                
            return {
                "success": True,
                "title": v_data.get("title") or "TikTok Video",
                "thumbnail": v_data.get("cover") or "",
                "download_url": play_url,
                "url": play_url,
                "duration": v_data.get("duration", 0)
            }
    return None

@app.post("/api/extract")
async def extract_video(request: VideoRequest):
    url = request.url.strip() if request.url else ""
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    # معالجة روابط تيك توك
    if "tiktok.com" in url:
        try:
            res = await fetch_tiktok_direct(url)
            if res:
                return res
        except Exception:
            pass

    # معالجة باقي المنصات عبر yt-dlp
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            d_url = info.get('url') or (info.get('formats', [{}])[-1].get('url') if info.get('formats') else '')
            
            return {
                "success": True,
                "title": info.get('title', 'Video'),
                "thumbnail": info.get('thumbnail', ''),
                "download_url": d_url,
                "url": d_url,
                "duration": info.get('duration', 0)
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Extraction failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
