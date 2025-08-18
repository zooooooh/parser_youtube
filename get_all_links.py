import yt_dlp
from typing import List, Tuple, Optional

def get_all_playlist_videos(playlist_url: str, max_videos: int = 100) -> List[Tuple[str, str, int]]:
    ydl_opts = {
        'extract_flat': True,  # Не скачивает видео, только метаданные
        'quiet': True,  # Убирает лишние сообщения
        'no_warnings': True,  # Игнорирует предупреждения
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)

            if 'entries' not in info:
                return []

            return [
                (
                    f"https://youtube.com/watch?v={video['id']}",
                    video.get('title', 'Без названия'),
                    video.get('duration', 0)
                )
                for video in info['entries']
            ]

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []