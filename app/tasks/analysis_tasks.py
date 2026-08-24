import logging
from datetime import datetime, timedelta, timezone
from app.extensions import celery, db
from app.models.extracted_notice import ExtractedNotice
from app.models.dispute import Dispute
from app.ai_analysis.analyzer import DisputeAnalyzer
from app.ai_analysis.clustering import find_or_create_cluster
from app import create_app

logger = logging.getLogger(__name__)

@celery.task(bind=True, max_retries=3, default_retry_delay=120)
def analyze_queue(self):
    """Pick unanalyzed extracted notices and run AI analysis."""
    app = create_app()
    with app.app_context():
        # ExtractedNotice where processing_status='processed' and no dispute exists
        notices = ExtractedNotice.query.filter_by(processing_status='processed').all()
        dispatched = 0
        for notice in notices:
            # check if dispute exists
            existing = Dispute.query.filter_by(extracted_notice_id=notice.id).first()
            if not existing:
                analyze_single_notice.delay(notice.id)
                dispatched += 1
                
        logger.info(f'Dispatched {dispatched} analysis tasks')
        return {'dispatched': dispatched}

@celery.task(bind=True, max_retries=3, default_retry_delay=180)
def analyze_single_notice(self, notice_id: int):
    """Run AI analysis on a single extracted notice."""
    app = create_app()
    with app.app_context():
        try:
            notice = ExtractedNotice.query.get(notice_id)
            if not notice:
                logger.error(f"Notice {notice_id} not found")
                return
                
            article = notice.raw_article
            text = f"{article.raw_text or ''}\n\n{notice.ocr_text or ''}"
            
            source_name = article.source.name if article.source else "Unknown Source"
            publish_date = article.publish_date or datetime.now(timezone.utc)
            
            analyzer = DisputeAnalyzer()
            analysis_result = analyzer.analyze(text, source_name, publish_date)
            
            # Simple severity classification if not provided
            severity = analysis_result.get('severity', 'medium')
            
            # Cluster ID via clustering logic
            cluster_id = find_or_create_cluster(analysis_result)
                
            dispute = Dispute(
                extracted_notice_id=notice.id,
                cluster_id=cluster_id,
                summary=analysis_result.get('summary', ''),
                dispute_type=analysis_result.get('dispute_type', notice.notice_type or 'General Dispute'),
                urgency_score=analysis_result.get('urgency_score', 5),
                severity=severity,
                location=analysis_result.get('location', notice.location or ''),
                parties_involved=analysis_result.get('related_parties', notice.disputing_parties or []),
                raw_llm_response=analysis_result,
                status='active'
            )
            db.session.add(dispute)
            db.session.commit()
            
            logger.info(f"Successfully analyzed notice {notice_id} -> Dispute {dispute.id}")
            return {'dispute_id': dispute.id}
            
        except Exception as exc:
            db.session.rollback()
            logger.error(f"Analysis failed for notice {notice_id}: {exc}")
            raise self.retry(exc=exc)

@celery.task
def recluster_disputes():
    """Periodic re-clustering to catch late-arriving related notices."""
    app = create_app()
    with app.app_context():
        # Get disputes from last 30 days
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        disputes = Dispute.query.filter(
            (Dispute.cluster_id == None) | 
            (Dispute.created_at >= thirty_days_ago)
        ).all()
        
        re_clustered = 0
        for dispute in disputes:
            if dispute.raw_llm_response:
                new_cluster_id = find_or_create_cluster(dispute.raw_llm_response)
                if new_cluster_id and new_cluster_id != dispute.cluster_id:
                    dispute.cluster_id = new_cluster_id
                    re_clustered += 1
                    
        db.session.commit()
        logger.info(f"Re-clustered {re_clustered} out of {len(disputes)} disputes")
        return {'processed': len(disputes), 're_clustered': re_clustered}
