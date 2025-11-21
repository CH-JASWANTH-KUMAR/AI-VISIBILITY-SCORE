"""
Anthropic Claude Service
Production-grade Claude integration with error handling
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any
from anthropic import AsyncAnthropic, APIError
from datetime import datetime

logger = logging.getLogger(__name__)


class ClaudeService:
    """
    Service for interacting with Anthropic Claude models
    Supports: claude-3-opus, claude-3-sonnet, claude-3-haiku
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = AsyncAnthropic(api_key=self.api_key) if self.api_key else None
        self.available = bool(self.client)
        self.model = "claude-3-5-sonnet-20241022"
        
        if self.available:
            logger.info("✅ Claude service initialized")
        else:
            logger.warning("⚠️  Anthropic API key not configured")
    
    async def query(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 800,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Query Claude model
        
        Args:
            prompt: User query
            model: Model name (defaults to claude-3-5-sonnet)
            temperature: Creativity (0-1)
            max_tokens: Max response length
            
        Returns:
            Standardized response dict
        """
        if not self.available:
            return self._error_response("Anthropic API key not configured")
        
        start_time = datetime.now()
        model_name = model or self.model
        
        try:
            logger.debug(f"🤖 Claude Query: {prompt[:100]}...")
            
            # Add timeout
            response = await asyncio.wait_for(
                self.client.messages.create(
                    model=model_name,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}],
                    **kwargs
                ),
                timeout=15.0
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            result = {
                "provider": "claude",
                "model": model_name,
                "response": response.content[0].text,
                "tokens": {
                    "prompt": response.usage.input_tokens,
                    "completion": response.usage.output_tokens,
                    "total": response.usage.input_tokens + response.usage.output_tokens
                },
                "timestamp": start_time.isoformat(),
                "elapsed_seconds": elapsed,
                "error": None,
                "success": True
            }
            
            logger.debug(f"✅ Claude Response ({elapsed:.2f}s, {result['tokens']['total']} tokens)")
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"⏱️  Claude timeout (>15s)")
            return self._error_response("Request timeout")
        except APIError as e:
            logger.error(f"❌ Claude API Error: {str(e)}")
            return self._error_response(f"Claude API error: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            return self._error_response(f"Unexpected error: {str(e)}")
    
    def _error_response(self, error_message: str) -> Dict[str, Any]:
        """Standard error response format"""
        return {
            "provider": "claude",
            "model": self.model,
            "response": "",
            "tokens": {"prompt": 0, "completion": 0, "total": 0},
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": 0,
            "error": error_message,
            "success": False
        }
