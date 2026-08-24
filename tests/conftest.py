import pytest
from app import create_app
from app.extensions import db as _db
from app.models.client import Client
from app.models.source import Source

@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    app = create_app('testing')
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()

@pytest.fixture(scope='function')
def db_session(app):
    """Create a clean database session for each test."""
    with app.app_context():
        yield _db.session
        _db.session.rollback()
        # Clean up tables between test runs
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()

@pytest.fixture
def client(app, db_session):
    """Flask test client."""
    return app.test_client()

@pytest.fixture
def api_client(app, db_session):
    """Authenticated API client with a test Client record."""
    test_client = Client.query.filter_by(api_key='test-api-key-12345').first()
    if not test_client:
        test_client = Client(
            name='Test Client',
            email='test@example.com',
            company='Test Corp',
            api_key='test-api-key-12345',
            plan_tier='enterprise',
            is_active=True
        )
        db_session.add(test_client)
        db_session.commit()
        
    flask_client = app.test_client()
    flask_client.api_key = 'test-api-key-12345'
    flask_client.test_client_id = test_client.id
    return flask_client

@pytest.fixture
def sample_source(db_session):
    """Sample newspaper source."""
    source = Source(
        name='Test Newspaper',
        base_url='https://example-newspaper.com/notices',
        scrape_frequency_minutes=60,
        source_type='html',
        selectors_config={
            'article_links': 'a.article-link',
            'title': 'h1.article-title',
            'body': 'div.article-body',
            'date': 'time.published',
            'notice_images': 'img.legal-notice'
        },
        is_active=True
    )
    db_session.add(source)
    db_session.commit()
    return source
