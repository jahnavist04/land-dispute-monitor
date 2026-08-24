import hashlib
import logging
from typing import Optional
from app.extensions import db
from app.models.raw_article import RawArticle

logger = logging.getLogger(__name__)

def compute_url_hash(url: str) -> str:
    """Compute SHA-256 hash of normalized URL."""
    normalized = url.strip().lower().rstrip('/')
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def compute_content_hash(text: str) -> str:
    """Compute SHA-256 hash of cleaned text content."""
    import re
    cleaned = re.sub(r'\s+', ' ', text.strip().lower())
    return hashlib.sha256(cleaned.encode('utf-8')).hexdigest()

def is_duplicate(url_or_hash: str, content_or_hash: Optional[str] = None) -> bool:
    """Check if article already exists by URL hash or content hash."""
    # Determine if raw URL or hash was passed
    if len(url_or_hash) == 64 and all(c in '0123456789abcdefABCDEF' for c in url_or_hash):
        u_hash = url_or_hash
    else:
        u_hash = compute_url_hash(url_or_hash)
        
    # Check URL hash first (fast)
    if RawArticle.query.filter_by(url_hash=u_hash).first():
        logger.debug(f'Duplicate found by URL hash: {u_hash[:16]}...')
        return True
        
    # Check content hash if provided
    if content_or_hash:
        if len(content_or_hash) == 64 and all(c in '0123456789abcdefABCDEF' for c in content_or_hash):
            c_hash = content_or_hash
        else:
            c_hash = compute_content_hash(content_or_hash)
            
        if RawArticle.query.filter_by(content_hash=c_hash).first():
            logger.debug(f'Duplicate found by content hash: {c_hash[:16]}...')
            return True
            
    return False
