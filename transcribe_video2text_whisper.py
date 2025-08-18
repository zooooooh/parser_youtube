from model_loader import model


def transcribe_video_to_text(input_file="video.mp4", output_file="transcription.txt"):
    """
    Транскрибирует видео в текст
    Args:
        input_file: путь к видео/аудио файлу
        output_file: куда сохранить результат
    """
    try:
        segments, info = model.transcribe(input_file, language="en", beam_size=5)
        text = " ".join(segment.text for segment in segments)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"✅ Транскрипция сохранена в {output_file}")


        return text
    except Exception as e:
        print(f"❌ Ошибка транскрипции: {e}")
        return None
