import logging
from typing import Optional

logger = logging.getLogger(__name__)

SEVERITY_MAP = {
    (8, 10): 'critical',
    (6, 7): 'high',
    (4, 5): 'medium',
    (2, 3): 'low',
    (1, 1): 'informational',
}

REAL_ESTATE_DISPUTE_TYPES = [
    'boundary_dispute', 'title_dispute', 'encroachment', 'partition',
    'sale_objection', 'mortgage_dispute', 'court_order'
]

def classify_severity(urgency_score: Optional[int]) -> str:
    """Map urgency score (1-10) to severity category."""
    if urgency_score is None:
        return 'medium'
        
    try:
        score = int(urgency_score)
        for (min_score, max_score), severity in SEVERITY_MAP.items():
            if min_score <= score <= max_score:
                return severity
    except (ValueError, TypeError):
        logger.warning(f"Invalid urgency score provided: {urgency_score}")
        
    return 'medium'

def is_relevant_for_real_estate(dispute_data: dict) -> bool:
    """Determine if dispute is relevant for real estate clients."""
    if not dispute_data:
        return False
        
    dispute_type = dispute_data.get('dispute_type', '')
    if dispute_type in REAL_ESTATE_DISPUTE_TYPES:
        return True
        
    return False
