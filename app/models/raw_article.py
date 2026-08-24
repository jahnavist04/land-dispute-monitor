from datetime import datetime
from app.extensions import db

class RawArticle(db.Model):
    """Model representing a scraped raw article."""
    __tablename__ = 'raw_articles'
    
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('sources.id'), nullable=False)
    url = db.Column(db.String(2048), nullable=False)
    url_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    content_hash = db.Column(db.String(64), nullable=True, index=True)
    title = db.Column(db.String(1024), nullable=True)
    raw_text = db.Column(db.Text, nullable=True)
    raw_html = db.Column(db.Text, nullable=True)
    image_urls = db.Column(db.JSON, default=list)  # list of image URLs found
    pdf_urls = db.Column(db.JSON, default=list)    # list of PDF URLs found
    publish_date = db.Column(db.DateTime, nullable=True)
    scrape_status = db.Column(db.String(20), default='pending')  # pending, scraped, failed
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    notices = db.relationship('ExtractedNotice', backref='raw_article', lazy='dynamic')
    
    def __repr__(self):
        return f'<RawArticle {self.url_hash}>'
