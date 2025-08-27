from fastapi import APIRouter
from app.api.downloads import router as downloads_router
from app.api.tasks import router as tasks_router

api_router = APIRouter()
api_router.include_router(downloads_router, prefix="", tags=["download"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
