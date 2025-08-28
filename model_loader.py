
from faster_whisper import WhisperModel

from functools import lru_cache

@lru_cache(maxsize=1)
def get_whisper_model(model_name: str = "large-v2") -> WhisperModel:
    """Возвращает модель Whisper с кэшированием."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    return WhisperModel(model_name, device=device, compute_type=compute_type)

# Использование:
model = get_whisper_model()  # Будет загружена только при первом вызове


@lru_cache(maxsize=1)
def get_whisper_model(model_name: str = "medium") -> WhisperModel:
    """Возвращает модель Whisper с кэшированием (оптимизировано для CPU)."""
    return WhisperModel(
        model_name,
        device="cpu",       # Принудительно используем CPU
        compute_type="int8" # Оптимальный тип для CPU
    )

# Использование (теперь всегда будет CPU-версия):
model = get_whisper_model()

@lru_cache(maxsize=1)
def get_whisper_model(model_name: str = "small") -> WhisperModel:
    """Возвращает модель Whisper с кэшированием (оптимизировано для CPU)."""
    return WhisperModel(
        model_name,
        device="cpu",       # Принудительно используем CPU
        compute_type="int8" # Оптимальный тип для CPU
    )

# Использование (теперь всегда будет CPU-версия):
model = get_whisper_model()


from vosk import Model
from functools import lru_cache
import os
import requests
import zipfile
import io

MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
MODEL_DIR = "vosk_models"


@lru_cache(maxsize=1)
def get_vosk_model():
    """Автоматически скачивает и загружает модель Vosk"""
    os.makedirs(MODEL_DIR, exist_ok=True)
    model_path = os.path.join(MODEL_DIR, "vosk-model-small-en-us-0.15")

    if not os.path.exists(model_path):
        print("⏳ Скачивание модели Vosk...")
        try:
            response = requests.get(MODEL_URL)
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                zip_ref.extractall(MODEL_DIR)
            print("✅ Модель успешно загружена")
        except Exception as e:
            raise RuntimeError(f"Ошибка загрузки модели: {str(e)}")

    return Model(model_path)


model = get_vosk_model()