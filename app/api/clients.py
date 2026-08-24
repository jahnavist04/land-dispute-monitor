from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.alert import Alert
from app.models.dispute import Dispute
from app.api import require_api_key

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/clients/<int:client_id>/alerts', methods=['GET'])
@require_api_key
def get_client_alerts(client_id):
    """Get alerts for a client with pagination."""
    if client_id != request.client.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    query = Alert.query.filter_by(client_id=client_id)
    
    is_read = request.args.get('is_read')
    if is_read is not None:
        is_read_bool = is_read.lower() in ['true', '1', 't', 'y', 'yes']
        query = query.filter_by(is_read=is_read_bool)
        
    severity = request.args.get('severity')
    if severity:
        query = query.join(Dispute).filter(Dispute.severity == severity)
        
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    pagination = query.order_by(Alert.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    items = []
    for alert in pagination.items:
        items.append({
            'id': alert.id,
            'dispute_id': alert.dispute_id,
            'message': alert.message or '',
            'severity': alert.dispute.severity if alert.dispute else 'low',
            'is_read': alert.is_read,
            'delivery_status': alert.delivery_status,
            'created_at': alert.created_at.isoformat() if alert.created_at else None
        })
        
    return jsonify({
        'items': items,
        'pagination': {
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': pagination.page,
            'per_page': pagination.per_page
        }
    }), 200

@clients_bp.route('/alerts/<int:alert_id>/read', methods=['PUT'])
@require_api_key
def mark_alert_read(alert_id):
    """Mark an alert as read."""
    alert = Alert.query.get_or_404(alert_id)
    if alert.client_id != request.client.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    alert.is_read = True
    db.session.commit()
    
    return jsonify({'message': 'Alert marked as read successfully'}), 200
