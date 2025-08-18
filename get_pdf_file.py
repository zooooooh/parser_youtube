from fpdf import FPDF
import os
from pathlib import Path

def get_pdf(output_path: str | Path, video_title: str = "") -> bool:
    """Создает PDF из transcription.txt и сохраняет по указанному пути"""
    try:
        # Создаем папку, если её нет
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Настройки PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Чтение текстового файла
        with open("transcription.txt", "r", encoding="utf-8") as file:
            text = file.read()

        # Запись текста в PDF
        pdf.multi_cell(0, 10, txt=text)

        # Сохраняем PDF
        pdf.output(output_path)
        print(f"✅ PDF успешно сохранён как: {output_path}")
        return True

    except Exception as e:
        print(f"❌ Ошибка при сохранении PDF: {e}")
        return False