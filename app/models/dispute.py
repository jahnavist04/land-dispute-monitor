from datetime import datetime
from app.extensions import db

class Dispute(db.Model):
    """Model representing a verified land dispute."""
    __tablename__ = 'disputes'
    
    id = db.Column(db.Integer, primary_key=True)
    extracted_notice_id = db.Column(db.Integer, db.ForeignKey('extracted_notices.id'), nullable=False)
    dispute_type = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(512), nullable=True)
    parties_involved = db.Column(db.JSON, default=list)
    urgency_score = db.Column(db.Integer, nullable=True)  # 1-10
    severity = db.Column(db.String(20), default='medium')  # critical, high, medium, low, informational
    status = db.Column(db.String(20), default='active')  # active, resolved, monitoring
    summary = db.Column(db.Text, nullable=True)
    raw_llm_response = db.Column(db.JSON, nullable=True)
    cluster_id = db.Column(db.String(64), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    alerts = db.relationship('Alert', backref='dispute', lazy='dynamic')
    
    def __repr__(self):
        return f'<Dispute {self.id}>'
