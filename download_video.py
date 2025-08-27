import yt_dlp
import os
import time
import logging
from typing import Optional, List, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_transcriber.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class YouTubeAudioDownloader:
    def __init__(self, output_dir: str = "downloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def _setup_ydl_opts(self, output_template: str, quality: int = 64) -> dict:
        """Настройка опций для yt-dlp"""
        return {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'quiet': False,
            'no_warnings': False,
            'nooverwrites': False,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': str(quality),
            }],
            'retries': 3,
            'fragment_retries': 3,
            'skip_unavailable_fragments': True,
            'socket_timeout': 30,
            'extract_flat': False,
            'concurrent_fragment_downloads': 4,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            },
        }

    def download_audio(
            self,
            url: str,
            output_filename: Optional[str] = None,
            quality: int = 64,
            max_retries: int = 3,
            retry_delay: int = 5
    ) -> Optional[Path]:
        """
        Скачивает аудио с YouTube

        Args:
            url: Ссылка на YouTube видео
            output_filename: Имя выходного файла
            quality: Качество аудио (0-320)
            max_retries: Максимальное количество попыток
            retry_delay: Задержка между попытками

        Returns:
            Path к скачанному файлу или None при ошибке
        """
        if output_filename:
            output_path = self.output_dir / output_filename
        else:
            output_path = self.output_dir / "audio.%(ext)s"

        ydl_opts = self._setup_ydl_opts(str(output_path), quality)

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Попытка {attempt}/{max_retries} скачивания: {url}")

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)

                # Поиск фактического имени файла
                actual_path = self._find_audio_file(output_path)
                if actual_path and actual_path.exists() and actual_path.stat().st_size > 0:
                    logger.info(f"Аудио успешно скачано: {actual_path}")
                    return actual_path

                raise Exception("Файл не был создан или пустой")

            except Exception as e:
                logger.error(f"Ошибка при попытке {attempt}: {str(e)}")
                if attempt < max_retries:
                    logger.info(f"Повторная попытка через {retry_delay} секунд...")
                    time.sleep(retry_delay)
                continue

        logger.error(f"Не удалось скачать аудио после {max_retries} попыток")
        return None

    def _find_audio_file(self, base_path: Path) -> Optional[Path]:
        """Поиск фактического аудио файла"""
        for ext in ['mp3', 'm4a', 'webm']:
            candidate = base_path.parent / f"{base_path.stem}.{ext}"
            if candidate.exists():
                return candidate
        return None

    def download_playlist(
            self,
            playlist_url: str,
            max_workers: int = 4,
            quality: int = 64
    ) -> List[Path]:
        """
        Асинхронная загрузка плейлиста

        Args:
            playlist_url: Ссылка на плейлист
            max_workers: Количество параллельных загрузок
            quality: Качество аудио

        Returns:
            Список путей к скачанным файлам
        """
        try:
            # Получаем информацию о плейлисте
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                playlist_info = ydl.extract_info(playlist_url, download=False)

            if not playlist_info or 'entries' not in playlist_info:
                logger.error("Не удалось получить информацию о плейлисте")
                return []

            video_urls = [
                entry['url'] for entry in playlist_info['entries']
                if entry and 'url' in entry
            ]

            logger.info(f"Найдено {len(video_urls)} видео в плейлисте")

            results = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Создаем задачи для каждого видео
                future_to_url = {
                    executor.submit(
                        self.download_audio,
                        url,
                        f"video_{i}_{time.time()}.%(ext)s",
                        quality,
                        2,  # Меньше попыток для плейлиста
                        3  # Меньшая задержка
                    ): url for i, url in enumerate(video_urls)
                }

                # Обрабатываем результаты по мере завершения
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                            logger.info(f"Завершено: {url}")
                    except Exception as e:
                        logger.error(f"Ошибка при загрузке {url}: {e}")

            return results

        except Exception as e:
            logger.error(f"Ошибка при обработке плейлиста: {e}")
            return []

    def download_content(
            self,
            url: str,
            quality: int = 64,
            max_workers: int = 4,
            max_retries: int = 3
    ) -> Union[Path, List[Path], None]:
        """
        Универсальный метод для скачивания видео или плейлиста

        Args:
            url: Ссылка на YouTube видео или плейлист
            quality: Качество аудио
            max_workers: Количество потоков для плейлистов
            max_retries: Максимальное количество попыток

        Returns:
            Для видео: Path к файлу
            Для плейлиста: List[Path] файлов
            При ошибке: None
        """
        if 'list=' in url or 'playlist' in url:
            logger.info(f"Обнаружен плейлист: {url}")
            return self.download_playlist(url, max_workers, quality)
        else:
            logger.info(f"Обнаружено отдельное видео: {url}")
            return self.download_audio(url, quality=quality, max_retries=max_retries)


# Функция для удобного использования модуля
def download_youtube_audio(
        url: str,
        output_dir: str = "downloads",
        quality: int = 64,
        max_workers: int = 4,
        max_retries: int = 3
) -> Union[Path, List[Path], None]:
    """
    Основная функция модуля для скачивания YouTube аудио

    Args:
        url: Ссылка на YouTube видео или плейлист
        output_dir: Директория для сохранения
        quality: Качество аудио (0-320)
        max_workers: Количество потоков для плейлистов
        max_retries: Максимальное количество попыток

    Returns:
        Для видео: Path к файлу
        Для плейлиста: List[Path] файлов
        При ошибке: None
    """
    downloader = YouTubeAudioDownloader(output_dir)
    return downloader.download_content(url, quality, max_workers, max_retries)


# Пример использования модуля


# Для отдельного видео
# audio_file = download_youtube_audio("https://www.youtube.com/watch?v=lO2A4g9tMJU&list=PLOGi5-fAu8bFiBX6StfdJytadWTDo3b_j")
# print(f"Скачано: {audio_file}")
