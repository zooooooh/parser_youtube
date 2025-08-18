import yt_dlp
import os
import time


def download_low_quality_fast(url, max_retries=3, retry_delay=5):
    """
    Скачивает видео с YouTube в низком качестве
    с автоматическими повторными попытками при ошибках

    Args:
        url (str): Ссылка на YouTube видео
        max_retries (int): Максимальное количество попыток
        retry_delay (int): Задержка между попытками (в секундах)

    Returns:
        bool: True если скачивание успешно, False при ошибке
    """
    ydl_opts = {
        'format': 'worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst',
        'outtmpl': 'video.mp4',
        'quiet': True,
        'nooverwrites': True,  # Не перезаписывать существующий файл
        'continuedl': False,  # Отключить возобновление загрузки
        'retries': 0,  # Отключаем встроенные повторы (реализуем свои)
    }

    for attempt in range(1, max_retries + 1):
        try:
            # Удаляем предыдущую неудачную попытку
            if os.path.exists('video.mp4'):
                os.remove('video.mp4')
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Проверяем, что файл действительно скачался
            if os.path.exists('video.mp4') and os.path.getsize('video.mp4') > 0:
                print("✅ Видео успешно скачано")
                return True
            else:
                raise Exception("Файл не был создан или пустой")

        except Exception as e:
            print(f"❌ Ошибка при попытке {attempt}: {str(e)}")
            if attempt < max_retries:
                time.sleep(retry_delay)
            continue

    print(f"🚫 Не удалось скачать видео после {max_retries} попыток")
    return False