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
        self._last_error: Optional[str] = None # Track errors
        
        # Warm cache in background
        logger.info("🚀 Initializing LeaderboardCache background warming...")
        thread = threading.Thread(target=self._refresh_cache)
        thread.daemon = True
        thread.start()
    
    def _refresh_cache(self):
        """Reload all data from BigQuery with minimal lock hold time"""
        try:
            print("🔄 [CACHE] Starting refresh from BigQuery...")
            logger.info("🔄 Refreshing leaderboard cache from BigQuery...")
            start_time = datetime.now()
            
            # Safety check for service initialization
            if not self.bigquery_service:
                raise Exception("BigQuery Service is not initialized (bigquery_service is None)")
            if not getattr(self.bigquery_service, 'client', None):
                raise Exception("BigQuery Client is not available (client is None)")
            
            # 1. Fetch data OUTSIDE lock (Slow part)
            print("🔍 [CACHE] Fetching cutoff date...")
            cutoff_date = self.bigquery_service.get_cutoff_date()
            print(f"📅 [CACHE] Cutoff Date: {cutoff_date}")
            
            print("🚀 [CACHE] Executing BigQuery Leaderboard Query (ALL Regions)...")
            all_data_df = self.bigquery_service.get_leaderboard(
                region="ALL",
                division=None,
                limit=None
            )
            
            row_count = len(all_data_df)
            print(f"📊 [CACHE] Query Complete. Found {row_count} records.")
            
            print("🧩 [CACHE] Converting to dictionary...")
            all_data = all_data_df.to_dict(orient='records')
            
            # 2. Update status and data INSIDE lock (Fast part)
            print("🔒 [CACHE] Updating in-memory state...")
            with self._lock:
                self._all_data = all_data
                self._cutoff_date = cutoff_date
                self._last_refresh = datetime.now()
                self._last_error = None # Clear error on success
            
            elapsed = (datetime.now() - start_time).total_seconds()
            msg = f"✅ [CACHE] REFRESHED: {len(all_data)} records in {elapsed:.2f}s"
            logger.info(msg)
            print(msg)
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ [CACHE] FATAL ERROR during refresh: {error_msg}")
            with self._lock:
                self._last_error = error_msg
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

    def get_kpis_cached(self, region: str) -> Dict[str, Any]:
        """Aggregate KPIs from memory"""
        with self._lock:
            data = self._all_data
        
        if not data:
            return self.bigquery_service.get_kpis(region)
            
        filtered = data if region == "ALL" else [r for r in data if r.get('region') == region]
        
        if not filtered:
            return {
                "total_revenue": 0, "total_target": 0, "achievement_rate": 0,
                "growth_rate": 0, "total_salesman": 0, "avg_customer_base": 0, "avg_roa": 0
            }
            
        rev = sum(r.get('omset_p4', 0) or 0 for r in filtered)
        prev_rev = sum(r.get('omset_p3', 0) or 0 for r in filtered)
        target = sum(r.get('target', 0) or 0 for r in filtered)
        
        ach_rate = (rev / target * 100) if target > 0 else 0
        growth = ((rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0
        forecast = rev * (1 + growth/100)
        
        return {
            "total_revenue": rev,
            "total_target": target,
            "achievement_rate": round(ach_rate, 2),
            "growth_rate": round(growth, 2),
            "forecast": round(forecast, 2),
            "total_salesman": len(filtered),
            "avg_customer_base": sum(r.get('total_customer', 0) or 0 for r in filtered) / len(filtered),
            "avg_roa": sum(r.get('roa_p4', 0) or 0 for r in filtered) / len(filtered)
        }

    def get_sales_trend_cached(self, region: str) -> List[Dict[str, Any]]:
        """Aggregate sales trend from memory"""
        with self._lock:
            data = self._all_data
            
        if not data:
            df = self.bigquery_service.get_sales_trend(region)
            return df.to_dict(orient='records')
            
        filtered = data if region == "ALL" else [r for r in data if r.get('region') == region]
        
        trends = []
        for p in range(1, 5):
            p_key = f'omset_p{p}'
            roa_key = f'roa_p{p}'
            revenue = sum(r.get(p_key, 0) or 0 for r in filtered)
            roa = sum(r.get(roa_key, 0) or 0 for r in filtered) / len(filtered) if filtered else 0
            trends.append({
                "period": f"Period {p}",
                "total_sales": revenue,
                "avg_roa": round(roa, 2),
                "salesman_count": len(filtered)
            })
        return trends

    def get_region_comparison_cached(self) -> List[Dict[str, Any]]:
        """Aggregate region comparison from memory"""
        with self._lock:
            data = self._all_data
            
        if not data:
            df = self.bigquery_service.get_region_comparison()
            return df.to_dict(orient='records')
            
        regions = sorted(list(set(r.get('region') for r in data if r.get('region'))))
        comparison = []
        
        for reg in regions:
            reg_data = [r for r in data if r.get('region') == reg]
            rev = sum(r.get('omset_p4', 0) or 0 for r in reg_data)
            target = sum(r.get('target', 0) or 0 for r in reg_data)
            ach = (rev / target * 100) if target > 0 else 0
            
            comparison.append({
                "region": reg,
                "total_revenue": rev,
                "total_target": target,
                "achievement_rate": round(ach, 2),
                "salesman_count": len(reg_data)
            })
            
        return sorted(comparison, key=lambda x: x['achievement_rate'], reverse=True)

    def get_top_performers_cached(self, region: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performers from memory"""
        data = self.get_leaderboard(region=region, limit=limit)
        return data

    def get_cache_info(self) -> Dict[str, Any]:
        """Diagnostic info for /health"""
        with self._lock:
            data = self._all_data or []
            cutoff = self._cutoff_date
            last_ref = self._last_refresh
            last_err = self._last_error
        
        # Calculate regions outside lock if possible, but small set is fine inside
        regions = sorted(list(set(r.get('region') for r in data if r.get('region'))))
        
        return {
            "total_records": len(data),
            "cutoff_date": cutoff,
            "last_refresh": last_ref.isoformat() if last_ref else None,
            "last_error": last_err,
            "regions_count": len(regions),
            "available_regions": regions
        }

    def force_refresh(self):
        self._refresh_cache()
