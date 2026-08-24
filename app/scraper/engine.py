import logging
from typing import Optional, List, Tuple
from urllib.parse import urljoin
from datetime import datetime
from bs4 import BeautifulSoup
from newspaper import Article

from app.extensions import db
from app.models.source import Source
from app.models.raw_article import RawArticle
from app.scraper.utils import get_retry_session, safe_request, rate_limit, extract_publish_date
from app.scraper.dedup import compute_url_hash, compute_content_hash, is_duplicate

logger = logging.getLogger(__name__)

class ScraperEngine:
    """Main scraping engine for fetching and processing articles from sources."""
    
    def __init__(self, source_id: int):
        self.source_id = source_id
        self.source = Source.query.get(source_id)
        if not self.source:
            raise ValueError(f"Source with id {source_id} not found")
        self.session = get_retry_session()
        
    def scrape(self) -> dict:
        """Main entry point. Scrape the source and return results summary."""
        summary = {
            'total_found': 0,
            'new_articles': 0,
            'duplicates': 0,
            'errors': 0
        }
        
        logger.info(f"Starting scrape for source: {self.source.name} ({self.source.base_url})")
        
        # 1. Fetch article listing page
        response = safe_request(self.source.base_url, self.session)
        if not response:
            logger.error(f"Failed to fetch source URL: {self.source.base_url}")
            summary['errors'] += 1
            return summary
            
        # 2. Extract article links using source's CSS selectors
        article_links = self._fetch_article_links(response.text)
        summary['total_found'] = len(article_links)
        logger.info(f"Found {len(article_links)} links for source {self.source.name}")
        
        # 3. For each article link:
        for link in article_links:
            try:
                # a. Check dedup
                url_hash = compute_url_hash(link)
                if is_duplicate(url_hash):
                    summary['duplicates'] += 1
                    continue
                    
                # b. Fetch article page, c. Extract text, d. Extract media, e. Store
                rate_limit()
                article = self._process_article(link, url_hash)
                
                if article:
                    db.session.add(article)
                    db.session.commit()
                    summary['new_articles'] += 1
                else:
                    summary['errors'] += 1
            except Exception as e:
                logger.error(f"Error processing article {link}: {e}", exc_info=True)
                db.session.rollback()
                summary['errors'] += 1
                
        # 4. Update source.last_scraped_at
        self.source.last_scraped_at = datetime.utcnow()
        db.session.commit()
        
        # 5. Return summary
        logger.info(f"Scrape finished for {self.source.name}: {summary}")
        return summary
        
    def _fetch_article_links(self, html: str) -> List[str]:
        """Extract article URLs from listing page using CSS selectors from source config."""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        selector = 'a'
        if self.source.selectors_config and isinstance(self.source.selectors_config, dict):
            selector = self.source.selectors_config.get('article_selector', 'a')
            
        elements = soup.select(selector)
        
        for el in elements:
            href = el.get('href')
            if href:
                full_url = urljoin(self.source.base_url, href)
                if full_url.startswith('http'):
                    links.append(full_url)
                    
        return list(dict.fromkeys(links))
        
    def _process_article(self, url: str, url_hash: str) -> Optional[RawArticle]:
        """Fetch, parse, and store a single article."""
        logger.debug(f"Processing article: {url}")
        
        # Fetch article page
        response = safe_request(url, self.session)
        if not response:
            return None
            
        # Use newspaper3k Article for text extraction
        article = Article(url)
        article.download(input_html=response.text)
        article.parse()
        
        title = article.title
        text_content = article.text
        html_content = response.text
        
        if not text_content:
            logger.warning(f"No text extracted for {url}")
            return None
            
        # Check dedup by content hash
        content_hash = compute_content_hash(text_content)
        if is_duplicate(url_hash, content_hash):
            return None
            
        # Extract publish date
        published_at_str = extract_publish_date(article)
        published_at = None
        if published_at_str:
            from dateutil import parser
            try:
                published_at = parser.parse(published_at_str)
            except Exception:
                pass
        
        # Extract media URLs
        soup = BeautifulSoup(html_content, 'html.parser')
        images, pdfs = self._extract_media_urls(soup, url)
        
        # Create DB record matching RawArticle model
        raw_article = RawArticle(
            source_id=self.source_id,
            url=url,
            url_hash=url_hash,
            content_hash=content_hash,
            title=title,
            raw_text=text_content,
            raw_html=html_content,
            image_urls=images,
            pdf_urls=pdfs,
            publish_date=published_at,
            scrape_status='scraped'
        )
        
        return raw_article
        
    def _extract_media_urls(self, soup: BeautifulSoup, base_url: str) -> Tuple[List[str], List[str]]:
        """Extract image and PDF URLs from article page."""
        images = []
        pdfs = []
        
        # Look for img tags
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                images.append(urljoin(base_url, src))
                
        # Look for a[href] ending in .pdf
        for a in soup.find_all('a', href=True):
            href = a.get('href')
            if href and href.lower().endswith('.pdf'):
                pdfs.append(urljoin(base_url, href))
                
        return list(set(images)), list(set(pdfs))
