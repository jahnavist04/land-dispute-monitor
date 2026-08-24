import hmac
import hashlib
import json
import logging
import httpx
from typing import Optional
from flask import current_app

logger = logging.getLogger(__name__)

def compute_signature(payload: str, secret_key: str) -> str:
    """Compute HMAC-SHA256 signature for webhook payload."""
    mac = hmac.new(
        secret_key.encode('utf-8'),
        msg=payload.encode('utf-8'),
        digestmod=hashlib.sha256
    )
    return mac.hexdigest()

def dispatch_webhook(url: str, payload: dict, secret_key: str, timeout: int = 10) -> dict:
    """Send a signed webhook payload to a URL.
    
    Signs payload with HMAC-SHA256 using the secret_key.
    Returns dict with status, response_code, error.
    """
    try:
        payload_str = json.dumps(payload)
        signature = compute_signature(payload_str, secret_key)
        
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Signature': signature
        }
        
        response = httpx.post(
            url, 
            content=payload_str,
            headers=headers,
            timeout=timeout
        )
        
        result = {
            'status': 'success' if response.is_success else 'failed',
            'response_code': response.status_code,
            'error': None
        }
        if not response.is_success:
            logger.warning(f"Webhook to {url} failed with status {response.status_code}")
            
        return result
        
    except httpx.TimeoutException:
        logger.error(f"Webhook to {url} timed out")
        return {
            'status': 'error',
            'response_code': None,
            'error': 'timeout'
        }
    except Exception as e:
        logger.error(f"Error dispatching webhook to {url}: {str(e)}")
        return {
            'status': 'error',
            'response_code': None,
            'error': str(e)
        }
