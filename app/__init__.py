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

    if Source.query.first() or Dispute.query.first():
        return

    client = Client(
        name='LandWatch Demo Client',
        email='demo@landwatch.local',
        company='LandWatch'
    )
    client.set_password('demo-access')
    db.session.add(client)

    demo_cases = [
        ('Deccan Herald', 'Bengaluru', 'Sy No. 142/2', 'Ownership Title Dispute', 'critical', 9),
        ('Eenadu', 'Hyderabad', 'Sy No. 45/1A', 'Partition & Succession Dispute', 'high', 8),
        ('The Hindu', 'Chennai', 'T.S. No. 88/4', 'Mortgage & SARFAESI Dispute', 'medium', 6),
    ]

    for source_name, location, survey_number, dispute_type, severity, urgency in demo_cases:
        source = Source(
            name=f'{source_name} Legal Notices',
            base_url=f'https://example.com/{source_name.lower().replace(" ", "-")}',
            source_type='html',
            selectors_config={'article_selector': 'a.notice'}
        )
        db.session.add(source)
        db.session.flush()

        article = RawArticle(
            source_id=source.id,
            url=f'https://example.com/notices/{survey_number.replace("/", "-")}',
            url_hash=f'vercel-demo-url-{source.id}',
            content_hash=f'vercel-demo-content-{source.id}',
            title=f'Public Notice: {dispute_type}',
            raw_text=f'Public legal notice concerning {survey_number} in {location}.',
            scrape_status='scraped'
        )
        db.session.add(article)
        db.session.flush()

        notice = ExtractedNotice(
            raw_article_id=article.id,
            notice_type='legal_notice',
            survey_number=survey_number,
            location=location,
            disputing_parties=['Demo Property Holder', 'Demo Respondent'],
            ocr_text=article.raw_text,
            processing_status='processed'
        )
        db.session.add(notice)
        db.session.flush()

        db.session.add(Dispute(
            extracted_notice_id=notice.id,
            dispute_type=dispute_type,
            location=location,
            parties_involved=notice.disputing_parties,
            urgency_score=urgency,
            severity=severity,
            status='active',
            summary=f'Demo {severity} risk notice concerning {survey_number} in {location}.',
            cluster_id=f'CLU-DEMO-{source.id}'
        ))

    db.session.commit()

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
            _seed_vercel_demo_data()

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
