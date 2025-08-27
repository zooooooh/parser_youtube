import os
import shutil
from app.core.config import settings

def get_task_dir(task_id: str) -> str:
    return os.path.join(settings.tasks_dir, task_id)

def create_dirs():
    os.makedirs(settings.tasks_dir, exist_ok=True)
    os.makedirs(settings.downloads_dir, exist_ok=True)

def delete_task_files(task_id: str):
    task_dir = get_task_dir(task_id)
    if os.path.exists(task_dir):
        shutil.rmtree(task_dir)
