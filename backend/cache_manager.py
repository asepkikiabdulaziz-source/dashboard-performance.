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
        
        # Cache storage
        self._all_data: List[Dict[str, Any]] = []
        self._competition_data: Dict[str, List[Dict[str, Any]]] = {} # Map "compid_level" -> data
        self._cutoff_date: Optional[str] = None
        self._last_refresh: Optional[datetime] = None
        self._last_error: Optional[str] = None
        
        # Warm cache in background
        logger.info("🚀 Initializing LeaderboardCache background warming...")
        thread = threading.Thread(target=self._refresh_cache)
        thread.daemon = True
        thread.start()
    
    def _refresh_cache(self):
        """Reload all data from BigQuery with minimal lock hold time"""
        try:
            logger.info("[CACHE] Starting refresh from BigQuery...")
            start_time = datetime.now()
            
            if not self.bigquery_service:
                raise Exception("BigQuery Service is not initialized")
            
            # 1. Fetch data OUTSIDE lock
            cutoff_date = self.bigquery_service.get_cutoff_date()
            
            # Fetch normal leaderboard
            all_data_df = self.bigquery_service.get_leaderboard(region="ALL")
            all_data = all_data_df.to_dict(orient='records')
            
            # Fetch AMO Competition data (ASS, BM, RBM)
            comp_data = {}
            from competition_config import COMPETITIONS
            for comp_id in COMPETITIONS:
                for level in ['ass', 'bm', 'rbm']:
                    logger.debug(f"[CACHE] Pre-loading {comp_id} level {level}...")
                    try:
                        data = self.bigquery_service.get_competition_ranks(
                            level=level,
                            competition_id=comp_id,
                            region="ALL" # Cache national version
                        )
                        comp_data[f"{comp_id}_{level}"] = data
                    except Exception as ce:
                        logger.warning(f"[CACHE] Failed to pre-load {comp_id}_{level}: {ce}")
            
            # 2. Update status and data INSIDE lock
            with self._lock:
                self._all_data = all_data
                self._competition_data = comp_data
                self._cutoff_date = cutoff_date
                self._last_refresh = datetime.now()
                self._last_error = None
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"[CACHE] REFRESHED: {len(all_data)} leaderboard + {len(comp_data)} comp levels in {elapsed:.2f}s")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[CACHE] FATAL ERROR during refresh: {error_msg}")
            with self._lock:
                self._last_error = error_msg
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

    def get_top_performers_summary(self, target_region: str = "ALL") -> List[Dict[str, Any]]:
        """Get top salesman per region and division for modal view"""
        with self._lock:
            data = self._all_data
            
        if not data:
            return []
            
        # Filter by region if requested
        regions = sorted(list(set(r.get('region') for r in data if r.get('region'))))
        if target_region and target_region != "ALL":
            regions = [target_region]
            
        summary = []
        for reg in regions:
            reg_data = [r for r in data if r.get('region') == reg]
            divisions = sorted(list(set(r.get('division') for r in reg_data if r.get('division'))))
            
            for div in divisions:
                div_data = [r for r in reg_data if r.get('division') == div]
                if div_data:
                    # Sort by total_score DESC
                    top = sorted(div_data, key=lambda x: x.get('total_score', 0), reverse=True)[0]
                    summary.append(top)
        
        return summary

    def get_competition_ranks_cached(
        self,
        level: str,
        competition_id: str,
        region: str = "ALL",
        role: str = "viewer",
        user_nik: Optional[str] = None,
        scope: Optional[str] = None,
        scope_id: Optional[str] = None,
        zona_rbm: Optional[str] = None,
        zona_bm: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Filtered competition data from memory"""
        self._check_and_refresh()
        
        cache_key = f"{competition_id}_{level.lower()}"
        with self._lock:
            data = self._competition_data.get(cache_key)
            
        if not data:
            # Fallback for cold cache
            return self.bigquery_service.get_competition_ranks(
                level=level,
                competition_id=competition_id,
                region=region,
                role=role,
                user_nik=user_nik,
                scope=scope,
                scope_id=scope_id,
                zona_rbm=zona_rbm,
                zona_bm=zona_bm
            )
            
        # In-memory filtering logic (mirrors bigquery_service.py RLS)
        filtered = data
        user_role_lower = role.lower()
        active_level_lower = level.lower()
        is_admin = user_role_lower in ['super_admin', 'admin', 'master', 'head']
        is_national_view = False

        if not is_admin:
            if active_level_lower == 'rbm':
                # If user is specific RBM, or admin/higher restricted them, or they chose a filter
                final_rbm = zona_rbm or region # region can be RBM code sometimes
                if final_rbm and final_rbm != "ALL":
                    filtered = [r for r in filtered if r.get('zona_rbm') == final_rbm or r.get('region') == final_rbm]
                else:
                    is_national_view = True
                    
            elif active_level_lower == 'bm':
                # BM filtering: prioritize zona_bm parameter, then fallbacks
                if zona_bm and zona_bm != "ALL":
                    filtered = [r for r in filtered if r.get('zona_bm') == zona_bm]
                elif zona_rbm and zona_rbm != "ALL":
                    filtered = [r for r in filtered if r.get('zona_rbm') == zona_rbm]
                elif region != "ALL":
                    filtered = [r for r in filtered if r.get('region') == region]
                else:
                    is_national_view = True
                    
            elif active_level_lower == 'ass':
                # ASS filtering
                if user_role_lower == 'bm' and scope_id:
                    filtered = [r for r in filtered if r.get('zona_bm') == scope_id or r.get('cabang') == scope_id]
                elif region != "ALL":
                    filtered = [r for r in filtered if r.get('region') == region]
                else:
                    is_national_view = True
        else:
            # Admin path: respects explicit filters passed as parameters
            if active_level_lower == 'ass' and region != "ALL":
                filtered = [r for r in filtered if r.get('region') == region]
            elif active_level_lower == 'bm' and zona_bm and zona_bm != "ALL":
                filtered = [r for r in filtered if r.get('zona_bm') == zona_bm]
            elif active_level_lower == 'rbm' and zona_rbm and zona_rbm != "ALL":
                filtered = [r for r in filtered if r.get('zona_rbm') == zona_rbm]
            else:
                is_national_view = True
        
        # Follow original order from cache (which follows DB order)
        return filtered

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
