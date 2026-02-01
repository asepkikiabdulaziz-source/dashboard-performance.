"""
Smart caching system for leaderboard data.
- Loads ALL data from BigQuery once
- Filters in-memory for fast responses
- Auto-refreshes when cutoff_date changes
"""
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class LeaderboardCache:
    """
    Intelligent cache for leaderboard data.
    Uses RLock and reference swapping to avoid deadlocks.
    """
    
    def __init__(self, bigquery_service):
        self.bigquery_service = bigquery_service
        self._lock = threading.RLock()
        
        # Cache storage (Atomic reference swapping targets)
        self._all_data: List[Dict[str, Any]] = []
        self._cutoff_date: Optional[str] = None
        self._last_refresh: Optional[datetime] = None
        
        # Warm cache in background
        logger.info("🚀 Initializing LeaderboardCache background warming...")
        thread = threading.Thread(target=self._refresh_cache)
        thread.daemon = True
        thread.start()
    
    def _refresh_cache(self):
        """Reload all data from BigQuery with minimal lock hold time"""
        try:
            logger.info("🔄 Refreshing leaderboard cache from BigQuery...")
            start_time = datetime.now()
            
            # 1. Fetch data OUTSIDE lock (Slow part)
            cutoff_date = self.bigquery_service.get_cutoff_date()
            all_data_df = self.bigquery_service.get_leaderboard(
                region="ALL",
                division=None,
                limit=None
            )
            all_data = all_data_df.to_dict(orient='records')
            
            # 2. Update status and data INSIDE lock (Fast part)
            with self._lock:
                self._all_data = all_data
                self._cutoff_date = cutoff_date
                self._last_refresh = datetime.now()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ CACHE REFRESHED: {len(all_data)} records in {elapsed:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Cache refresh failed: {e}")
            import traceback
            traceback.print_exc()

    def _check_and_refresh(self):
        """Rate-limited check for updates"""
        try:
            # Check every 15 minutes
            now = datetime.now()
            with self._lock:
                last = self._last_refresh
            
            if last and (now - last).total_seconds() < 900:
                return False

            # Trigger background check
            thread = threading.Thread(target=self._run_background_check)
            thread.daemon = True
            thread.start()
            return True
        except Exception as e:
            logger.error(f"Error in check_and_refresh: {e}")
            return False

    def _run_background_check(self):
        """Background cutoff check"""
        try:
            current_cutoff = self.bigquery_service.get_cutoff_date()
            with self._lock:
                old_cutoff = self._cutoff_date
            
            if current_cutoff != old_cutoff:
                self._refresh_cache()
            else:
                # Update last refresh time anyway to reset the timer
                with self._lock:
                    self._last_refresh = datetime.now()
        except Exception as e:
            logger.error(f"Background check failed: {e}")

    def get_leaderboard(self, region: str, division: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        self._check_and_refresh()
        
        with self._lock:
            data = self._all_data
            
        if not data:
            # Fallback for cold cache
            df = self.bigquery_service.get_leaderboard(region=region, division=division, limit=limit)
            return df.to_dict(orient='records')
            
        # In-memory filtering
        filtered = data
        if region and region != "ALL":
            filtered = [r for r in filtered if r.get('region') == region]
        if division:
            filtered = [r for r in filtered if r.get('division') == division]
        
        return filtered[:limit] if limit else filtered

    def get_regions(self) -> List[str]:
        with self._lock:
            data = self._all_data
        
        if not data:
            # Fallback
            df = self.bigquery_service.get_region_comparison()
            return sorted(df['region'].unique().tolist())
            
        return sorted(list(set(r.get('region') for r in data if r.get('region'))))

    def get_divisions(self, region: str) -> List[str]:
        with self._lock:
            data = self._all_data
            
        if not data:
            return self.bigquery_service.get_divisions(region)
            
        reg_data = [r for r in data if r.get('region') == region or region == "ALL"]
        return sorted(list(set(r.get('division') for r in reg_data if r.get('division'))))

    def get_cache_info(self) -> Dict[str, Any]:
        """Diagnostic info for /health"""
        with self._lock:
            data = self._all_data or []
            cutoff = self._cutoff_date
            last_ref = self._last_refresh
        
        # Calculate regions outside lock if possible, but small set is fine inside
        regions = sorted(list(set(r.get('region') for r in data if r.get('region'))))
        
        return {
            "total_records": len(data),
            "cutoff_date": cutoff,
            "last_refresh": last_ref.isoformat() if last_ref else None,
            "regions_count": len(regions),
            "available_regions": regions
        }

    def force_refresh(self):
        self._refresh_cache()
