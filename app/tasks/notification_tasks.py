import logging
import json
import httpx
import hmac
import hashlib
from datetime import datetime, timezone
from flask import current_app
from app.extensions import celery, db
from app.models.dispute import Dispute
from app.models.alert import Alert
from app.models.subscription import Subscription
from app import create_app

logger = logging.getLogger(__name__)

SEVERITY_ORDER = {
    'informational': 0,
    'low': 1,
    'medium': 2,
    'high': 3,
    'critical': 4
}

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def check_and_send_alerts(self):
    """Match new disputes against active subscriptions and create alerts."""
    app = create_app()
    with app.app_context():
        try:
            # Checking recent disputes against active subscriptions
            disputes = Dispute.query.order_by(Dispute.created_at.desc()).limit(100).all()
            subscriptions = Subscription.query.filter_by(is_active=True).all()
            
            alerts_created = 0
            for dispute in disputes:
                dispute_severity_val = SEVERITY_ORDER.get(dispute.severity.lower() if dispute.severity else 'informational', 0)
                
                for sub in subscriptions:
                    # Check if alert already exists
                    existing_alert = Alert.query.filter_by(
                        subscription_id=sub.id,
                        dispute_id=dispute.id
                    ).first()
                    
                    if existing_alert:
                        continue
                        
                    # Check severity
                    sub_severity_val = SEVERITY_ORDER.get(sub.min_severity.lower() if sub.min_severity else 'informational', 0)
                    if dispute_severity_val < sub_severity_val:
                        continue
                        
                    # Check location match (case-insensitive contains)
                    location_match = False
                    if not sub.tracked_regions:
                        location_match = True  # If no regions specified, track all
                    elif dispute.location:
                        dispute_loc = dispute.location.lower()
                        for region in sub.tracked_regions:
                            if region.lower() in dispute_loc:
                                location_match = True
                                break
                                
                    if location_match:
                        # Create alert
                        alert = Alert(
                            client_id=sub.client_id,
                            subscription_id=sub.id,
                            dispute_id=dispute.id,
                            alert_type='new_dispute',
                            message=f"New {dispute.severity} dispute detected: {dispute.summary[:100] if dispute.summary else dispute.location}",
                            delivery_status='pending'
                        )
                        db.session.add(alert)
                        db.session.flush()
                        
                        # Dispatch delivery tasks
                        if sub.webhook_url:
                            send_webhook.delay(alert.id)
                        if sub.client and sub.client.email and sub.notification_method in ['email', 'both']:
                            send_email_alert.delay(alert.id)
                            
                        alerts_created += 1
                        
            db.session.commit()
            logger.info(f"Created {alerts_created} alerts")
            return {'alerts_created': alerts_created}
            
        except Exception as exc:
            db.session.rollback()
            logger.error(f"Error checking alerts: {exc}")
            raise self.retry(exc=exc)

@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def send_webhook(self, alert_id: int):
    """Send webhook notification for an alert."""
    app = create_app()
    with app.app_context():
        try:
            alert = Alert.query.get(alert_id)
            if not alert or not alert.subscription or not alert.subscription.webhook_url:
                return
                
            sub = alert.subscription
            dispute = alert.dispute
            
            payload = {
                'alert_id': alert.id,
                'dispute_id': dispute.id,
                'dispute_type': dispute.dispute_type,
                'severity': dispute.severity,
                'location': dispute.location,
                'summary': dispute.summary,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            payload_bytes = json.dumps(payload).encode('utf-8')
            
            # Sign payload with HMAC-SHA256
            secret = current_app.config.get('SECRET_KEY', 'default_secret').encode('utf-8')
            signature = hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()
            
            headers = {
                'Content-Type': 'application/json',
                'X-Webhook-Signature': signature
            }
            
            # Send using httpx
            with httpx.Client(timeout=10.0) as client:
                response = client.post(sub.webhook_url, content=payload_bytes, headers=headers)
                response.raise_for_status()
                
            alert.delivery_status = 'sent'
            alert.delivered_at = datetime.now(timezone.utc)
            db.session.commit()
            logger.info(f"Webhook delivered for alert {alert.id}")
            
        except Exception as exc:
            logger.error(f"Webhook delivery failed for alert {alert_id}: {exc}")
            raise self.retry(exc=exc)

@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def send_email_alert(self, alert_id: int):
    """Send email notification for an alert (logs to console/service)."""
    app = create_app()
    with app.app_context():
        try:
            alert = Alert.query.get(alert_id)
            if not alert or not alert.subscription or not alert.subscription.client:
                return
                
            email = alert.subscription.client.email
            logger.info(f"Sending email notification for alert #{alert.id} to {email}")
            
            alert.delivery_status = 'sent'
            alert.delivered_at = datetime.now(timezone.utc)
            db.session.commit()
            
        except Exception as exc:
            logger.error(f"Email delivery failed for alert {alert_id}: {exc}")
            raise self.retry(exc=exc)
