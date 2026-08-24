import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:////tmp/landwatch.db' if os.environ.get('VERCEL') else 'sqlite:///land_disputes.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
    
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'openai')
    LLM_MODEL = os.environ.get('LLM_MODEL', 'gpt-4o')
    
    TESSERACT_CMD = os.environ.get('TESSERACT_CMD', '/usr/bin/tesseract')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    SCRAPE_DEFAULT_INTERVAL_MINUTES = 60
    OCR_CONFIDENCE_THRESHOLD = 0.7
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 30

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
