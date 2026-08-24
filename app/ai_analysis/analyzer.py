import json
import logging
import time
import httpx
from typing import Optional
from app.config import Config
from app.ai_analysis.prompts import SYSTEM_PROMPT, EXTRACTION_PROMPT

logger = logging.getLogger(__name__)

class DisputeAnalyzer:
    """Analyzes land dispute notices using LLM API."""
    
    def __init__(self):
        self.api_key = Config.LLM_API_KEY
        self.provider = Config.LLM_PROVIDER  # 'openai' or 'anthropic'
        self.model = Config.LLM_MODEL
        self.max_retries = Config.MAX_RETRIES
        self.timeout = 60.0
    
    def analyze(self, text: str, source_name: str = '', publish_date: str = '') -> dict:
        """Run full analysis on notice text.
        
        Returns dict with dispute_type, location, parties_involved,
        urgency_score, status, summary, etc.
        Returns partial result on failure.
        """
        user_prompt = EXTRACTION_PROMPT.format(
            source_name=source_name,
            publish_date=publish_date,
            notice_text=text
        )
        
        try:
            if self.provider == 'openai':
                return self._call_openai(SYSTEM_PROMPT, user_prompt)
            elif self.provider == 'anthropic':
                return self._call_anthropic(SYSTEM_PROMPT, user_prompt)
            else:
                logger.error(f"Unsupported LLM provider: {self.provider}")
                return {}
        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            return {}
    
    def _call_openai(self, system_prompt: str, user_prompt: str) -> dict:
        """Call OpenAI API with JSON mode."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(url, headers=headers, json=data)
                    
                if response.status_code in [429, 500, 502, 503]:
                    logger.warning(f"Retryable error from OpenAI: {response.status_code}")
                    time.sleep(2 ** attempt)
                    continue
                    
                response.raise_for_status()
                response_json = response.json()
                content = response_json['choices'][0]['message']['content']
                return self._parse_response(content)
                
            except httpx.RequestError as e:
                logger.error(f"OpenAI request error: {e}")
                if attempt == self.max_retries - 1:
                    break
                time.sleep(2 ** attempt)
                
        return {}
    
    def _call_anthropic(self, system_prompt: str, user_prompt: str) -> dict:
        """Call Anthropic Claude API."""
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        data = {
            "model": self.model,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 4096
        }
        
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(url, headers=headers, json=data)
                    
                if response.status_code in [429, 500, 502, 503]:
                    logger.warning(f"Retryable error from Anthropic: {response.status_code}")
                    time.sleep(2 ** attempt)
                    continue
                    
                response.raise_for_status()
                response_json = response.json()
                content = response_json['content'][0]['text']
                return self._parse_response(content)
                
            except httpx.RequestError as e:
                logger.error(f"Anthropic request error: {e}")
                if attempt == self.max_retries - 1:
                    break
                time.sleep(2 ** attempt)
                
        return {}
    
    def _parse_response(self, raw_response: str) -> dict:
        """Parse LLM JSON response with fallback handling."""
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            # Fallback: Try to extract from markdown code blocks
            logger.warning("Failed to parse JSON directly. Attempting to extract from markdown.")
            try:
                import re
                match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_response, re.DOTALL)
                if match:
                    return json.loads(match.group(1))
            except Exception as e:
                logger.error(f"Failed to extract JSON from markdown: {e}")
            return {}
