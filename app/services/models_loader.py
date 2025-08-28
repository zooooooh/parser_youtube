# app/services/models_loader.py

import os
import io
import zipfile
import requests
from functools import lru_cache
from faster_whisper import WhisperModel
from vosk import Model
from app.core.logging_config import logger


MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
MODEL_DIR = "vosk_models"


@lru_cache(maxsize=1)
def get_whisper_model(model_name: str = "small") -> WhisperModel:
    """
    Возвращает faster-whisper модель (CPU, int8).
    """
    logger.info(f"Загрузка модели Whisper: '{model_name}' (device=cpu, compute_type=int8)")
    return WhisperModel(
        model_name,
        device="cpu",
        compute_type="int8"
    )


@lru_cache(maxsize=1)
def get_vosk_model() -> Model:
    """
    Скачивает и возвращает Vosk модель.
    """
    os.makedirs(MODEL_DIR, exist_ok=True)
    model_path = os.path.join(MODEL_DIR, "vosk-model-small-en-us-0.15")

    if not os.path.exists(model_path):
        logger.info("Начато скачивание модели Vosk...")
        try:
            response = requests.get(MODEL_URL)
            response.raise_for_status()

            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                zip_ref.extractall(MODEL_DIR)

            logger.info("Модель Vosk успешно загружена и распакована.")
        except Exception as e:
            logger.exception("Ошибка при загрузке модели Vosk")
            raise RuntimeError(f"Ошибка загрузки модели: {str(e)}")

    return Model(model_path)
