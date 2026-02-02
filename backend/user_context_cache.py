"""
User Context Caching System
Provides high-performance caching for user slot context resolution
Supports both in-memory and Redis backends for scalability
"""
import threading
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from logger import get_logger

logger = get_logger("user_context_cache")

# Cache storage
_user_context_cache: Dict[str, tuple] = {}  # email -> (context_data, cached_time)
_cache_lock = threading.RLock()
_cache_ttl = timedelta(minutes=15)  # TTL for user context

# Redis support (optional, for distributed caching)
_redis_client = None
_use_redis = False


def init_redis(redis_url: Optional[str] = None):
    """
    Initialize Redis client for distributed caching (optional)
    
    Args:
        redis_url: Redis connection URL (e.g., 'redis://localhost:6379')
                   If None, uses in-memory cache
    """
    global _redis_client, _use_redis
    
    if not redis_url:
        logger.info("Using in-memory cache for user context")
        return
    
    try:
        import redis
        _redis_client = redis.from_url(redis_url, decode_responses=True)
        # Test connection
        _redis_client.ping()
        _use_redis = True
        logger.info(f"✅ Redis cache initialized: {redis_url}")
    except ImportError:
        logger.warning("Redis not installed, falling back to in-memory cache")
        _use_redis = False
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}, falling back to in-memory cache")
        _use_redis = False


def get_cached_user_context(email: str) -> Optional[Dict[str, Any]]:
    """
    Get cached user context if available and not expired
    
    Args:
        email: User email address
        
    Returns:
        Cached context dict or None if not found/expired
    """
    if _use_redis and _redis_client:
        try:
            cache_key = f"user_context:{email}"
            cached_json = _redis_client.get(cache_key)
            if cached_json:
                import json
                cached_data = json.loads(cached_json)
                logger.debug(f"Cache HIT (Redis): {email}")
                return cached_data
            logger.debug(f"Cache MISS (Redis): {email}")
            return None
        except Exception as e:
            logger.error(f"Redis cache read error: {e}, falling back to memory")
    
    # In-memory cache
    with _cache_lock:
        if email in _user_context_cache:
            cached_data, cached_time = _user_context_cache[email]
            if datetime.now() - cached_time < _cache_ttl:
                logger.debug(f"Cache HIT (Memory): {email}")
                return cached_data
            else:
                # Expired, remove it
                del _user_context_cache[email]
                logger.debug(f"Cache EXPIRED: {email}")
        
        logger.debug(f"Cache MISS (Memory): {email}")
        return None


def set_cached_user_context(email: str, context: Dict[str, Any]):
    """
    Cache user context with TTL
    
    Args:
        email: User email address
        context: User context dictionary
    """
    if _use_redis and _redis_client:
        try:
            cache_key = f"user_context:{email}"
            import json
            _redis_client.setex(
                cache_key,
                int(_cache_ttl.total_seconds()),
                json.dumps(context)
            )
            logger.debug(f"Cached (Redis): {email}")
            return
        except Exception as e:
            logger.error(f"Redis cache write error: {e}, falling back to memory")
    
    # In-memory cache
    with _cache_lock:
        _user_context_cache[email] = (context, datetime.now())
        logger.debug(f"Cached (Memory): {email}")


def invalidate_user_context(email: str):
    """
    Invalidate cached user context (e.g., when assignment changes)
    
    Args:
        email: User email address
    """
    if _use_redis and _redis_client:
        try:
            cache_key = f"user_context:{email}"
            _redis_client.delete(cache_key)
            logger.info(f"Invalidated cache (Redis): {email}")
        except Exception as e:
            logger.error(f"Redis cache invalidation error: {e}")
    
    # In-memory cache
    with _cache_lock:
        if email in _user_context_cache:
            del _user_context_cache[email]
            logger.info(f"Invalidated cache (Memory): {email}")


def clear_all_cache():
    """Clear all cached user contexts (use with caution)"""
    if _use_redis and _redis_client:
        try:
            # Delete all keys matching pattern
            keys = _redis_client.keys("user_context:*")
            if keys:
                _redis_client.delete(*keys)
            logger.info(f"Cleared Redis cache: {len(keys)} entries")
        except Exception as e:
            logger.error(f"Redis cache clear error: {e}")
    
    # In-memory cache
    with _cache_lock:
        count = len(_user_context_cache)
        _user_context_cache.clear()
        logger.info(f"Cleared memory cache: {count} entries")


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics for monitoring"""
    stats = {
        "backend": "redis" if _use_redis else "memory",
        "memory_entries": 0,
        "memory_size_mb": 0
    }
    
    if _use_redis and _redis_client:
        try:
            keys = _redis_client.keys("user_context:*")
            stats["redis_entries"] = len(keys)
        except:
            stats["redis_entries"] = 0
    
    with _cache_lock:
        stats["memory_entries"] = len(_user_context_cache)
        # Rough size estimate (1KB per entry)
        stats["memory_size_mb"] = len(_user_context_cache) * 0.001
    
    return stats
