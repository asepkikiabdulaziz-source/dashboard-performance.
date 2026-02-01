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
    Checks cutoff_date before serving cached data.
    """
    
    def __init__(self, bigquery_service):
        self.bigquery_service = bigquery_service
        self._lock = threading.RLock() # Use RLock to prevent deadlocks
        
        # Cache storage
        self._all_data: List[Dict[str, Any]] = []
        self._cutoff_date: Optional[str] = None
        self._last_refresh: Optional[datetime] = None
        
        # Warm cache in background to not block startup
        thread = threading.Thread(target=self._refresh_cache)
        thread.daemon = True
        thread.start()
    
    def _refresh_cache(self):
        """Reload all data from BigQuery"""
        try:
            logger.info("🔄 Refreshing leaderboard cache from BigQuery (Background)...")
            start_time = datetime.now()
            
            # Get cutoff date
            cutoff_date = self.bigquery_service.get_cutoff_date()
            
            # Load ALL data (no region filter, no limit)
            all_data_df = self.bigquery_service.get_leaderboard(
                region="ALL",  # Get all regions
                division=None,
                limit=None  # No limit
            )
            
            # Convert to list of dicts for cache storage
            all_data = all_data_df.to_dict(orient='records')
            
            with self._lock:
                self._all_data = all_data
                self._cutoff_date = cutoff_date
                self._last_refresh = datetime.now()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            msg = f"✅ CACHE REFRESHED! Loaded {len(all_data)} records in {elapsed:.2f}s."
            logger.info(msg)
            print(msg) # Ensure we see it
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"❌ Cache refresh failed: {e}")
            print(f"❌ CACHE REFRESH FAILED: {e}")

    def _check_and_refresh(self):
        """
        Check if cutoff_date changed and refresh if needed.
        Rate limited to check only every 15 minutes to avoid BigQuery latency.
        """
        try:
            # Rate limit check: only check only every 15 minutes
            if self._last_refresh and (datetime.now() - self._last_refresh).total_seconds() < 900:  # 15 mins
                return False

            logger.info("⏳ Checking for data updates (cutoff check)...")
            # Run check in background to not block request
            thread = threading.Thread(target=self._run_background_refresh_check)
            thread.daemon = True
            thread.start()
            return False
            
        except Exception as e:
            logger.error(f"❌ Cutoff date check failed: {e}")
            return False

    def _run_background_refresh_check(self):
        """Run actual check in background"""
        try:
            current_cutoff = self.bigquery_service.get_cutoff_date()
            
            if current_cutoff != self._cutoff_date:
                logger.info(f"📅 Cutoff date changed: {self._cutoff_date} → {current_cutoff}")
                self._refresh_cache()
            
            with self._lock:
                self._last_refresh = datetime.now()
        except Exception as e:
            logger.error(f"❌ Background cutoff check failed: {e}")

    def get_leaderboard(
        self, 
        region: str, 
        division: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get leaderboard data. Use cache if ready, otherwise fallback to BigQuery.
        """
        # Trigger background check
        self._check_and_refresh()
        
        # Check if cache is empty (warming up)
        with self._lock:
            data = self._all_data.copy() if self._all_data else None
            
        if not data:
            logger.warning("⚠️ Cache not ready, falling back to BigQuery direct query...")
            # Fallback to direct query
            df = self.bigquery_service.get_leaderboard(
                region=region,
                division=division,
                limit=limit
            )
            return df.to_dict(orient='records')
        
        # Apply filters in-memory
        filtered_data = data
        
        # Filter by region
        if region and region != "ALL":
            filtered_data = [
                record for record in filtered_data 
                if record.get('region') == region
            ]
        
        # Filter by division
        if division:
            filtered_data = [
                record for record in filtered_data 
                if record.get('division') == division
            ]
        
        # Apply limit
        if limit:
            filtered_data = filtered_data[:limit]
        
        return filtered_data
    
    def get_regions(self) -> List[str]:
        """Get unique regions from cache (or fallback)"""
        with self._lock:
            data = self._all_data
            
        if not data:
             # Fallback
             df = self.bigquery_service.get_region_comparison()
             return sorted(df['region'].unique().tolist())

        regions = list(set(
            record.get('region') 
            for record in data 
            if record.get('region')
        ))
        return sorted(regions)
    
    def get_divisions(self, region: str) -> List[str]:
        """Get divisions from cache (or fallback)"""
        with self._lock:
            data = self._all_data
            
        if not data:
             # Fallback
             return self.bigquery_service.get_divisions(region)
             
        # Filter by region first
        region_data = [
            record for record in data
            if record.get('region') == region or region == "ALL"
        ]
        
        # Get unique divisions
        divisions = list(set(
            record.get('division')
            for record in region_data
            if record.get('division')
        ))
    
        return sorted(divisions)
    
    def get_top_performers_summary(self, target_region: str = "ALL") -> List[Dict[str, Any]]:
        """
        Get aggregated Top 1 Salesman per Region and Division (AEGDA/AEPDA).
        If target_region is specified (and not ALL), filters to that region.
        Returns a list of records sorted by Region and Division.
        """
        # Trigger background check
        self._check_and_refresh()
        
        with self._lock:
            data = self._all_data
            
        if not data:
            return []
            
        summary = []
        
        # Filter regions list based on target_region
        all_regions = self.get_regions()
        if target_region and target_region != "ALL":
             regions = [r for r in all_regions if r == target_region]
        else:
             regions = all_regions
        divisions = ["AEGDA", "AEPDA"] # Specific divisions requested
        
        for region in regions:
            for division in divisions:
                # Filter for this region/division
                candidates = [
                    r for r in data 
                    if r.get('region') == region and r.get('division') == division
                ]
                
                if candidates:
                    # Find max score
                    top_performer = max(candidates, key=lambda x: x.get('total_score') or 0)
                    summary.append({
                        "region": region,
                        "division": division,
                        "nik": top_performer.get('nik'),
                        "salesman_name": top_performer.get('salesman_name'),
                        "total_score": top_performer.get('total_score'),
                        "salesman_code": top_performer.get('salesman_code') # Helpful for display
                    })
        
        return summary

    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache statistics (Safe from deadlocks)"""
        with self._lock:
            # Calculate metrics from internal data to avoid nested locks
            data = self._all_data or []
            unique_regions = sorted(list(set(
                record.get('region') for record in data if record.get('region')
            )))
            
            return {
                "total_records": len(data),
                "cutoff_date": self._cutoff_date,
                "last_refresh": self._last_refresh.isoformat() if self._last_refresh else None,
                "regions_count": len(unique_regions),
                "available_regions": unique_regions
            }
    
    def force_refresh(self):
        """Force cache refresh (for admin/testing)"""
        logger.info("🔄 Force refresh requested")
        self._refresh_cache()
