from datetime import datetime
from app.extensions import db

class Alert(db.Model):
    """Model representing an alert sent to a client."""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    dispute_id = db.Column(db.Integer, db.ForeignKey('disputes.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)
    alert_type = db.Column(db.String(50), default='new_dispute')  # new_dispute, status_change, severity_upgrade
    message = db.Column(db.Text, nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    delivered_at = db.Column(db.DateTime, nullable=True)
    delivery_status = db.Column(db.String(20), default='pending')  # pending, sent, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Alert {self.id}>'
