from model_loader import model
from vosk import KaldiRecognizer
import wave
import json
import subprocess
import os
from pathlib import Path


def convert_to_wav(input_file: str) -> str:
    """Конвертирует медиафайл в WAV 16kHz mono"""
    output_file = "temp_audio.wav"
    cmd = [
        "ffmpeg",
        "-i", input_file,
        "-ar", "16000",
        "-ac", "1",
        "-acodec", "pcm_s16le",
        "-y",
        output_file
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_file
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Ошибка конвертации: {e.stderr.decode()}")


def transcribe_media_to_text(input_file: str, output_file: str = "transcription.txt") -> bool:
    """Основная функция транскрипции"""
    temp_wav = None
    try:
        # Создаем папку для результата, если её нет
        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

        temp_wav = convert_to_wav(input_file)

        with wave.open(temp_wav, "rb") as wf:
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
                raise ValueError("Аудио должно быть моно, 16-bit PCM")

            rec = KaldiRecognizer(model, wf.getframerate())
            results = []

            while True:
                data = wf.readframes(4000)
                if not data:
                    break
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    if "text" in result:
                        results.append(result["text"])

            final_result = json.loads(rec.FinalResult())
            if "text" in final_result:
                results.append(final_result["text"])

            full_text = " ".join(filter(None, results))

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full_text)

        print(f"✅ Транскрипция сохранена в {output_file}")
        return True

    except Exception as e:
        print(f"❌ Ошибка транскрипции: {str(e)}")
        return False

    finally:
        if temp_wav and os.path.exists(temp_wav):
            try:
                os.unlink(temp_wav)
            except:
                pass