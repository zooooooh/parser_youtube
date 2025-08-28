# app/utils/pdf_generator.py


from pathlib import Path
from fpdf import FPDF

from app.core.logging_config import logger


def generate_pdf_from_textfile(text_file_path: str | Path, output_pdf_path: str | Path) -> bool:
    """
    Создает PDF из указанного текстового файла и сохраняет его по указанному пути.
    """
    try:
        text_file_path = Path(text_file_path)
        output_pdf_path = Path(output_pdf_path)

        # Убедимся, что директория существует
        output_pdf_path.parent.mkdir(parents=True, exist_ok=True)

        # Читаем содержимое текстового файла
        with open(text_file_path, "r", encoding="utf-8") as file:
            text = file.read()

        # Генерируем PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=text)
        pdf.output(str(output_pdf_path))

        logger.info(f"PDF создан: {output_pdf_path}")
        return True

    except Exception as e:
        logger.exception(f"Ошибка при создании PDF из {text_file_path}")
        return False
