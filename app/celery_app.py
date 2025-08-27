from celery import Celery
from app.core.config import settings

celery = Celery(
    'youtube_downloader',
    broker=settings.redis_broker_url,
    backend=settings.redis_backend_url,
    include=['app.services.tasks']
)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
)
