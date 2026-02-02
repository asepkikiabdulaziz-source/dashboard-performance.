"""
Connection Pool Configuration
Optimizes database connection management for scalability
"""
import os
from typing import Optional
from logger import get_logger

logger = get_logger("connection_pool")

# Connection pool settings
MAX_CONNECTIONS = int(os.getenv("DB_MAX_CONNECTIONS", "20"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # 1 hour

def get_connection_pool_config() -> dict:
    """
    Get connection pool configuration for Supabase/PostgreSQL
    
    Returns:
        Dictionary with pool configuration
    """
    return {
        "max_connections": MAX_CONNECTIONS,
        "pool_timeout": POOL_TIMEOUT,
        "pool_recycle": POOL_RECYCLE,
    }


def configure_httpx_pool():
    """
    Configure HTTP connection pooling for requests library
    This helps with Supabase API calls
    """
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    # Create session with connection pooling
    session = requests.Session()
    
    # Retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    # HTTP adapter with connection pooling
    adapter = HTTPAdapter(
        pool_connections=MAX_CONNECTIONS,
        pool_maxsize=MAX_CONNECTIONS * 2,
        max_retries=retry_strategy
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    logger.info(f"HTTP connection pool configured: max_connections={MAX_CONNECTIONS}")
    return session

# Global session for reuse
_http_session = None

def get_http_session():
    """Get or create HTTP session with connection pooling"""
    global _http_session
    if _http_session is None:
        _http_session = configure_httpx_pool()
    return _http_session
