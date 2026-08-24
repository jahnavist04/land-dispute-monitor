"""Celery configuration for the Land Dispute Monitoring System."""
import os
from dotenv import load_dotenv

load_dotenv()

# Broker and backend
broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

# Serialization
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

# Task settings
task_acks_late = True
task_reject_on_worker_lost = True
worker_prefetch_multiplier = 1

# Beat schedule (periodic tasks)
beat_schedule = {
    'scrape-all-sources-hourly': {
        'task': 'app.tasks.scraping_tasks.scrape_all_sources',
        'schedule': 3600.0,  # every hour (default, individual sources have their own frequency)
    },
    'process-ocr-queue': {
        'task': 'app.tasks.ocr_tasks.process_ocr_queue',
        'schedule': 300.0,  # every 5 minutes
    },
    'analyze-queue': {
        'task': 'app.tasks.analysis_tasks.analyze_queue',
        'schedule': 300.0,  # every 5 minutes
    },
    'check-and-send-alerts': {
        'task': 'app.tasks.notification_tasks.check_and_send_alerts',
        'schedule': 60.0,  # every minute
    },
    'recluster-disputes-daily': {
        'task': 'app.tasks.analysis_tasks.recluster_disputes',
        'schedule': 86400.0,  # daily
    },
}
