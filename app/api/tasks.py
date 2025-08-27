from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.models import TaskResponse, TaskStatus
from celery.result import AsyncResult
from datetime import datetime
from app.storage import get_task_dir
import os
from app.celery_app import celery  # <--- импортируем celery

router = APIRouter()

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    try:
        result = AsyncResult(task_id, app=celery)

        date_submitted = getattr(result, 'date_submitted', None)
        created_at = date_submitted.isoformat() if date_submitted else datetime.now().isoformat()

        if not result.ready():
            return {
                "task_id": task_id,
                "status": TaskStatus.PROCESSING,
                "created_at": created_at,
                "updated_at": datetime.now().isoformat()
            }

        if result.successful():
            result_data = result.result
            return {
                "task_id": task_id,
                "status": TaskStatus.COMPLETED,
                "download_type": result_data.get('download_type'),
                "files": result_data.get('files'),
                "created_at": created_at,
                "updated_at": result_data.get('updated_at', datetime.now().isoformat())
            }
        else:
            return {
                "task_id": task_id,
                "status": TaskStatus.FAILED,
                "error": str(result.result) if hasattr(result, 'result') else "Unknown error",
                "created_at": created_at,
                "updated_at": datetime.now().isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Task not found or error: {str(e)}")


@router.get("/{task_id}/files")
async def list_task_files(task_id: str):
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

@router.get("/download/{task_id}/files/{filename}")
async def download_file(task_id: str, filename: str):
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
