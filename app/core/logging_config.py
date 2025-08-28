import logging
from pathlib import Path

log_path = Path(__file__).parent.parent.parent / "youtube_transcriber.log"

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Удаляем все старые хендлеры
    while logger.handlers:
        logger.handlers.pop()

    # Добавляем консоль + файл логгеры
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    stream_handler = logging.StreamHandler()

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
