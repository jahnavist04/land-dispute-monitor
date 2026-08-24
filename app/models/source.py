from datetime import datetime
from app.extensions import db

class Source(db.Model):
    """Model representing a source of land dispute notices."""
    __tablename__ = 'sources'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    base_url = db.Column(db.String(1024), nullable=False, unique=True)
    scrape_frequency_minutes = db.Column(db.Integer, default=60)
    source_type = db.Column(db.String(50), default='html')  # html, image, pdf, mixed
    selectors_config = db.Column(db.JSON, default=dict)
    is_active = db.Column(db.Boolean, default=True)
    last_scraped_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    articles = db.relationship('RawArticle', backref='source', lazy='dynamic')
    
    def __repr__(self):
        return f'<Source {self.name}>'
