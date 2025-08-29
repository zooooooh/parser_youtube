# app/core/config.py
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    redis_broker_url: str = "redis://localhost:6379/0"
    redis_backend_url: str = "redis://localhost:6379/0"
    tasks_dir: str = "tasks"
    downloads_dir: str = "downloads"

    # Новые параметры:
    models_preload: bool = True
    preload_models: List[str] = ["whisper-small", "vosk"]

    class Config:
        env_file = ".env"


settings = Settings()
