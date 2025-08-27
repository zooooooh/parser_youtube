from app.celery_app import celery
from app.models import TaskStatus, DownloadType
from app.services.downloader import DownloaderService
from app.core.config import settings
from datetime import datetime
import os

def get_task_dir(task_id: str) -> str:
    return os.path.join(settings.tasks_dir, task_id)

@celery.task(bind=True, name='process_download_task')
def process_download_task(self, task_id: str, url: str, quality: int, max_workers: int):
    try:
        task_dir = get_task_dir(task_id)
        os.makedirs(task_dir, exist_ok=True)

        self.update_state(
            state='PROCESSING',
            meta={
                'status': TaskStatus.PROCESSING,
                'download_type': DownloadType.PLAYLIST if ('list=' in url or 'playlist' in url) else DownloadType.VIDEO,
                'updated_at': datetime.now().isoformat()
            }
        )

        downloader = DownloaderService(task_dir)
        result = downloader.download_content(url, quality, max_workers, max_retries=3)

        if not result:
            raise Exception("Failed to download content")

        if isinstance(result, list):
            files = [str(os.path.relpath(file, task_dir)) for file in result]
        else:
            files = [str(os.path.relpath(result, task_dir))]

        return {
            'status': TaskStatus.COMPLETED,
            'download_type': DownloadType.PLAYLIST if ('list=' in url or 'playlist' in url) else DownloadType.VIDEO,
            'files': files,
            'updated_at': datetime.now().isoformat()
        }

    except Exception as e:
        return {
            'status': TaskStatus.FAILED,
            'error': str(e),
            'updated_at': datetime.now().isoformat()
        }
