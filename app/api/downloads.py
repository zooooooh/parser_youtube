from fastapi import APIRouter, HTTPException, status
from app.models import DownloadRequest, TaskResponse, TaskStatus
from app.services.tasks import process_download_task
from datetime import datetime
import uuid

router = APIRouter()

@router.post("/download", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_download_task(request: DownloadRequest):
    try:
        task_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        celery_task = process_download_task.apply_async(
            args=[task_id, request.url, request.quality.value, request.max_workers, request.model_name.value if request.model_name else "whisper-small"],
            task_id=task_id
        )

        return {
            "task_id": task_id,
            "status": TaskStatus.PENDING,
            "created_at": created_at,
            "updated_at": created_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")
