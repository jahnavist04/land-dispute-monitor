from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.source import Source
from app.api import require_api_key

sources_bp = Blueprint('sources', __name__)

@sources_bp.route('/sources', methods=['GET'])
@require_api_key
def list_sources():
    """List all newspaper sources."""
    sources = Source.query.all()
    items = []
    for source in sources:
        items.append({
            'id': source.id,
            'name': source.name,
            'base_url': source.base_url,
            'scrape_frequency_minutes': source.scrape_frequency_minutes,
            'source_type': source.source_type,
            'selectors_config': source.selectors_config or {},
            'is_active': source.is_active,
            'last_scraped_at': source.last_scraped_at.isoformat() if source.last_scraped_at else None
        })
    return jsonify({'sources': items}), 200

@sources_bp.route('/sources', methods=['POST'])
@require_api_key
def create_source():
    """Add a new newspaper source."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON data'}), 400
        
    if 'name' not in data or 'base_url' not in data:
        return jsonify({'error': 'Missing required fields: name and base_url'}), 400
        
    source = Source(
        name=data['name'],
        base_url=data['base_url'],
        scrape_frequency_minutes=data.get('scrape_frequency_minutes', 120),
        source_type=data.get('source_type', 'html'),
        selectors_config=data.get('selectors_config', {}),
        is_active=True
    )
    
    db.session.add(source)
    db.session.commit()
    
    return jsonify({'id': source.id, 'message': 'Source created successfully'}), 201

@sources_bp.route('/sources/<int:source_id>', methods=['PUT'])
@require_api_key
def update_source(source_id):
    """Update a newspaper source."""
    source = Source.query.get_or_404(source_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON data'}), 400
        
    if 'name' in data:
        source.name = data['name']
    if 'base_url' in data:
        source.base_url = data['base_url']
    if 'scrape_frequency_minutes' in data:
        source.scrape_frequency_minutes = data['scrape_frequency_minutes']
    if 'source_type' in data:
        source.source_type = data['source_type']
    if 'selectors_config' in data:
        source.selectors_config = data['selectors_config']
    if 'is_active' in data:
        source.is_active = data['is_active']
        
    db.session.commit()
    return jsonify({'message': 'Source updated successfully'}), 200

@sources_bp.route('/sources/<int:source_id>', methods=['DELETE'])
@require_api_key
def delete_source(source_id):
    """Soft delete (deactivate) a source."""
    source = Source.query.get_or_404(source_id)
    source.is_active = False
    db.session.commit()
    return jsonify({'message': 'Source deactivated successfully'}), 200
