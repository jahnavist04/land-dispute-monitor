import logging
from datetime import datetime, timezone, timedelta
from app.extensions import celery, db
from app.models.source import Source
from app.scraper.engine import ScraperEngine
from app import create_app

logger = logging.getLogger(__name__)

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def scrape_all_sources(self):
    """Periodic task: dispatch individual scrape tasks for all active sources.
    
    Checks each source's scrape_frequency_minutes and last_scraped_at
    to determine if it's due for scraping.
    """
    app = create_app()
    with app.app_context():
        sources = Source.query.filter_by(is_active=True).all()
        dispatched = 0
        now = datetime.now(timezone.utc)
        for source in sources:
            if source.last_scraped_at:
                last_scraped = source.last_scraped_at
                if last_scraped.tzinfo is None:
                    last_scraped = last_scraped.replace(tzinfo=timezone.utc)
                frequency_td = timedelta(minutes=source.scrape_frequency_minutes)
                if now - last_scraped < frequency_td:
                    continue
            
            scrape_single_source.delay(source.id)
            dispatched += 1
            
        logger.info(f'Dispatched {dispatched} scraping tasks')
        return {'dispatched': dispatched}

@celery.task(bind=True, max_retries=3, default_retry_delay=120)
def scrape_single_source(self, source_id: int):
    """Scrape a single newspaper source."""
    app = create_app()
    with app.app_context():
        try:
            engine = ScraperEngine(source_id)
            result = engine.scrape()
            logger.info(f'Scraping source {source_id} completed: {result}')
            return result
        except Exception as exc:
            logger.error(f'Scraping source {source_id} failed: {exc}')
            raise self.retry(exc=exc)
