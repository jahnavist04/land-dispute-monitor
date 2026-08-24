from flask import jsonify

from app import create_app

app = create_app()


@app.route('/api/health')
def health():
	return jsonify({'status': 'ok', 'service': 'land-dispute-monitor'})
