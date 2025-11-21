"""
AI Service Manager
Coordinates all AI services with fallback logic and parallel execution
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from .openai_service import OpenAIService
from .gemini_service import GeminiService
from .claude_service import ClaudeService
from .perplexity_service import PerplexityService
from ..core.query_cache import get_cached_response, cache_response, get_cache_stats

logger = logging.getLogger(__name__)


class AIServiceManager:
    """
    Centralized manager for all AI services
    Features:
    - Auto-detect available models
    - Parallel query execution
    - Graceful fallback (GPT → Gemini → templates)
    - Never crash if model fails
    """
    
    def __init__(self):
        # Initialize all services
        self.openai = OpenAIService()
        self.gemini = GeminiService()
        self.claude = ClaudeService()
        self.perplexity = PerplexityService()
        
        # Track available services
        self.available_services = self._detect_available_services()
        
        logger.info(f"🚀 AI Service Manager initialized")
        logger.info(f"📊 Available models: {', '.join(self.available_services)}")
    
    def _detect_available_services(self) -> List[str]:
        """Detect which AI services are available based on API keys"""
        services = []
        if self.openai.available:
            services.append("ChatGPT-4")
        if self.gemini.available:
            services.append("Gemini-Pro")
        if self.claude.available:
            services.append("Claude-3")
        if self.perplexity.available:
            services.append("Perplexity")
        return services
    
    def get_available_models(self) -> List[str]:
        """Return list of available model names"""
        return self.available_services.copy()
    
    async def query_all(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 800
    ) -> Dict[str, Dict[str, Any]]:
        """
        Query all available models in parallel with caching
        
        Args:
            prompt: User query
            temperature: Creativity setting
            max_tokens: Max response length
            
        Returns:
            Dict mapping model name to response
        """
        tasks = []
        model_names = []
        
        # Check cache first for each model
        response_map = {}
        
        if self.openai.available:
            cached = get_cached_response(prompt, "ChatGPT-4")
            if cached:
                logger.info(f"✅ Cache HIT for ChatGPT-4")
                response_map["ChatGPT-4"] = cached
            else:
                tasks.append(self.openai.query(prompt, temperature=temperature, max_tokens=max_tokens))
                model_names.append("ChatGPT-4")
        
        if self.gemini.available:
            cached = get_cached_response(prompt, "Gemini-Pro")
            if cached:
                logger.info(f"✅ Cache HIT for Gemini-Pro")
                response_map["Gemini-Pro"] = cached
            else:
                tasks.append(self.gemini.query(prompt, temperature=temperature, max_tokens=max_tokens))
                model_names.append("Gemini-Pro")
        
        if self.claude.available:
            cached = get_cached_response(prompt, "Claude-3")
            if cached:
                logger.info(f"✅ Cache HIT for Claude-3")
                response_map["Claude-3"] = cached
            else:
                tasks.append(self.claude.query(prompt, temperature=temperature, max_tokens=max_tokens))
                model_names.append("Claude-3")
        
        if self.perplexity.available:
            cached = get_cached_response(prompt, "Perplexity")
            if cached:
                logger.info(f"✅ Cache HIT for Perplexity")
                response_map["Perplexity"] = cached
            else:
                tasks.append(self.perplexity.query(prompt, temperature=temperature, max_tokens=max_tokens))
                model_names.append("Perplexity")
        
        if not tasks and not response_map:
            logger.error("❌ No AI services available")
            return {}
        
        # Execute only non-cached queries in parallel
        if tasks:
            logger.info(f"🔄 Querying {len(tasks)} models in parallel (+ {len(response_map)} from cache)...")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Map results to model names and cache
            for model_name, result in zip(model_names, results):
                if isinstance(result, Exception):
                    logger.error(f"❌ {model_name} raised exception: {result}")
                    response_map[model_name] = {
                        "provider": model_name.lower().split('-')[0],
                        "model": model_name,
                        "response": "",
                        "error": str(result),
                        "success": False
                    }
                else:
                    # Cache successful responses
                    if result.get('success'):
                        cache_response(prompt, model_name, result)
                        logger.info(f"💾 Cached response for {model_name}")
                    response_map[model_name] = result
        
        return response_map
    
    async def query_with_fallback(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 800
    ) -> Dict[str, Any]:
        """
        Query with automatic fallback: GPT-4 → Gemini → Claude → Perplexity
        
        Args:
            prompt: User query
            temperature: Creativity setting
            max_tokens: Max response length
            
        Returns:
            First successful response
        """
        # Try OpenAI first (highest quality)
        if self.openai.available:
            result = await self.openai.query(prompt, temperature=temperature, max_tokens=max_tokens)
            if result['success']:
                logger.info("✅ Used OpenAI GPT-4")
                return result
            logger.warning("⚠️  OpenAI failed, trying Gemini...")
        
        # Fallback to Gemini
        if self.gemini.available:
            result = await self.gemini.query(prompt, temperature=temperature, max_tokens=max_tokens)
            if result['success']:
                logger.info("✅ Used Gemini (fallback)")
                return result
            logger.warning("⚠️  Gemini failed, trying Claude...")
        
        # Fallback to Claude
        if self.claude.available:
            result = await self.claude.query(prompt, temperature=temperature, max_tokens=max_tokens)
            if result['success']:
                logger.info("✅ Used Claude (fallback)")
                return result
            logger.warning("⚠️  Claude failed, trying Perplexity...")
        
        # Final fallback to Perplexity
        if self.perplexity.available:
            result = await self.perplexity.query(prompt, temperature=temperature, max_tokens=max_tokens)
            if result['success']:
                logger.info("✅ Used Perplexity (fallback)")
                return result
        
        # All models failed
        logger.error("❌ All AI models failed")
        return {
            "provider": "none",
            "model": "none",
            "response": "",
            "error": "All AI models failed or unavailable",
            "success": False
        }
    
    async def classify_industry_with_fallback(
        self,
        brand_name: str,
        website_text: str
    ) -> str:
        """
        Classify industry with fallback logic
        
        Priority: Gemini → OpenAI → "Other"
        """
        # Try Gemini first (fast and good for classification)
        if self.gemini.available:
            result = await self.gemini.classify_industry(brand_name, website_text)
            if result != "Other":
                logger.info(f"✅ Industry classified via Gemini: {result}")
                return result
        
        # Fallback to OpenAI
        if self.openai.available:
            result = await self.openai.classify_industry(brand_name, website_text)
            logger.info(f"✅ Industry classified via OpenAI: {result}")
            return result
        
        # Ultimate fallback
        logger.warning("⚠️  No AI model available for industry classification")
        return "Other"
    
    async def generate_queries_batch(
        self,
        industry: str,
        brand_name: str,
        count: int = 30
    ) -> List[str]:
        """
        Generate queries using OpenAI (best for creative generation)
        Falls back to empty list if unavailable
        """
        if not self.openai.available:
            logger.warning("⚠️  OpenAI not available for query generation")
            return []
        
        return await self.openai.generate_queries(industry, brand_name, count)
