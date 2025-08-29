import os
import subprocess
import tempfile
import wave
import json
from pathlib import Path


from vosk import KaldiRecognizer

from app.services.models_loader import get_whisper_model, get_vosk_model
from app.utils.pdf_generator import generate_pdf_from_textfile
from app.core.logging_config import setup_logger

logger = setup_logger(__name__)

logger.info("Модуль инициализирован")



def transcribe_file(mp3_path: str, model_name: str = "whisper-small") -> str:
    """
    Транскрибирует MP3 файл выбранной моделью.
    Также сохраняет результат в .txt и .pdf.
    После успешного создания PDF удаляет исходный mp3 и txt файл.
    """
    if model_name.startswith("whisper"):
        text = transcribe_with_whisper(mp3_path, model_name.replace("whisper-", ""))
    elif model_name == "vosk":
        text = transcribe_with_vosk(mp3_path)
    else:
        raise ValueError(f"Неизвестная модель: {model_name}")

    base_path = Path(mp3_path).with_suffix("")
    txt_path = base_path.with_suffix(".txt")
    pdf_path = base_path.with_suffix(".pdf")

    # Сохраняем транскрипт в .txt
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)
    logger.info(f"Транскрипт сохранён в: {txt_path}")

    # Создаем PDF из .txt
    pdf_created = generate_pdf_from_textfile(txt_path, pdf_path)
    if pdf_created and pdf_path.exists():
        logger.info(f"PDF успешно создан: {pdf_path}")

        # Удаляем исходный mp3 файл
        if Path(mp3_path).exists():
            try:
                os.remove(mp3_path)
                logger.info(f"Удалён исходный MP3 файл: {mp3_path}")
            except Exception as e:
                logger.warning(f"Не удалось удалить MP3 файл {mp3_path}: {e}")
        else:
            logger.debug(f"MP3 файл уже отсутствует: {mp3_path}")

        # Удаляем txt файл
        if txt_path.exists():
            try:
                os.remove(txt_path)
                logger.info(f"Удалён временный TXT файл: {txt_path}")
            except Exception as e:
                logger.warning(f"Не удалось удалить TXT файл {txt_path}: {e}")
        else:
            logger.debug(f"TXT файл уже отсутствует: {txt_path}")

    else:
        logger.warning(f"PDF не создан, файлы не удаляются: {pdf_path}")

    return text


def transcribe_with_whisper(mp3_path: str, model_size: str) -> str:
    """
    Транскрипция через faster-whisper (CPU).
    """
    model = get_whisper_model(model_size)
    segments, _ = model.transcribe(mp3_path)

    result = []
    for segment in segments:
        result.append(segment.text.strip())
    return " ".join(result)


def transcribe_with_vosk(mp3_path: str) -> str:
    """
    Транскрипция через vosk (после конвертации mp3 → wav).
    """
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        wav_path = temp_wav.name

    try:
        subprocess.run(
            [
                "ffmpeg", "-i", mp3_path,
                "-ar", "16000", "-ac", "1", "-f", "wav", wav_path,
                "-y"
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        wf = wave.open(wav_path, "rb")
        vosk_model = get_vosk_model()
        rec = KaldiRecognizer(vosk_model, wf.getframerate())

        results = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                results.append(json.loads(rec.Result())["text"])
        results.append(json.loads(rec.FinalResult())["text"])

        return " ".join(results)

    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)
            logger.debug(f"Временный WAV файл удалён: {wav_path}")
