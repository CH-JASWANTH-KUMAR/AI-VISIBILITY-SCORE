"""
OpenAI GPT Service
Production-grade OpenAI integration with error handling
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any
from openai import AsyncOpenAI, OpenAIError
from datetime import datetime

logger = logging.getLogger(__name__)


class OpenAIService:
    """
    Service for interacting with OpenAI GPT models
    Supports: GPT-4, GPT-4-Turbo, GPT-3.5-Turbo
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None
        self.available = bool(self.client)
        self.model = "gpt-4-turbo-preview"
        
        if self.available:
            logger.info("✅ OpenAI service initialized")
        else:
            logger.warning("⚠️  OpenAI API key not configured")
    
    async def query(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 800,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Query OpenAI model
        
        Args:
            prompt: User query
            model: Model name (defaults to gpt-4-turbo-preview)
            temperature: Creativity (0-2)
            max_tokens: Max response length
            
        Returns:
            Standardized response dict
        """
        if not self.available:
            return self._error_response("OpenAI API key not configured")
        
        start_time = datetime.now()
        model_name = model or self.model
        
        try:
            logger.debug(f"🤖 OpenAI Query: {prompt[:100]}...")
            
            # Add timeout to prevent hanging
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                ),
                timeout=15.0  # 15 second timeout
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            result = {
                "provider": "openai",
                "model": model_name,
                "response": response.choices[0].message.content,
                "tokens": {
                    "prompt": response.usage.prompt_tokens,
                    "completion": response.usage.completion_tokens,
                    "total": response.usage.total_tokens
                },
                "timestamp": start_time.isoformat(),
                "elapsed_seconds": elapsed,
                "error": None,
                "success": True
            }
            
            logger.debug(f"✅ OpenAI Response ({elapsed:.2f}s, {result['tokens']['total']} tokens)")
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"⏱️  OpenAI timeout (>15s)")
            return self._error_response("Request timeout")
        except OpenAIError as e:
            logger.error(f"❌ OpenAI Error: {str(e)}")
            return self._error_response(f"OpenAI API error: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            return self._error_response(f"Unexpected error: {str(e)}")
    
    async def generate_queries(
        self,
        industry: str,
        brand_name: str,
        count: int = 30
    ) -> list[str]:
        """Generate search queries using GPT-4"""
        if not self.available:
            return []
        
        prompt = f"""Generate {count} diverse search queries that consumers would ask when looking for products/services in the {industry} industry.

Focus on:
- Product comparisons ("X vs Y")
- Best-of lists ("best X for Y")
- Reviews and recommendations
- Buying guides ("how to choose")
- Budget-focused queries ("most affordable")
- Specific use cases

Consider the brand: {brand_name}

Return as a numbered list, one query per line."""
        
        try:
            result = await self.query(prompt, temperature=0.8, max_tokens=1000)
            if not result['success']:
                return []
            
            text = result['response']
            queries = []
            for line in text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith(('-', '•', '*'))):
                    query = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                    if query:
                        queries.append(query)
            
            logger.info(f"📝 Generated {len(queries)} queries via OpenAI")
            return queries
        except Exception as e:
            logger.error(f"❌ Query generation failed: {e}")
            return []
    
    async def classify_industry(self, brand_name: str, website_text: str) -> str:
        """Classify industry using GPT-4"""
        if not self.available:
            return "Other"
        
        prompt = f"""Analyze this brand and website content to classify the industry.

Brand: {brand_name}
Website content: {website_text}

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
                return result['response'].strip()
            return "Other"
        except Exception:
            return "Other"
    
    def _error_response(self, error_message: str) -> Dict[str, Any]:
        """Standard error response format"""
        return {
            "provider": "openai",
            "model": self.model,
            "response": "",
            "tokens": {"prompt": 0, "completion": 0, "total": 0},
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": 0,
            "error": error_message,
            "success": False
        }
