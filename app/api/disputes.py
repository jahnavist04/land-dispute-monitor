from flask import Blueprint, request, jsonify
from datetime import datetime
from app.extensions import db
from app.models.dispute import Dispute
from app.models.extracted_notice import ExtractedNotice
from app.api import require_api_key

disputes_bp = Blueprint('disputes', __name__)

@disputes_bp.route('/disputes', methods=['GET'])
@require_api_key
def list_disputes():
    """List disputes with filtering and pagination.
    
    Query params:
    - location: filter by location (case-insensitive contains)
    - date_from: filter by created_at >= date (ISO format)
    - date_to: filter by created_at <= date
    - type: filter by dispute_type
    - severity: filter by severity
    - status: filter by status (active/resolved/monitoring)
    - page: page number (default 1)
    - per_page: items per page (default 20, max 100)
    """
    query = Dispute.query

    # Filters
    location = request.args.get('location')
    if location:
        query = query.filter(Dispute.location.ilike(f'%{location}%'))
    
    date_from_str = request.args.get('date_from')
    if date_from_str:
        try:
            date_from = datetime.fromisoformat(date_from_str)
            query = query.filter(Dispute.created_at >= date_from)
        except ValueError:
            return jsonify({'error': 'Invalid date_from format. Use ISO format.'}), 400
            
    date_to_str = request.args.get('date_to')
    if date_to_str:
        try:
            date_to = datetime.fromisoformat(date_to_str)
            query = query.filter(Dispute.created_at <= date_to)
        except ValueError:
            return jsonify({'error': 'Invalid date_to format. Use ISO format.'}), 400
            
    dispute_type = request.args.get('type')
    if dispute_type:
        query = query.filter(Dispute.dispute_type == dispute_type)
        
    severity = request.args.get('severity')
    if severity:
        query = query.filter(Dispute.severity == severity)
        
    status = request.args.get('status')
    if status:
        query = query.filter(Dispute.status == status)

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    pagination = query.order_by(Dispute.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    items = []
    for dispute in pagination.items:
        items.append({
            'id': dispute.id,
            'location': dispute.location,
            'dispute_type': dispute.dispute_type,
            'severity': dispute.severity,
            'urgency_score': dispute.urgency_score,
            'status': dispute.status,
            'summary': dispute.summary,
            'created_at': dispute.created_at.isoformat() if dispute.created_at else None,
            'cluster_id': dispute.cluster_id
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

@disputes_bp.route('/disputes/<int:dispute_id>', methods=['GET'])
@require_api_key
def get_dispute(dispute_id):
    """Get single dispute detail with related notices."""
    dispute = Dispute.query.get_or_404(dispute_id)
    notice = ExtractedNotice.query.get(dispute.extracted_notice_id) if dispute.extracted_notice_id else None
    
    notice_list = []
    if notice:
        notice_list.append({
            'id': notice.id,
            'notice_type': notice.notice_type,
            'property_number': notice.property_number,
            'survey_number': notice.survey_number,
            'location': notice.location,
            'issuing_authority': notice.issuing_authority,
            'notice_date': notice.notice_date.isoformat() if notice.notice_date else None,
            'ocr_text': notice.ocr_text,
            'disputing_parties': notice.disputing_parties or []
        })
        
    return jsonify({
        'id': dispute.id,
        'location': dispute.location,
        'dispute_type': dispute.dispute_type,
        'severity': dispute.severity,
        'urgency_score': dispute.urgency_score,
        'status': dispute.status,
        'summary': dispute.summary,
        'created_at': dispute.created_at.isoformat() if dispute.created_at else None,
        'cluster_id': dispute.cluster_id,
        'notices': notice_list
    }), 200

@disputes_bp.route('/disputes/<int:dispute_id>/notices', methods=['GET'])
@require_api_key
def get_dispute_notices(dispute_id):
    """Get extracted notices related to a dispute."""
    dispute = Dispute.query.get_or_404(dispute_id)
    notice = ExtractedNotice.query.get(dispute.extracted_notice_id) if dispute.extracted_notice_id else None
    
    notice_list = []
    if notice:
        notice_list.append({
            'id': notice.id,
            'notice_type': notice.notice_type,
            'property_number': notice.property_number,
            'survey_number': notice.survey_number,
            'location': notice.location,
            'issuing_authority': notice.issuing_authority,
            'notice_date': notice.notice_date.isoformat() if notice.notice_date else None,
            'ocr_text': notice.ocr_text,
            'disputing_parties': notice.disputing_parties or []
        })
        
    return jsonify({'notices': notice_list}), 200

@disputes_bp.route('/disputes/clusters/<cluster_id>', methods=['GET'])
@require_api_key
def get_cluster(cluster_id):
    """Get all disputes in a cluster."""
    disputes = Dispute.query.filter_by(cluster_id=cluster_id).all()
    
    items = []
    for dispute in disputes:
        items.append({
            'id': dispute.id,
            'location': dispute.location,
            'dispute_type': dispute.dispute_type,
            'severity': dispute.severity,
            'urgency_score': dispute.urgency_score,
            'status': dispute.status,
            'summary': dispute.summary,
            'created_at': dispute.created_at.isoformat() if dispute.created_at else None,
            'cluster_id': dispute.cluster_id
        })
        
    return jsonify({'cluster_id': cluster_id, 'disputes': items}), 200
