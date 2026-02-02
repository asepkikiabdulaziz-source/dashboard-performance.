"""
Zone Resolution Service
Pre-loads and caches zone mappings (ZONA_RBM, ZONA_BM) from BigQuery
Moved out of auth flow for better performance
"""
import threading
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from logger import get_logger

logger = get_logger("zone_resolution")

# Cache for zone mappings: region_name -> {zona_rbm, zona_bm}
_zone_cache: Dict[str, Dict[str, str]] = {}
_zone_cache_lock = threading.RLock()
_zone_cache_ttl = timedelta(hours=24)  # Zones don't change often
_zone_cache_time: Dict[str, datetime] = {}


def resolve_zones_for_region(region_name: str) -> Dict[str, Optional[str]]:
    """
    Resolve competition zones (ZONA_RBM, ZONA_BM) for a region.
    Uses cache first, falls back to BigQuery if needed.
    
    Args:
        region_name: Full region name (e.g., 'R06 JABODEBEK')
        
    Returns:
        Dict with 'zona_rbm' and 'zona_bm' keys
    """
    if not region_name or region_name == 'ALL':
        return {"zona_rbm": None, "zona_bm": None}
    
    # Check cache
    with _zone_cache_lock:
        if region_name in _zone_cache:
            cached_time = _zone_cache_time.get(region_name)
            if cached_time and (datetime.now() - cached_time) < _zone_cache_ttl:
                logger.debug(f"Zone cache HIT: {region_name}")
                return _zone_cache[region_name]
    
    # Cache miss - resolve from BigQuery (async/background recommended)
    try:
        from bigquery_service import get_bigquery_service
        bq = get_bigquery_service()
        
        if not bq or not bq.client:
            logger.warning("BigQuery service not available for zone resolution")
            return {"zona_rbm": None, "zona_bm": None}
        
        zone_query = f"""
        SELECT DISTINCT ZONA_RBM, ZONA_BM 
        FROM `{bq.project_id}.{bq.dataset}.rank_ass` 
        WHERE REGION = '{region_name}' 
        LIMIT 1
        """
        
        zone_df = bq.client.query(zone_query).to_dataframe()
        
        if not zone_df.empty:
            result = {
                "zona_rbm": zone_df.iloc[0].get('ZONA_RBM'),
                "zona_bm": zone_df.iloc[0].get('ZONA_BM')
            }
            
            # Cache it
            with _zone_cache_lock:
                _zone_cache[region_name] = result
                _zone_cache_time[region_name] = datetime.now()
            
            logger.info(f"Resolved zones for {region_name}: RBM={result['zona_rbm']}, BM={result['zona_bm']}")
            return result
        else:
            logger.warning(f"No zone data found for region: {region_name}")
            return {"zona_rbm": None, "zona_bm": None}
            
    except Exception as e:
        logger.error(f"Error resolving zones for {region_name}: {e}", exc_info=True)
        return {"zona_rbm": None, "zona_bm": None}


def preload_zones_for_regions(regions: list[str]):
    """
    Pre-load zone mappings for multiple regions (background task)
    
    Args:
        regions: List of region names to preload
    """
    logger.info(f"Pre-loading zones for {len(regions)} regions...")
    
    for region in regions:
        if region and region != 'ALL':
            resolve_zones_for_region(region)
    
    logger.info(f"Zone pre-loading complete: {len(_zone_cache)} regions cached")


def get_zone_cache_stats() -> Dict[str, Any]:
    """Get zone cache statistics"""
    with _zone_cache_lock:
        return {
            "cached_regions": len(_zone_cache),
            "cache_size_mb": len(_zone_cache) * 0.001  # Rough estimate
        }
