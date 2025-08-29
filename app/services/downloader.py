#app\services\downloader.py
from app.services.downloader_engine import YouTubeAudioDownloader  # твой импорт

class DownloaderService:
    def __init__(self, task_dir: str):
        self.task_dir = task_dir
        self.downloader = YouTubeAudioDownloader(task_dir)

    def download_content(self, url: str, quality: int, max_workers: int, max_retries=3):
        return self.downloader.download_content(url, quality, max_workers, max_retries)
