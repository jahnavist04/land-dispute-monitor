import logging
import os
from flask import Flask, request
from flask_login import current_user, login_user
from app.config import DevelopmentConfig, ProductionConfig, TestingConfig
from app.extensions import db, migrate, celery, init_celery, login_manager


def _seed_vercel_demo_data():
    from app.models.client import Client
    from app.models.source import Source
    from app.models.raw_article import RawArticle
    from app.models.extracted_notice import ExtractedNotice
    from app.models.dispute import Dispute

def create_app(config_name='development'):
    """Flask application factory."""
    app = Flask(__name__)
    
    if config_name == 'development':
        app.config.from_object(DevelopmentConfig)
    elif config_name == 'production':
        app.config.from_object(ProductionConfig)
    elif config_name == 'testing':
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(DevelopmentConfig)
        
    logging.basicConfig(level=app.config.get('LOG_LEVEL', 'INFO'))
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    init_celery(app)
    
    # Flask-Login user loader
    from app.models.client import Client
    @login_manager.user_loader
    def load_user(user_id):
        return Client.query.get(int(user_id))

    @app.before_request
    def auto_login_web_user():
        """Use the first active client for the public dashboard experience."""
        if request.path == '/api/health' or request.path.startswith('/api/'):
            return

        if os.environ.get('VERCEL'):
            db.create_all()

        if current_user.is_authenticated:
            return
        guest = Client.query.filter_by(is_active=True).order_by(Client.id).first()
        if not guest:
            guest = Client(
                name='LandWatch Demo Client',
                email='demo@landwatch.local',
                company='LandWatch'
            )
            guest.set_password('demo-access')
            db.session.add(guest)
            db.session.commit()
        if guest:
            login_user(guest, remember=False)
        
    # Global template context processor
    @app.context_processor
    def inject_global_context():
        unread_count = 0
        if current_user.is_authenticated:
            from app.models.alert import Alert
            unread_count = Alert.query.filter_by(
                client_id=current_user.id, is_read=False
            ).count()
        return dict(unread_count=unread_count)
    
    # Blueprint registrations
    from app.api.disputes import disputes_bp
    from app.api.subscriptions import subscriptions_bp
    from app.api.clients import clients_bp
    from app.api.sources import sources_bp
    from app.web import web_bp
    
    app.register_blueprint(disputes_bp, url_prefix='/api/v1')
    app.register_blueprint(subscriptions_bp, url_prefix='/api/v1')
    app.register_blueprint(clients_bp, url_prefix='/api/v1')
    app.register_blueprint(sources_bp, url_prefix='/api/v1')
    app.register_blueprint(web_bp, url_prefix='')

    return app
