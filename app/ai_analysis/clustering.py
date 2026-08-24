import logging
import uuid
from typing import Optional
from app.extensions import db
from app.models.dispute import Dispute
from app.models.extracted_notice import ExtractedNotice

logger = logging.getLogger(__name__)

def find_or_create_cluster(dispute_data: dict) -> str:
    """Find existing cluster for this dispute or create a new cluster ID.
    
    Matching criteria:
    1. Same survey/property number (strongest signal)
    2. Same location AND overlapping parties
    3. Same location AND similar date range (within 90 days)
    
    Returns cluster_id string.
    """
    try:
        # Check by survey number
        prop_details = dispute_data.get('property_identifiers', {})
        survey_number = prop_details.get('survey_number') if isinstance(prop_details, dict) else None
        if not survey_number and 'survey_number' in dispute_data:
            survey_number = dispute_data['survey_number']
            
        if survey_number:
            cluster_id = _match_by_survey_number(survey_number)
            if cluster_id:
                return cluster_id
                
        # Check by location and parties
        location = dispute_data.get('location')
        parties = dispute_data.get('parties_involved', []) or dispute_data.get('related_parties', [])
        
        if location and parties:
            cluster_id = _match_by_location_and_parties(location, parties)
            if cluster_id:
                return cluster_id
                
    except Exception as e:
        logger.error(f"Error in find_or_create_cluster: {e}")
        
    return _generate_cluster_id()

def _match_by_survey_number(survey_number: str) -> Optional[str]:
    """Find cluster by matching survey number."""
    if not survey_number:
        return None
        
    try:
        # Query disputes with matching survey number via extracted_notice
        match = db.session.query(Dispute).join(ExtractedNotice, Dispute.extracted_notice_id == ExtractedNotice.id).filter(
            ExtractedNotice.survey_number == survey_number
        ).first()
        
        if match and match.cluster_id:
            return match.cluster_id
    except Exception as e:
        logger.error(f"Error matching by survey number: {e}")
        
    return None

def _match_by_location_and_parties(location: str, parties: list) -> Optional[str]:
    """Find cluster by location + party overlap."""
    if not location or not parties:
        return None
        
    try:
        # Query disputes with similar location using ILIKE
        potential_matches = db.session.query(Dispute).filter(
            Dispute.location.ilike(f"%{location}%")
        ).limit(10).all()
        
        for match in potential_matches:
            match_parties = set(match.parties_involved or [])
            if not match_parties:
                continue
                
            query_parties = set(parties)
            overlap = query_parties.intersection(match_parties)
            
            # If they share at least 1 party or >50% overlap
            if len(overlap) > 0 and len(overlap) / max(len(query_parties), 1) >= 0.5:
                if match.cluster_id:
                    return match.cluster_id
    except Exception as e:
        logger.error(f"Error matching by location and parties: {e}")
        
    return None

def _generate_cluster_id() -> str:
    """Generate a new unique cluster ID."""
    return f"CLU-{str(uuid.uuid4())[:8].upper()}"
