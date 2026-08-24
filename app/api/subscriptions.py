from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.subscription import Subscription
from app.api import require_api_key

subscriptions_bp = Blueprint('subscriptions', __name__)

@subscriptions_bp.route('/subscribe', methods=['POST'])
@require_api_key
def create_subscription():
    """Create a new subscription."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON data'}), 400
        
    if 'tracked_regions' not in data and 'tracked_properties' not in data:
        return jsonify({'error': 'Missing required field: tracked_regions or tracked_properties'}), 400

    sub = Subscription(
        client_id=request.client.id,
        tracked_regions=data.get('tracked_regions', []),
        tracked_properties=data.get('tracked_properties', []),
        min_severity=data.get('min_severity', 'low'),
        notification_method=data.get('notification_method', 'email'),
        webhook_url=data.get('webhook_url'),
        is_active=True
    )
    
    db.session.add(sub)
    db.session.commit()
    
    return jsonify({'id': sub.id, 'message': 'Subscription created successfully'}), 201

@subscriptions_bp.route('/subscriptions/<int:sub_id>', methods=['GET'])
@require_api_key
def get_subscription(sub_id):
    """Get a subscription by ID."""
    sub = Subscription.query.get_or_404(sub_id)
    if sub.client_id != request.client.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    return jsonify({
        'id': sub.id,
        'client_id': sub.client_id,
        'tracked_regions': getattr(sub, 'tracked_regions', []),
        'tracked_properties': getattr(sub, 'tracked_properties', []),
        'min_severity': getattr(sub, 'min_severity', 'low'),
        'notification_method': getattr(sub, 'notification_method', 'email'),
        'webhook_url': getattr(sub, 'webhook_url', None),
        'is_active': getattr(sub, 'is_active', True)
    }), 200

@subscriptions_bp.route('/subscriptions/<int:sub_id>', methods=['PUT'])
@require_api_key
def update_subscription(sub_id):
    """Update a subscription."""
    sub = Subscription.query.get_or_404(sub_id)
    if sub.client_id != request.client.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON data'}), 400
        
    if 'tracked_regions' in data:
        sub.tracked_regions = data['tracked_regions']
    if 'tracked_properties' in data:
        sub.tracked_properties = data['tracked_properties']
    if 'min_severity' in data:
        sub.min_severity = data['min_severity']
    if 'notification_method' in data:
        sub.notification_method = data['notification_method']
    if 'webhook_url' in data:
        sub.webhook_url = data['webhook_url']
    if 'is_active' in data:
        sub.is_active = data['is_active']
        
    db.session.commit()
    return jsonify({'message': 'Subscription updated successfully'}), 200

@subscriptions_bp.route('/subscriptions/<int:sub_id>', methods=['DELETE'])
@require_api_key
def delete_subscription(sub_id):
    """Soft delete (deactivate) a subscription."""
    sub = Subscription.query.get_or_404(sub_id)
    if sub.client_id != request.client.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    sub.is_active = False
    db.session.commit()
    return jsonify({'message': 'Subscription deactivated successfully'}), 200
