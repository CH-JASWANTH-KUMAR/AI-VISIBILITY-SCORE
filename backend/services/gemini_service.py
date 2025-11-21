"""
Google Gemini Service
Production-grade Gemini integration with error handling
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Service for interacting with Google Gemini models
    Supports: gemini-pro, gemini-1.5-pro
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.available = bool(self.api_key)
        self.model = "gemini-pro"  # Using stable gemini-pro model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        
        if self.available:
            logger.info("✅ Gemini service initialized")
        else:
            logger.warning("⚠️  Google API key not configured")
    
    async def query(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 800,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Query Gemini model
        
        Args:
            prompt: User query
            model: Model name (defaults to gemini-1.5-pro)
            temperature: Creativity (0-2)
            max_tokens: Max response length
            
        Returns:
            Standardized response dict
        """
        if not self.available:
            return self._error_response("Google API key not configured")
        
        start_time = datetime.now()
        model_name = model or self.model
        
        try:
            logger.debug(f"🤖 Gemini Query: {prompt[:100]}...")
            
            # Reduce timeout for faster failure detection
            async with httpx.AsyncClient(timeout=12.0) as client:
                url = f"{self.base_url}/{model_name}:generateContent?key={self.api_key}"
                
                payload = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "temperature": temperature,
                        "maxOutputTokens": max_tokens,
                        "topP": 0.95,
                        "topK": 40
                    }
                }
                
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                data = response.json()
                
                if 'candidates' not in data or not data['candidates']:
                    return self._error_response("No response from Gemini")
                
                candidate = data['candidates'][0]
                if candidate.get('finishReason') != 'STOP':
                    finish_reason = candidate.get('finishReason', 'UNKNOWN')
                    logger.warning(f"⚠️  Gemini finished with reason: {finish_reason}")
                
                content = candidate['content']['parts'][0]['text']
                
                # Extract token counts if available
                usage = data.get('usageMetadata', {})
                tokens = {
                    "prompt": usage.get('promptTokenCount', 0),
                    "completion": usage.get('candidatesTokenCount', 0),
                    "total": usage.get('totalTokenCount', 0)
                }
                
                elapsed = (datetime.now() - start_time).total_seconds()
                result = {
                    "provider": "gemini",
                    "model": model_name,
                    "response": content,
                    "tokens": tokens,
                    "timestamp": start_time.isoformat(),
                    "elapsed_seconds": elapsed,
                    "error": None,
                    "success": True
                }
                
                logger.debug(f"✅ Gemini Response ({elapsed:.2f}s, {tokens['total']} tokens)")
                return result
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"❌ Gemini HTTP Error: {error_msg}")
            return self._error_response(error_msg)
        except httpx.TimeoutException:
            logger.error("❌ Gemini request timed out")
            return self._error_response("Request timeout")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            return self._error_response(f"Unexpected error: {str(e)}")
    
    async def classify_industry(self, brand_name: str, website_text: str) -> str:
        """Classify industry using Gemini"""
        if not self.available:
            return "Other"
        
        prompt = f"""Analyze this brand and website content to classify the industry.

Brand: {brand_name}
Website content: {website_text[:2000]}

Choose ONE industry from:
- Meal Kits & Food Delivery
- E-commerce & Retail
- SaaS & Software
- Health & Wellness
- Travel & Hospitality
- Financial Services
- Education & E-learning
- Startup Incubators & Accelerators
- Marketing & Advertising
- Real Estate
- Automotive & EV
- Other

Respond with ONLY the industry name, nothing else."""
        
        try:
            result = await self.query(prompt, temperature=0.1, max_tokens=50)
            if result['success']:
                industry = result['response'].strip()
                # Clean up common formatting
                industry = industry.replace('*', '').replace('#', '').strip()
                return industry
            return "Other"
        except Exception as e:
            logger.error(f"❌ Industry classification failed: {e}")
            return "Other"
    
    def _error_response(self, error_message: str) -> Dict[str, Any]:
        """Standard error response format"""
        return {
            "provider": "gemini",
            "model": self.model,
            "response": "",
            "tokens": {"prompt": 0, "completion": 0, "total": 0},
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": 0,
            "error": error_message,
            "success": False
        }
