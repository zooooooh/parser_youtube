from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class DownloadType(str, Enum):
    VIDEO = "video"
    PLAYLIST = "playlist"

class QualityLevel(int, Enum):
    LOW = 64
    MEDIUM = 128
    HIGH = 192
    VERY_HIGH = 320

class ModelName(str, Enum):
    whisper_small = "whisper-small"
    whisper_medium = "whisper-medium"
    whisper_large_2 = "whisper-large-2"
    vosk = "vosk"

class DownloadRequest(BaseModel):
    url: str = Field(..., description="YouTube URL видео или плейлиста")
    quality: QualityLevel = Field(QualityLevel.MEDIUM, description="Качество аудио")
    max_workers: int = Field(4, ge=1, le=10, description="Количество потоков для плейлистов")
    model_name: Optional[ModelName] = Field(ModelName.whisper_small, description="Модель для транскрипции")


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


