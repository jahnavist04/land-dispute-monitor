from datetime import datetime
from app.extensions import db

class Subscription(db.Model):
    """Model representing a client's subscription/monitoring preferences."""
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    tracked_regions = db.Column(db.JSON, default=list)  # ['Bangalore', 'Chennai']
    tracked_properties = db.Column(db.JSON, default=list)  # ['Sy No 123/4', ...]
    min_severity = db.Column(db.String(20), default='medium')  # minimum severity to alert on
    notification_method = db.Column(db.String(20), default='webhook')  # email, webhook, both
    webhook_url = db.Column(db.String(1024), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    alerts = db.relationship('Alert', backref='subscription', lazy='dynamic')
    
    def __repr__(self):
        return f'<Subscription {self.id}>'
