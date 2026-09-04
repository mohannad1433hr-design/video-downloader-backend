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

async def get_tiktok_video(url: str):
    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        # استخدام API خارجي مخصص لتيك توك يتجاوز الحظر
        api_url = f"https://tikwm.com/api/?url={url}"
        response = await client.get(api_url)
        data = response.json()
        if data.get("code") == 0 and "data" in data:
            video_data = data["data"]
            return {
                "success": True,
                "title": video_data.get("title", "TikTok Video"),
                "thumbnail": video_data.get("cover", ""),
                "download_url": video_data.get("play", ""),
                "duration": video_data.get("duration", 0)
            }
    return None

@app.post("/api/extract")
async def extract_video(request: VideoRequest):
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    # إذا كان الرابط من تيك توك يتم معالجته بواسطة API المخصص
    if "tiktok.com" in url:
        try:
            result = await get_tiktok_video(url)
            if result:
                return result
        except Exception:
            pass

    # للمنصات الأخرى (YouTube, Instagram, X) يتم استخدام yt-dlp
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
            download_url = info.get('url') or (info.get('formats', [{}])[-1].get('url') if info.get('formats') else '')
            return {
                "success": True,
                "title": info.get('title', 'Video'),
                "thumbnail": info.get('thumbnail', ''),
                "download_url": download_url,
                "duration": info.get('duration', 0)
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract video: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            
            # Extract highest quality direct video URL
            download_url = info.get('url') or (info.get('formats', [{}])[-1].get('url') if info.get('formats') else '')
            
            return {
                "success": True,
                "title": info.get('title', 'Video'),
                "thumbnail": info.get('thumbnail', ''),
                "download_url": download_url,
                "duration": info.get('duration', 0)
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
