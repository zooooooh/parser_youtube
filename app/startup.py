# app/startup.py
from app.core.config import settings
from app.core.logging_config import setup_logger
from app.services.models_loader import get_whisper_model, get_vosk_model

logger = setup_logger(__name__)

VALID_MODELS = {"whisper-small", "whisper-medium", "whisper-large-2", "vosk"}

def preload_models():
    if not settings.models_preload:
        logger.info("Предзагрузка моделей отключена")
        return

    logger.info("Начата предзагрузка моделей...")

    for model_name in settings.preload_models:
        if model_name not in VALID_MODELS:
            logger.warning(f"Модель '{model_name}' не поддерживается и будет пропущена")
            continue

        try:
            if model_name.startswith("whisper"):
                get_whisper_model(model_name.replace("whisper-", ""))
                logger.info(f"Whisper-модель '{model_name}' успешно загружена")
            elif model_name == "vosk":
                get_vosk_model()
                logger.info("Vosk-модель успешно загружена")
        except Exception as e:
            logger.exception(f"Ошибка при загрузке модели '{model_name}': {e}")

    logger.info("Предзагрузка моделей завершена")
