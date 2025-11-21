"""
In-Memory Query Cache for Performance Optimization
Avoids duplicate API calls for similar queries
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import json


class QueryCache:
    """
    Simple in-memory cache for LLM responses
    Features:
    - TTL (Time To Live) expiration
    - Query normalization
    - Memory-efficient storage
    - No external dependencies (no Redis needed)
    """
    
    def __init__(self, ttl_hours: int = 24):
        """
        Args:
            ttl_hours: How long cached responses stay valid
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = timedelta(hours=ttl_hours)
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query to avoid near-duplicates"""
        # Convert to lowercase, remove extra spaces
        normalized = ' '.join(query.lower().strip().split())
        return normalized
    
    def _generate_key(self, query: str, model: str) -> str:
        """Generate unique cache key"""
        normalized = self._normalize_query(query)
        key_string = f"{model}:{normalized}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, query: str, model: str) -> Optional[Dict[str, Any]]:
        """
        Get cached response if available and not expired
        
        Args:
            query: User query text
            model: AI model name (e.g., "ChatGPT-4")
        
        Returns:
            Cached response dict or None if not found/expired
        """
        key = self._generate_key(query, model)
        
        if key not in self.cache:
            return None
        
        cached = self.cache[key]
        
        # Check expiration
        if datetime.now() > cached['expires_at']:
            del self.cache[key]
            return None
        
        return cached['response']
    
    def set(self, query: str, model: str, response: Dict[str, Any]):
        """
        Store response in cache
        
        Args:
            query: User query text
            model: AI model name
            response: LLM response dict (must include 'response' key)
        """
        key = self._generate_key(query, model)
        
        self.cache[key] = {
            'response': response,
            'cached_at': datetime.now(),
            'expires_at': datetime.now() + self.ttl,
            'original_query': query[:100]  # Store truncated for debugging
        }
    
    def clear(self):
        """Clear entire cache"""
        self.cache.clear()
    
    def cleanup_expired(self):
        """Remove expired entries (memory optimization)"""
        now = datetime.now()
        expired_keys = [
            key for key, value in self.cache.items()
            if now > value['expires_at']
        ]
        for key in expired_keys:
            del self.cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        now = datetime.now()
        active = sum(1 for v in self.cache.values() if now <= v['expires_at'])
        expired = len(self.cache) - active
        
        return {
            'total_entries': len(self.cache),
            'active_entries': active,
            'expired_entries': expired,
            'ttl_hours': self.ttl.total_seconds() / 3600,
            'memory_approx_kb': len(str(self.cache)) / 1024
        }


# Global cache instance (shared across all workers)
query_cache = QueryCache(ttl_hours=24)


# Convenience functions
def get_cached_response(query: str, model: str) -> Optional[Dict[str, Any]]:
    """Get cached response if available"""
    return query_cache.get(query, model)


def cache_response(query: str, model: str, response: Dict[str, Any]):
    """Cache LLM response"""
    query_cache.set(query, model, response)


def clear_cache():
    """Clear all cached responses"""
    query_cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    return query_cache.get_stats()
