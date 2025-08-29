from fastapi import FastAPI
from app.api.router import api_router
from app.core.logging_config import setup_logger

setup_logger(__name__)
app = FastAPI(
    title="YouTube Audio Downloader API",
    description="API для асинхронной загрузки аудио с YouTube",
    version="1.0.0"
)

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

# celery -A app.celery_app.celery worker --loglevel=info --pool=solo
# python -m app.main
