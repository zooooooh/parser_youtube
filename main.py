import hashlib
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import os

# Импортируем ваши функции
from download_video import download_low_quality_fast
from transcribe_video2text_vosk import transcribe_media_to_text
from get_all_links import get_all_playlist_videos
from get_pdf_file import get_pdf

app = FastAPI(title="YouTube Playlist Processor")

# Константы
RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)  # Создаем папку если не существует


class PlaylistRequest(BaseModel):
    playlist_url: str


@app.post("/process_playlist/")
async def process_playlist(request: Request, playlist_request: PlaylistRequest):
    """Обработка YouTube плейлиста с возвратом всех ссылок для скачивания"""
    try:
        playlist_url = playlist_request.playlist_url
        links = get_all_playlist_videos(playlist_url)

        if not links:
            raise HTTPException(status_code=404, detail="No videos found in playlist")

        # Создаем уникальное имя папки для плейлиста
        playlist_hash = hashlib.md5(playlist_url.encode()).hexdigest()[:8]
        playlist_dir = os.path.join(RESULTS_DIR, f"playlist_{playlist_hash}")
        os.makedirs(playlist_dir, exist_ok=True)

        base_url = str(request.base_url)
        download_links = []
        current_date = datetime.now().strftime("%Y-%m-%d")

        for i, (url, title, duration) in enumerate(links):
            # Обработка видео
            download_low_quality_fast(url)
            transcribe_media_to_text("video.mp4", "transcription.txt")

            # Создаем PDF с именем по дате и позиции
            pdf_filename = f"{current_date}_pos{i+1}.pdf"
            pdf_path = os.path.join(playlist_dir, pdf_filename)
            get_pdf(pdf_path)

            # Добавляем ссылку для скачивания
            download_links.append(f"{base_url}download/playlist_{playlist_hash}/{pdf_filename}")

            # Очистка временных файлов
            for file in ["video.mp4", "transcription.txt"]:
                if os.path.exists(file):
                    os.remove(file)

        return JSONResponse({
            "status": "success",
            "download_links": download_links,
            "message": "All PDF files are ready for download"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download_file/{filename}")
async def download_file(filename: str):
    """Сервисный эндпоинт для непосредственной отдачи файла"""
    file_path = os.path.join(RESULTS_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        file_path,
        media_type='application/pdf',
        filename=filename
    )

@app.get("/download/{playlist_hash}/{filename}")
async def download_file(playlist_hash: str, filename: str):
    """Сервисный эндпоинт для непосредственной отдачи файла"""
    file_path = os.path.join(RESULTS_DIR, f"playlist_{playlist_hash}", filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        file_path,
        media_type='application/pdf',
        filename=filename
    )
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)