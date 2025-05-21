# ocr_utils.py
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import io

def extract_text_from_bytes(file_bytes):
    text = ""

    if file_bytes[:4] == b'%PDF':
        images = convert_from_bytes(file_bytes)
        for img in images:
            text += pytesseract.image_to_string(img) + "\n"
    else:
        image = Image.open(io.BytesIO(file_bytes))
        text = pytesseract.image_to_string(image)

    return text.strip()
