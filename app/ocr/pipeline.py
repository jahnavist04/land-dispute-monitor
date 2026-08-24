import pytesseract
import logging
from typing import Optional
from PIL import Image
import io
import numpy as np
import pdf2image
from app.ocr.preprocess import preprocess_image
from app.config import Config

logger = logging.getLogger(__name__)

# Configure Tesseract path from config
pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD

def ocr_image(image_bytes: bytes) -> dict:
    """OCR a single image.
    
    Returns:
        {
            'text': str,           # Full extracted text
            'confidence': float,   # Average confidence (0-100)
            'word_confidences': list[dict]  # Per-word: {'word': str, 'confidence': float}
        }
    """
    try:
        preprocessed = preprocess_image(image_bytes)
        if preprocessed is not None:
            img = Image.fromarray(preprocessed)
        else:
            img = Image.open(io.BytesIO(image_bytes))
            
        custom_config = r'--oem 3 --psm 6'
        
        text = pytesseract.image_to_string(img, config=custom_config)
        
        data = pytesseract.image_to_data(img, config=custom_config, output_type=pytesseract.Output.DICT)
        
        word_confidences = []
        total_conf = 0
        count = 0
        
        for i in range(len(data['text'])):
            word = data['text'][i].strip()
            conf = int(data['conf'][i])
            
            if word and conf >= 0:
                word_confidences.append({'word': word, 'confidence': float(conf)})
                total_conf += conf
                count += 1
                
        avg_confidence = (total_conf / count) if count > 0 else 0.0
        
        return {
            'text': text,
            'confidence': avg_confidence,
            'word_confidences': word_confidences
        }
    except Exception as e:
        logger.error(f"Error during OCR image processing: {e}")
        return {
            'text': '',
            'confidence': 0.0,
            'word_confidences': []
        }

def ocr_pdf(pdf_bytes: bytes) -> dict:
    """OCR a PDF document (convert pages to images first).
    
    Returns:
        {
            'text': str,           # Combined text from all pages
            'confidence': float,   # Average confidence across all pages
            'page_results': list[dict]  # Per-page OCR results
        }
    """
    try:
        pages = pdf2image.convert_from_bytes(pdf_bytes)
        page_results = []
        full_text = []
        total_conf = 0.0
        
        for page in pages:
            img_byte_arr = io.BytesIO()
            page.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            res = ocr_image(img_bytes)
            page_results.append(res)
            
            if res['text']:
                full_text.append(res['text'])
            total_conf += res['confidence']
            
        avg_conf = (total_conf / len(pages)) if pages else 0.0
        
        return {
            'text': '\\n--- PAGE BREAK ---\\n'.join(full_text),
            'confidence': avg_conf,
            'page_results': page_results
        }
    except Exception as e:
        logger.error(f"Error during PDF OCR processing: {e}")
        return {
            'text': '',
            'confidence': 0.0,
            'page_results': []
        }

def compute_field_confidence(word_data: list[dict], field_text: str) -> float:
    """Compute confidence score for a specific extracted field.
    
    Match words from field_text against OCR word data to get
    the average confidence for that field's words.
    """
    if not field_text or not word_data:
        return 0.0
        
    field_words = field_text.split()
    total_conf = 0.0
    count = 0
    
    for fw in field_words:
        fw_lower = fw.lower()
        # Find highest confidence match for this word
        best_conf = 0.0
        for wd in word_data:
            if fw_lower in wd['word'].lower():
                best_conf = max(best_conf, wd['confidence'])
        
        if best_conf > 0:
            total_conf += best_conf
            count += 1
            
    return (total_conf / count) if count > 0 else 0.0
