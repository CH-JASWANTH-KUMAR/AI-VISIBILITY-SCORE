"""
Perplexity Service
Production-grade Perplexity integration with error handling
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class PerplexityService:
    """
    Service for interacting with Perplexity AI models
    Supports: llama-3.1-sonar-small, llama-3.1-sonar-large, llama-3.1-sonar-huge
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('PERPLEXITY_API_KEY')
        self.available = bool(self.api_key)
        self.model = "llama-3.1-sonar-large-128k-online"
        self.base_url = "https://api.perplexity.ai"
        
        if self.available:
            logger.info("✅ Perplexity service initialized")
        else:
            logger.warning("⚠️  Perplexity API key not configured")
    
    async def query(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 800,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Query Perplexity model
        
        Args:
            prompt: User query
            model: Model name (defaults to llama-3.1-sonar-large)
            temperature: Creativity (0-2)
            max_tokens: Max response length
            
        Returns:
            Standardized response dict with citations
        """
        if not self.available:
            return self._error_response("Perplexity API key not configured")
        
        start_time = datetime.now()
        model_name = model or self.model
        
        try:
            logger.debug(f"🤖 Perplexity Query: {prompt[:100]}...")
            
            async with httpx.AsyncClient(timeout=12.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    **kwargs
                }
                
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                
                data = response.json()
                
                if 'choices' not in data or not data['choices']:
                    return self._error_response("No response from Perplexity")
                
                choice = data['choices'][0]
                content = choice['message']['content']
                
                # Extract citations if available
                citations = data.get('citations', [])
                
                # Extract token counts if available
                usage = data.get('usage', {})
                tokens = {
                    "prompt": usage.get('prompt_tokens', 0),
                    "completion": usage.get('completion_tokens', 0),
                    "total": usage.get('total_tokens', 0)
                }
                
                elapsed = (datetime.now() - start_time).total_seconds()
                result = {
                    "provider": "perplexity",
                    "model": model_name,
                    "response": content,
                    "tokens": tokens,
                    "timestamp": start_time.isoformat(),
                    "elapsed_seconds": elapsed,
                    "error": None,
                    "success": True,
                    "citations": citations  # Unique to Perplexity
                }
                
                logger.debug(f"✅ Perplexity Response ({elapsed:.2f}s, {tokens['total']} tokens, {len(citations)} citations)")
                return result
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            logger.error(f"❌ Perplexity HTTP Error: {error_msg}")
            return self._error_response(error_msg)
        except httpx.TimeoutException:
            logger.error("❌ Perplexity request timed out")
            return self._error_response("Request timeout")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            return self._error_response(f"Unexpected error: {str(e)}")
    
    def _error_response(self, error_message: str) -> Dict[str, Any]:
        """Standard error response format"""
        return {
            "provider": "perplexity",
            "model": self.model,
            "response": "",
            "tokens": {"prompt": 0, "completion": 0, "total": 0},
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": 0,
            "error": error_message,
            "success": False,
            "citations": []
        }
