from datetime import datetime
from app.extensions import db

class ExtractedNotice(db.Model):
    """Model representing a notice extracted from an article."""
    __tablename__ = 'extracted_notices'
    
    id = db.Column(db.Integer, primary_key=True)
    raw_article_id = db.Column(db.Integer, db.ForeignKey('raw_articles.id'), nullable=False)
    notice_type = db.Column(db.String(100), nullable=True)  # sale, mortgage, dispute, partition
    property_number = db.Column(db.String(255), nullable=True)
    survey_number = db.Column(db.String(255), nullable=True)
    disputing_parties = db.Column(db.JSON, default=list)
    location = db.Column(db.String(512), nullable=True)
    notice_date = db.Column(db.DateTime, nullable=True)
    issuing_authority = db.Column(db.String(512), nullable=True)
    ocr_text = db.Column(db.Text, nullable=True)
    ocr_confidence_scores = db.Column(db.JSON, default=dict)
    needs_manual_review = db.Column(db.Boolean, default=False)
    processing_status = db.Column(db.String(20), default='pending')  # pending, processed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    dispute = db.relationship('Dispute', backref='extracted_notice', uselist=False)
    
    def __repr__(self):
        return f'<ExtractedNotice {self.id}>'
