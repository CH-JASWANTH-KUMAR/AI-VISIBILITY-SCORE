"""
Simple in-memory cache for query templates
Prevents regenerating same queries for same industry
"""

import hashlib
from typing import Optional, List
from datetime import datetime, timedelta

class QueryCache:
    """In-memory cache with TTL"""
    
    def __init__(self, ttl_hours: int = 24):
        self._cache = {}
        self._ttl = timedelta(hours=ttl_hours)
    
    def _make_key(self, industry: str, brand_name: str, count: int) -> str:
        """Create cache key from parameters"""
        key_str = f"{industry}:{brand_name}:{count}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, industry: str, brand_name: str, count: int) -> Optional[List[str]]:
        """Get cached queries if available and not expired"""
        key = self._make_key(industry, brand_name, count)
        
        if key in self._cache:
            queries, timestamp = self._cache[key]
            
            # Check if expired
            if datetime.now() - timestamp < self._ttl:
                return queries
            else:
                # Expired, remove
                del self._cache[key]
        
        return None
    
    def set(self, industry: str, brand_name: str, count: int, queries: List[str]):
        """Cache queries"""
        key = self._make_key(industry, brand_name, count)
        self._cache[key] = (queries, datetime.now())
    
    def clear(self):
        """Clear all cache"""
        self._cache.clear()

# Global cache instance
query_cache = QueryCache()
