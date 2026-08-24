import pytest
from unittest.mock import patch, MagicMock
from app.scraper.dedup import compute_url_hash, compute_content_hash, is_duplicate
from app.scraper.utils import get_retry_session
from app.scraper.engine import ScraperEngine
from app.models.raw_article import RawArticle

class TestDedup:
    def test_compute_url_hash_consistent(self):
        """Same URL should always produce same hash."""
        url = "https://example.com/article"
        hash1 = compute_url_hash(url)
        hash2 = compute_url_hash(url)
        assert hash1 == hash2
    
    def test_compute_url_hash_normalizes(self):
        """URL hash should normalize (lowercase, strip trailing slash)."""
        hash1 = compute_url_hash("HTTPS://EXAMPLE.COM/ARTICLE/")
        hash2 = compute_url_hash("https://example.com/article")
        assert hash1 == hash2
    
    def test_compute_content_hash_consistent(self):
        content = "Sample content"
        hash1 = compute_content_hash(content)
        hash2 = compute_content_hash(content)
        assert hash1 == hash2
    
    def test_compute_content_hash_ignores_whitespace(self):
        content1 = "Sample content with spaces"
        content2 = "Sample   content\nwith\tspaces  "
        hash1 = compute_content_hash(content1)
        hash2 = compute_content_hash(content2)
        assert hash1 == hash2
    
    def test_is_duplicate_returns_false_for_new(self, app, db_session):
        assert is_duplicate("https://example.com/new", "New content") is False
    
    def test_is_duplicate_returns_true_for_existing_url(self, app, db_session, sample_source):
        """Create a RawArticle, then check is_duplicate returns True."""
        url = "https://example.com/existing"
        content = "Existing content"
        url_hash = compute_url_hash(url)
        content_hash = compute_content_hash(content)
        
        article = RawArticle(
            source_id=sample_source.id,
            url=url,
            url_hash=url_hash,
            content_hash=content_hash,
            title="Existing Title"
        )
        db_session.add(article)
        db_session.flush()
        
        assert is_duplicate(url, content) is True

class TestScraperUtils:
    def test_get_retry_session_has_user_agent(self):
        session = get_retry_session()
        assert 'User-Agent' in session.headers
    
    def test_get_retry_session_has_retry_adapter(self):
        session = get_retry_session()
        adapter = session.get_adapter('http://')
        assert adapter.max_retries is not None

class TestScraperEngine:
    @patch('app.scraper.engine.safe_request')
    def test_scrape_handles_network_error(self, mock_request, app, db_session, sample_source):
        """Scraper should handle network errors gracefully."""
        mock_request.return_value = None
        engine = ScraperEngine(sample_source.id)
        result = engine.scrape()
        assert result['errors'] == 1
        assert result['new_articles'] == 0
    
    @patch('app.scraper.engine.safe_request')
    def test_scrape_deduplicates(self, mock_request, app, db_session, sample_source):
        """Scraper should skip duplicate articles."""
        # Create an existing article
        url = "https://example.com/notices/1"
        url_hash = compute_url_hash(url)
        article = RawArticle(
            source_id=sample_source.id,
            url=url,
            url_hash=url_hash,
            title="Existing Dispute"
        )
        db_session.add(article)
        db_session.flush()
        
        # Mock listing page returning the same url
        mock_resp = MagicMock()
        mock_resp.text = f'<html><body><a href="{url}">Notice Link</a></body></html>'
        mock_request.return_value = mock_resp
        
        engine = ScraperEngine(sample_source.id)
        result = engine.scrape()
        assert result['duplicates'] == 1
        assert result['new_articles'] == 0
