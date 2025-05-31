# ocr_utils.py
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import io
import logging

# Set Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def extract_text_from_bytes(file_bytes):
    text = ""
    logger.debug("Starting text extraction from bytes")
    
    try:
        if file_bytes[:4] == b'%PDF':
            logger.debug("Detected PDF file, converting to images")
            images = convert_from_bytes(file_bytes)
            for i, img in enumerate(images):
                logger.debug(f"Processing page {i+1}")
                text += pytesseract.image_to_string(img) + "\n"
        else:
            logger.debug("Processing as image file")
            image = Image.open(io.BytesIO(file_bytes))
            text = pytesseract.image_to_string(image)
            
        logger.debug(f"Extracted text length: {len(text)}")
        return text.strip()
    except Exception as e:
        logger.error(f"Error in text extraction: {str(e)}")
        raise
