import logging
import requests
import tempfile
import os
from typing import List, Dict, Any
from app.extensions import celery, db
from app.models.raw_article import RawArticle
from app.models.extracted_notice import ExtractedNotice
from app.ocr.pipeline import ocr_image, ocr_pdf
from app.ocr.extractor import extract_notice_fields
from app import create_app

logger = logging.getLogger(__name__)

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def process_ocr_queue(self):
    """Pick unprocessed raw articles with images/PDFs and run OCR."""
    app = create_app()
    with app.app_context():
        articles = RawArticle.query.filter(
            RawArticle.scrape_status.in_(['pending', 'scraped'])
        ).all()
        
        dispatched = 0
        for article in articles:
            has_media = False
            if article.image_urls and len(article.image_urls) > 0:
                has_media = True
            if article.pdf_urls and len(article.pdf_urls) > 0:
                has_media = True
                
            if has_media:
                # Check if ExtractedNotice already exists
                existing = ExtractedNotice.query.filter_by(raw_article_id=article.id).first()
                if not existing:
                    ocr_single_article.delay(article.id)
                    dispatched += 1
        
        logger.info(f'Dispatched {dispatched} OCR tasks')
        return {'dispatched': dispatched}

@celery.task(bind=True, max_retries=3, default_retry_delay=120)
def ocr_single_article(self, article_id: int):
    """OCR a single article's images/PDFs."""
    app = create_app()
    with app.app_context():
        try:
            article = RawArticle.query.get(article_id)
            if not article:
                logger.error(f"Article {article_id} not found for OCR")
                return
            
            combined_text = []
            
            # Download and OCR images
            if article.image_urls:
                for img_url in article.image_urls:
                    try:
                        resp = requests.get(img_url, timeout=30)
                        resp.raise_for_status()
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                            tmp.write(resp.content)
                            tmp_path = tmp.name
                        text = ocr_image(tmp_path)
                        if text:
                            combined_text.append(text)
                        os.unlink(tmp_path)
                    except Exception as e:
                        logger.error(f"Error processing image {img_url}: {e}")
            
            # Download and OCR PDFs
            pdf_urls = article.pdf_urls or []
            for pdf_url in pdf_urls:
                try:
                    resp = requests.get(pdf_url, timeout=30)
                    resp.raise_for_status()
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(resp.content)
                        tmp_path = tmp.name
                    text = ocr_pdf(tmp_path)
                    if text:
                        combined_text.append(text)
                    os.unlink(tmp_path)
                except Exception as e:
                    logger.error(f"Error processing PDF {pdf_url}: {e}")
                    
            full_text = "\n\n".join(combined_text)
            if not full_text and article.raw_text:
                full_text = article.raw_text
                
            fields = extract_notice_fields(full_text)
            
            notice = ExtractedNotice(
                raw_article_id=article.id,
                ocr_text=full_text,
                notice_type=fields.get('notice_type', 'dispute'),
                property_number=fields.get('property_number'),
                survey_number=fields.get('survey_number'),
                disputing_parties=fields.get('disputing_parties', []),
                location=fields.get('location'),
                issuing_authority=fields.get('issuing_authority'),
                ocr_confidence_scores=fields.get('ocr_confidence_scores', {}),
                needs_manual_review=fields.get('needs_manual_review', False),
                processing_status='processed'
            )
            db.session.add(notice)
            article.scrape_status = 'scraped'
            db.session.commit()
            
            logger.info(f"Completed OCR for article {article_id}")
            return {'article_id': article_id, 'notice_id': notice.id}
            
        except Exception as exc:
            db.session.rollback()
            logger.error(f'OCR for article {article_id} failed: {exc}')
            raise self.retry(exc=exc)
