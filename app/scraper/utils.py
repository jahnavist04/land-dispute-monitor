import logging
import random
import time
from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from dateutil import parser

logger = logging.getLogger(__name__)

# User-Agent rotation list (10+ realistic browser user agents)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
]

def get_retry_session(retries: int = 3, backoff_factor: float = 0.5, timeout: int = 30) -> requests.Session:
    """Create a requests session with retry logic and random user agent."""
    session = requests.Session()
    retry = Retry(total=retries, backoff_factor=backoff_factor, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update({'User-Agent': random.choice(USER_AGENTS)})
    return session

def safe_request(url: str, session: requests.Session, timeout: int = 30) -> Optional[requests.Response]:
    """Make a safe HTTP request with error handling."""
    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f'Request failed for {url}: {e}')
        return None

def rate_limit(delay_seconds: float = 1.0) -> None:
    """Simple rate limiter — sleep between requests."""
    time.sleep(delay_seconds + random.uniform(0, 0.5))

def extract_publish_date(article) -> Optional[str]:
    """Extract publish date from newspaper3k article with fallbacks."""
    # Try newspaper3k's built-in date
    if article.publish_date:
        return article.publish_date.isoformat()
    
    if not article.html:
        return None
        
    soup = BeautifulSoup(article.html, 'html.parser')
    
    # Fallback: look for common date meta tags
    meta_tags = soup.find_all('meta', attrs={'name': ['pubdate', 'publishdate', 'timestamp', 'date', 'dc.date']})
    meta_tags.extend(soup.find_all('meta', attrs={'property': ['article:published_time', 'og:pubdate']}))
    
    for tag in meta_tags:
        content = tag.get('content')
        if content:
            try:
                parsed = parser.parse(content, fuzzy=True)
                return parsed.isoformat()
            except (ValueError, TypeError):
                continue
                
    # Fallback: look for time tags
    time_tags = soup.find_all('time')
    for tag in time_tags:
        dt = tag.get('datetime')
        if dt:
            try:
                parsed = parser.parse(dt, fuzzy=True)
                return parsed.isoformat()
            except (ValueError, TypeError):
                continue
                
    return None
