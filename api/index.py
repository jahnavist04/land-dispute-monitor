from flask import jsonify
from sqlalchemy import text

from app import create_app

app = create_app()


@app.route('/api/health')
def health():
	return jsonify({'status': 'ok', 'service': 'land-dispute-monitor'})


@app.route('/api/db-health')
def db_health():
	try:
		from app.extensions import db
		with db.engine.connect() as connection:
			connection.execute(text('SELECT 1'))
		return jsonify({'status': 'ok', 'database': 'connected'})
	except Exception as error:
		return jsonify({'status': 'error', 'error_type': type(error).__name__, 'message': str(error)[:300]}), 500
