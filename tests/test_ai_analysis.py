import pytest
from unittest.mock import patch, MagicMock
from app.ai_analysis.analyzer import DisputeAnalyzer
from app.ai_analysis.classifier import classify_severity, is_relevant_for_real_estate
from app.ai_analysis.clustering import find_or_create_cluster, _generate_cluster_id

class TestClassifier:
    def test_severity_critical(self):
        assert classify_severity(9) == 'critical'
        assert classify_severity(10) == 'critical'
    
    def test_severity_high(self):
        assert classify_severity(7) == 'high'
    
    def test_severity_medium(self):
        assert classify_severity(5) == 'medium'
    
    def test_severity_low(self):
        assert classify_severity(2) == 'low'
    
    def test_severity_informational(self):
        assert classify_severity(1) == 'informational'
    
    def test_severity_none(self):
        assert classify_severity(None) == 'medium'  # default
    
    def test_relevant_boundary_dispute(self):
        assert is_relevant_for_real_estate({'dispute_type': 'boundary_dispute'}) is True
    
    def test_not_relevant_other(self):
        assert is_relevant_for_real_estate({'dispute_type': 'other'}) is False

class TestAnalyzer:
    @patch('app.ai_analysis.analyzer.httpx.Client')
    def test_analyze_openai(self, mock_httpx, app):
        """Test OpenAI API call with mocked response."""
        mock_client = MagicMock()
        mock_httpx.return_value.__enter__.return_value = mock_client
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"severity": 8, "dispute_type": "title_dispute"}'}}]
        }
        mock_client.post.return_value = mock_response
        
        analyzer = DisputeAnalyzer()
        result = analyzer.analyze("Sample notice text")
        assert result.get("severity") == 8
    
    def test_parse_response_valid_json(self, app):
        """Test parsing valid JSON response."""
        analyzer = DisputeAnalyzer()
        result = analyzer._parse_response('{"test": "value"}')
        assert result == {"test": "value"}
    
    def test_parse_response_json_in_markdown(self, app):
        """Test extracting JSON from markdown code block."""
        analyzer = DisputeAnalyzer()
        result = analyzer._parse_response('```json\n{"test": "value"}\n```')
        assert result == {"test": "value"}

class TestClustering:
    def test_generate_cluster_id(self):
        cid = _generate_cluster_id()
        assert len(cid) == 12
        assert isinstance(cid, str)
