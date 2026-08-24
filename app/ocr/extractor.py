import re
import logging
from typing import Optional
from datetime import datetime
from app.ocr.pipeline import compute_field_confidence

logger = logging.getLogger(__name__)

def extract_notice_fields(ocr_text: str, word_confidences: list[dict] = None, confidence_threshold: float = 70.0) -> dict:
    """Extract structured fields from OCR text.
    
    Returns:
        {
            'notice_type': str or None,
            'property_number': str or None,
            'survey_number': str or None,
            'disputing_parties': list[str],
            'location': str or None,
            'notice_date': str or None (ISO format),
            'issuing_authority': str or None,
            'confidence_scores': dict,  # per-field confidence
            'needs_manual_review': bool
        }
    """
    if word_confidences is None:
        word_confidences = []
        
    try:
        notice_type = _extract_notice_type(ocr_text)
        survey_number = _extract_survey_number(ocr_text)
        property_number = _extract_property_number(ocr_text)
        parties = _extract_parties(ocr_text)
        location = _extract_location(ocr_text)
        notice_date = _extract_date(ocr_text)
        issuing_authority = _extract_authority(ocr_text)

        confidence_scores = {
            'notice_type': compute_field_confidence(word_confidences, notice_type) if notice_type and word_confidences else 0.85,
            'survey_number': compute_field_confidence(word_confidences, survey_number) if survey_number and word_confidences else 0.85,
            'property_number': compute_field_confidence(word_confidences, property_number) if property_number and word_confidences else 0.85,
            'parties': sum(compute_field_confidence(word_confidences, p) for p in parties) / len(parties) if parties and word_confidences else 0.85,
            'location': compute_field_confidence(word_confidences, location) if location and word_confidences else 0.85,
            'notice_date': compute_field_confidence(word_confidences, notice_date) if notice_date and word_confidences else 0.85,
            'issuing_authority': compute_field_confidence(word_confidences, issuing_authority) if issuing_authority and word_confidences else 0.85
        }

        needs_manual_review = False
        if word_confidences:
            key_fields = ['notice_type', 'survey_number', 'parties', 'location']
            for field in key_fields:
                if confidence_scores.get(field, 0.0) < confidence_threshold:
                    needs_manual_review = True
                    break

        return {
            'notice_type': notice_type,
            'property_number': property_number,
            'survey_number': survey_number,
            'disputing_parties': parties,
            'location': location,
            'notice_date': notice_date,
            'issuing_authority': issuing_authority,
            'confidence_scores': confidence_scores,
            'needs_manual_review': needs_manual_review
        }
    except Exception as e:
        logger.error(f"Error extracting notice fields: {e}")
        return {
            'notice_type': None,
            'property_number': None,
            'survey_number': None,
            'disputing_parties': [],
            'location': None,
            'notice_date': None,
            'issuing_authority': None,
            'confidence_scores': {},
            'needs_manual_review': True
        }

def _extract_notice_type(text: str) -> Optional[str]:
    """Identify notice type from keywords."""
    patterns = [
        (r'sale notice', 'sale'),
        (r'dispute notice|land dispute|dispute', 'dispute'),
        (r'mortgage notice', 'mortgage'),
        (r'partition notice', 'partition'),
        (r'court order', 'court_order'),
        (r'public notice', 'public_notice'),
        (r'legal notice', 'legal_notice')
    ]
    for pattern, name in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return name
    return None

def _extract_survey_number(text: str) -> Optional[str]:
    """Extract survey/property number."""
    patterns = [
        r'survey\s*no\.?\s*([0-9a-zA-Z/-]+)',
        r'sy\.?\s*no\.?\s*([0-9a-zA-Z/-]+)',
        r's\.no\.?\s*([0-9a-zA-Z/-]+)',
        r'khasra\s*no\.?\s*([0-9a-zA-Z/-]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def _extract_property_number(text: str) -> Optional[str]:
    """Extract property/khata number."""
    patterns = [
        r'property\s*no\.?\s*([0-9a-zA-Z/-]+)',
        r'khata\s*no\.?\s*([0-9a-zA-Z/-]+)',
        r'plot\s*no\.?\s*([0-9a-zA-Z/-]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def _extract_parties(text: str) -> list[str]:
    """Extract disputing party names."""
    parties = []
    
    # Pattern: X vs/versus Y
    vs_match = re.search(r'([A-Za-z\s\.]+)\s+(?:vs|versus)\.?\s+([A-Za-z\s\.]+)', text, re.IGNORECASE)
    if vs_match:
        parties.extend([vs_match.group(1).strip(), vs_match.group(2).strip()])
        
    # Pattern: between X and Y
    between_match = re.search(r'between\s+([A-Za-z\s\.]+)\s+and\s+([A-Za-z\s\.]+)', text, re.IGNORECASE)
    if between_match:
        parties.extend([between_match.group(1).strip(), between_match.group(2).strip()])
        
    # Pattern: Sri/Smt/Mr/Mrs/Ms NAME s/o|d/o|w/o PARENT_NAME
    indian_names = re.findall(r'(?:sri|smt|mr|mrs|ms)\.?\s+([A-Za-z\s\.]+)\s+(?:s/o|d/o|w/o)\s+([A-Za-z\s\.]+)', text, re.IGNORECASE)
    for name, parent in indian_names:
        parties.append(f"{name.strip()} ({parent.strip()})")
        
    return list(set(parties))

def _extract_location(text: str) -> Optional[str]:
    """Extract location/address."""
    patterns = [
        r'situated at\s+([^,]+(?:,\s*[^,]+)*)',
        r'located at\s+([^,]+(?:,\s*[^,]+)*)',
        r'village\s+([A-Za-z\s]+)',
        r'taluk\s+([A-Za-z\s]+)',
        r'district\s+([A-Za-z\s]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None

def _extract_date(text: str) -> Optional[str]:
    """Extract notice date."""
    patterns = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\,?\s+\d{4})'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None

def _extract_authority(text: str) -> Optional[str]:
    """Extract issuing authority."""
    patterns = [
        r'(sub-registrar)', r'(district court)', r'(civil court)',
        r'(revenue department)', r'(tahsildar)', r'(bda)', r'(bbmp)'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).title()
    return None
