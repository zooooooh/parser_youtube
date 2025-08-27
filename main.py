import hashlib
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from enum import Enum
from celery import Celery
from celery.result import AsyncResult

from download_video import YouTubeAudioDownloader

# Инициализация Celery
celery = Celery(
    'youtube_downloader',
    broker='redis://localhost:6379/0',  # или 'amqp://guest:guest@localhost:5672//'
    backend='redis://localhost:6379/0',
    include=['main']  # важно для автообнаружения задач
)

# Конфигурация Celery
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour timeout
)

app = FastAPI(
    title="YouTube Audio Downloader API",
    description="API для асинхронной загрузки аудио с YouTube",
    version="1.0.0"
)

# Константы
DOWNLOADS_DIR = "downloads"
TASKS_DIR = "tasks"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(TASKS_DIR, exist_ok=True)


class DownloadType(str, Enum):
    VIDEO = "video"
    PLAYLIST = "playlist"


class QualityLevel(int, Enum):
    LOW = 64
    MEDIUM = 128
    HIGH = 192
    VERY_HIGH = 320


class DownloadRequest(BaseModel):
    url: str = Field(..., description="YouTube URL видео или плейлиста")
    quality: QualityLevel = Field(QualityLevel.MEDIUM, description="Качество аудио")
    max_workers: int = Field(4, ge=1, le=10, description="Количество потоков для плейлистов")


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    download_type: Optional[DownloadType] = None
    files: Optional[List[str]] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str


def get_task_dir(task_id: str) -> str:
    """Получить директорию для задачи"""
    return os.path.join(TASKS_DIR, task_id)


@celery.task(bind=True, name='process_download_task')
def process_download_task(self, task_id: str, url: str, quality: int, max_workers: int):
    """Celery задача для обработки загрузки"""
    try:
        task_dir = get_task_dir(task_id)
        os.makedirs(task_dir, exist_ok=True)

        # Обновляем статус задачи в Redis через Celery
        self.update_state(
            state='PROCESSING',
            meta={
                'status': TaskStatus.PROCESSING,
                'download_type': DownloadType.PLAYLIST if ('list=' in url or 'playlist' in url) else DownloadType.VIDEO,
                'updated_at': datetime.now().isoformat()
            }
        )

        # Загружаем контент
        downloader = YouTubeAudioDownloader(task_dir)
        result = downloader.download_content(url, quality, max_workers, max_retries=3)

        if not result:
            raise Exception("Failed to download content")

        # Сохраняем результаты
        if isinstance(result, list):
            files = [str(file.relative_to(task_dir)) for file in result]
        else:
            files = [str(result.relative_to(task_dir))]

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


@app.post("/download", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_download_task(request: DownloadRequest):
    """Создать задачу на загрузку YouTube аудио"""
    try:
        # Генерируем ID задачи
        task_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        # Запускаем Celery задачу
        celery_task = process_download_task.apply_async(
            args=[task_id, request.url, request.quality.value, request.max_workers],
            task_id=task_id  # Используем тот же ID для удобства
        )

        return {
            "task_id": task_id,
            "status": TaskStatus.PENDING,
            "created_at": created_at,
            "updated_at": created_at
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """Получить статус задачи"""
    try:
        # Получаем результат из Celery
        result = AsyncResult(task_id, app=celery)

        if not result.ready():
            # Задача еще выполняется
            return {
                "task_id": task_id,
                "status": TaskStatus.PROCESSING,
                "created_at": result.date_submitted.isoformat() if result.date_submitted else datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

        if result.successful():
            # Задача успешно завершена
            result_data = result.result
            return {
                "task_id": task_id,
                "status": TaskStatus.COMPLETED,
                "download_type": result_data.get('download_type'),
                "files": result_data.get('files'),
                "created_at": result.date_submitted.isoformat() if result.date_submitted else datetime.now().isoformat(),
                "updated_at": result_data.get('updated_at', datetime.now().isoformat())
            }
        else:
            # Задача завершилась с ошибкой
            return {
                "task_id": task_id,
                "status": TaskStatus.FAILED,
                "error": str(result.result) if hasattr(result, 'result') else "Unknown error",
                "created_at": result.date_submitted.isoformat() if result.date_submitted else datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Task not found or error: {str(e)}")


@app.get("/tasks/{task_id}/files")
async def list_task_files(task_id: str):
    """Получить список файлов задачи"""
    result = AsyncResult(task_id, app=celery)

    if not result.ready() or not result.successful():
        raise HTTPException(status_code=400, detail="Task not completed yet")

    result_data = result.result
    if 'files' not in result_data:
        raise HTTPException(status_code=404, detail="No files found")

    task_dir = get_task_dir(task_id)
    files = []

    for file_name in result_data['files']:
        file_path = os.path.join(task_dir, file_name)
        if os.path.exists(file_path):
            files.append({
                "name": file_name,
                "size": os.path.getsize(file_path),
                "download_url": f"/download/{task_id}/files/{file_name}"
            })

    return {"files": files}


@app.get("/download/{task_id}/files/{filename}")
async def download_file(task_id: str, filename: str):
    """Скачать файл из задачи"""
    result = AsyncResult(task_id, app=celery)

    if not result.ready() or not result.successful():
        raise HTTPException(status_code=400, detail="Task not completed yet")

    file_path = os.path.join(get_task_dir(task_id), filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        file_path,
        media_type="audio/mpeg",
        filename=filename
    )


@app.get("/tasks")
async def list_tasks(limit: int = 10, offset: int = 0):
    """Получить список всех задач (упрощенная версия для Celery)"""
    # В production нужно использовать Redis для хранения метаданных задач
    return {
        "tasks": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
        "message": "Use specific task endpoint for Celery tasks"
    }


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str):
    """Удалить задачу и файлы"""
    try:
        # Revoke Celery task
        celery.control.revoke(task_id, terminate=True)

        # Удаляем файлы задачи
        task_dir = get_task_dir(task_id)
        if os.path.exists(task_dir):
            import shutil
            shutil.rmtree(task_dir)

        return None

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Task not found: {str(e)}")


# Команды для запуска:
# 1. Запустить Redis: redis-server
# 2. Запустить Celery worker: celery -A main.celery worker --loglevel=info
# 3. Запустить FastAPI: uvicorn main:app --reload

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)