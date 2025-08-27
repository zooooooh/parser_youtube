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
