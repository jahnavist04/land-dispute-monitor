import secrets
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db

class Client(UserMixin, db.Model):
    """Model representing a system client or user."""
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=True)
    company = db.Column(db.String(255), nullable=True)
    api_key = db.Column(db.String(64), unique=True, default=lambda: secrets.token_hex(32))
    plan_tier = db.Column(db.String(20), default='basic')  # basic, pro, enterprise
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = db.relationship('Subscription', backref='client', lazy='dynamic')
    alerts = db.relationship('Alert', backref='client', lazy='dynamic')
    
    def set_password(self, password: str):
        """Set hashed password."""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password: str) -> bool:
        """Check password against hash."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Client {self.name}>'
