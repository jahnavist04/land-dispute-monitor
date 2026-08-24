"""REST API module for the Land Dispute Monitoring System."""
import functools
from flask import request, jsonify
from app.models.client import Client

def require_api_key(f):
    """Decorator to require API key authentication via X-API-Key header."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'Missing API key'}), 401
        client = Client.query.filter_by(api_key=api_key, is_active=True).first()
        if not client:
            return jsonify({'error': 'Invalid API key'}), 401
        # Attach client to request context
        request.client = client
        return f(*args, **kwargs)
    return decorated
