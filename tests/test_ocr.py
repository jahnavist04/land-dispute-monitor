import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from app.ocr.preprocess import preprocess_image, _to_grayscale, _deskew
from app.ocr.pipeline import ocr_image
from app.ocr.extractor import (
    extract_notice_fields, _extract_notice_type, _extract_survey_number,
    _extract_parties, _extract_location, _extract_authority
)

class TestPreprocess:
    def test_grayscale_conversion(self):
        """Test that color image is converted to grayscale."""
        # Create a simple 100x100 color image
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        result = _to_grayscale(img)
        assert len(result.shape) == 2  # grayscale has no channel dimension
    
    def test_preprocess_returns_none_on_invalid_input(self):
        assert preprocess_image(None) is None

class TestExtractor:
    def test_extract_notice_type_sale(self):
        text = 'This is a sale notice for the property situated at...'
        result = _extract_notice_type(text)
        assert result == 'sale'
    
    def test_extract_notice_type_dispute(self):
        text = 'Public notice regarding land dispute between parties...'
        result = _extract_notice_type(text)
        assert 'dispute' in result.lower()
    
    def test_extract_survey_number(self):
        text = 'Property bearing Survey No. 123/4 situated at Village XYZ'
        result = _extract_survey_number(text)
        assert '123/4' in result
    
    def test_extract_survey_number_sy_format(self):
        text = 'Land in Sy. No. 45/2A of Hobli ABC'
        result = _extract_survey_number(text)
        assert '45/2' in result
    
    def test_extract_parties_vs_pattern(self):
        text = 'In the matter of Sri Ramesh Kumar vs Smt Lakshmi Devi'
        result = _extract_parties(text)
        assert len(result) >= 2
    
    def test_extract_location_village(self):
        text = 'Property situated at Village Yelahanka, Taluk Bangalore North, District Bangalore Urban'
        result = _extract_location(text)
        assert 'Yelahanka' in result or 'Bangalore' in result
    
    def test_extract_authority_court(self):
        text = 'By order of the District Court, Bangalore Urban'
        result = _extract_authority(text)
        assert 'District Court' in result
    
    def test_extract_authority_registrar(self):
        text = 'Issued by the Sub-Registrar, Jayanagar'
        result = _extract_authority(text)
        assert 'Sub-Registrar' in result
    
    def test_full_extraction(self):
        """Test full extraction pipeline with realistic notice text."""
        text = """PUBLIC NOTICE
        This is to notify that Sri Mahesh Kumar S/o Late Ramaiah has filed 
        an objection regarding the sale of property bearing Survey No. 234/5 
        situated at Village Kengeri, Taluk Bangalore South, District Bangalore Urban.
        The matter is pending before the Sub-Registrar, Kengeri.
        Interested parties may file objections within 15 days from 01/03/2024.
        """
        result = extract_notice_fields(text, [])
        assert result['notice_type'] is not None
        assert result['survey_number'] is not None
        assert result['location'] is not None
