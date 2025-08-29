#app\services\tasks.py
import os
from datetime import datetime

from app.celery_app import celery
from app.models import TaskStatus, DownloadType
from app.services.downloader import DownloaderService
from app.services.transcriber import transcribe_file
from app.core.config import settings
from app.core.logging_config import setup_logger
logger = setup_logger(__name__)


def get_task_dir(task_id: str) -> str:
    return os.path.join(settings.tasks_dir, task_id)


@celery.task(bind=True, name='process_download_task')
def process_download_task(self, task_id: str, url: str, quality: int, max_workers: int, model_name: str = "whisper-small"):
    logger.info(f"[{task_id}] Старт задачи загрузки. URL: {url}")
    try:
        task_dir = get_task_dir(task_id)
        os.makedirs(task_dir, exist_ok=True)
        logger.info(f"[{task_id}] Рабочая директория создана: {task_dir}")

        download_type = DownloadType.PLAYLIST if ('list=' in url or 'playlist' in url) else DownloadType.VIDEO

        self.update_state(
            state='PROCESSING',
            meta={
                'status': TaskStatus.PROCESSING,
                'download_type': download_type,
                'updated_at': datetime.now().isoformat()
            }
        )
        logger.info(f"[{task_id}] Состояние обновлено: PROCESSING")

        downloader = DownloaderService(task_dir)
        result = downloader.download_content(url, quality, max_workers, max_retries=3)

        if not result:
            raise Exception("Не удалось скачать контент")

        downloaded_files = result if isinstance(result, list) else [result]

        logger.info(f"[{task_id}] Загружено файлов: {len(downloaded_files)}")

        transcribed_files = []
        for file_path in downloaded_files:
            abs_path = os.path.abspath(file_path)
            transcription_task = transcribe_audio.delay(abs_path, model_name=model_name)
            logger.info(f"[{task_id}] Отправлена задача транскрипции: {transcription_task.id} для файла {abs_path}")
            transcribed_files.append({
                "audio_file": os.path.relpath(abs_path, task_dir),
                "transcription_task_id": transcription_task.id
            })

        logger.info(f"[{task_id}] Задача завершена успешно.")
        return {
            'status': TaskStatus.COMPLETED,
            'download_type': download_type,
            'files': [os.path.relpath(f, task_dir) for f in downloaded_files],
            'transcriptions': transcribed_files,
            'updated_at': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"[{task_id}] Ошибка при обработке задачи: {e}")
        return {
            'status': TaskStatus.FAILED,
            'error': str(e),
            'updated_at': datetime.now().isoformat()
        }



@celery.task
def transcribe_audio(mp3_path: str, model_name: str = "whisper-small"):
    try:
        logger.info(f"[Transcribe] Начало транскрипции файла: {mp3_path} (модель: {model_name})")
        text = transcribe_file(mp3_path, model_name)
        txt_path = mp3_path.replace(".mp3", ".txt")

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)

        logger.info(f"[Transcribe] Транскрипция завершена: {txt_path}")
        return txt_path

    except Exception as e:
        logger.error(f"[Transcribe] Ошибка транскрипции {mp3_path}: {e}")
        return None
