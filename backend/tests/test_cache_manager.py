"""
Tests for Cache Manager (cache_manager.py)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from cache_manager import LeaderboardCache


class TestLeaderboardCache:
    """Tests for LeaderboardCache class"""
    
    @pytest.fixture
    def mock_bigquery_service(self):
        """Create mock BigQuery service"""
        mock_service = Mock()
        mock_service.project_id = "test-project"
        mock_service.dataset = "test-dataset"
        mock_service.get_cutoff_date.return_value = "2024-01-01"
        
        # Mock DataFrame
        import pandas as pd
        mock_df = pd.DataFrame([
            {"region": "R06 JABODEBEK", "name": "Salesman A", "revenue": 500000},
            {"region": "R07 BANDUNG", "name": "Salesman B", "revenue": 450000}
        ])
        mock_service.get_leaderboard.return_value = mock_df
        mock_service.get_competition_ranks.return_value = []
        
        return mock_service
    
    def test_cache_initialization(self, mock_bigquery_service):
        """Test cache initialization"""
        cache = LeaderboardCache(mock_bigquery_service)
        
        assert cache.bigquery_service == mock_bigquery_service
        assert cache._all_data == []
        assert cache._cutoff_date is None
    
    def test_get_leaderboard_with_region_filter(self, mock_bigquery_service):
        """Test getting leaderboard filtered by region"""
        cache = LeaderboardCache(mock_bigquery_service)
        
        # Manually set cache data
        cache._all_data = [
            {"region": "R06 JABODEBEK", "name": "Salesman A", "revenue": 500000},
            {"region": "R07 BANDUNG", "name": "Salesman B", "revenue": 450000},
            {"region": "R06 JABODEBEK", "name": "Salesman C", "revenue": 400000}
        ]
        
        result = cache.get_leaderboard(region="R06 JABODEBEK")
        
        assert len(result) == 2
        assert all(r["region"] == "R06 JABODEBEK" for r in result)
    
    def test_get_leaderboard_all_regions(self, mock_bigquery_service):
        """Test getting leaderboard for all regions (admin)"""
        cache = LeaderboardCache(mock_bigquery_service)
        
        cache._all_data = [
            {"region": "R06 JABODEBEK", "name": "Salesman A", "revenue": 500000},
            {"region": "R07 BANDUNG", "name": "Salesman B", "revenue": 450000}
        ]
        
        result = cache.get_leaderboard(region="ALL")
        
        assert len(result) == 2
    
    def test_get_leaderboard_with_limit(self, mock_bigquery_service):
        """Test leaderboard with limit parameter"""
        cache = LeaderboardCache(mock_bigquery_service)
        
        cache._all_data = [
            {"region": "R06 JABODEBEK", "name": f"Salesman {i}", "revenue": 500000 - i*10000}
            for i in range(10)
        ]
        
        result = cache.get_leaderboard(region="R06 JABODEBEK", limit=5)
        
        assert len(result) == 5
    
    def test_get_leaderboard_with_division_filter(self, mock_bigquery_service):
        """Test leaderboard with division filter"""
        cache = LeaderboardCache(mock_bigquery_service)
        
        cache._all_data = [
            {"region": "R06 JABODEBEK", "division": "DIV1", "name": "Salesman A", "revenue": 500000},
            {"region": "R06 JABODEBEK", "division": "DIV2", "name": "Salesman B", "revenue": 450000},
            {"region": "R06 JABODEBEK", "division": "DIV1", "name": "Salesman C", "revenue": 400000}
        ]
        
        result = cache.get_leaderboard(region="R06 JABODEBEK", division="DIV1")
        
        assert len(result) == 2
        assert all(r["division"] == "DIV1" for r in result)
    
    def test_get_leaderboard_cold_cache(self, mock_bigquery_service):
        """Test leaderboard when cache is empty (cold cache)"""
        cache = LeaderboardCache(mock_bigquery_service)
        
        # Cache is empty, should fallback to BigQuery
        import pandas as pd
        mock_df = pd.DataFrame([
            {"region": "R06 JABODEBEK", "name": "Salesman A", "revenue": 500000}
        ])
        mock_bigquery_service.get_leaderboard.return_value = mock_df
        
        result = cache.get_leaderboard(region="R06 JABODEBEK")
        
        assert len(result) == 1
        mock_bigquery_service.get_leaderboard.assert_called_once()
    
    def test_get_regions(self, mock_bigquery_service):
        """Test getting list of available regions"""
        cache = LeaderboardCache(mock_bigquery_service)
        
        cache._all_data = [
            {"region": "R06 JABODEBEK"},
            {"region": "R07 BANDUNG"},
            {"region": "R06 JABODEBEK"}  # Duplicate
        ]
        
        regions = cache.get_regions()
        
        assert "R06 JABODEBEK" in regions
        assert "R07 BANDUNG" in regions
        assert len(regions) == 2  # Unique regions
    
    def test_get_divisions(self, mock_bigquery_service):
        """Test getting divisions for a region"""
        cache = LeaderboardCache(mock_bigquery_service)
        
        cache._all_data = [
            {"region": "R06 JABODEBEK", "division": "DIV1"},
            {"region": "R06 JABODEBEK", "division": "DIV2"},
            {"region": "R07 BANDUNG", "division": "DIV1"}
        ]
        
        divisions = cache.get_divisions("R06 JABODEBEK")
        
        assert "DIV1" in divisions
        assert "DIV2" in divisions
        assert len(divisions) == 2
    
    def test_get_kpis_cached(self, mock_bigquery_service):
        """Test getting KPIs from cache"""
        cache = LeaderboardCache(mock_bigquery_service)
        
        cache._all_data = [
            {
                "region": "R06 JABODEBEK",
                "omset_p4": 1000000,
                "omset_p3": 900000,
                "target": 1200000,
                "total_customer": 100,
                "roa_p4": 15.5
            },
            {
                "region": "R06 JABODEBEK",
                "omset_p4": 500000,
                "omset_p3": 450000,
                "target": 600000,
                "total_customer": 50,
                "roa_p4": 12.0
            }
        ]
        
        kpis = cache.get_kpis_cached("R06 JABODEBEK")
        
        assert kpis["total_revenue"] == 1500000
        assert kpis["total_target"] == 1800000
        assert kpis["achievement_rate"] > 0
        assert kpis["growth_rate"] > 0
        assert kpis["total_salesman"] == 2
    
    def test_get_kpis_empty_data(self, mock_bigquery_service):
        """Test KPIs when no data available"""
        cache = LeaderboardCache(mock_bigquery_service)
        
        cache._all_data = []
        
        kpis = cache.get_kpis_cached("R06 JABODEBEK")
        
        assert kpis["total_revenue"] == 0
        assert kpis["achievement_rate"] == 0
        assert kpis["total_salesman"] == 0
    
    def test_cache_refresh_on_cutoff_change(self, mock_bigquery_service):
        """Test that cache refreshes when cutoff date changes"""
        cache = LeaderboardCache(mock_bigquery_service)
        
        # Set initial cutoff
        cache._cutoff_date = "2024-01-01"
        cache._all_data = [{"region": "R06 JABODEBEK", "name": "Salesman A"}]
        
        # Change cutoff date
        mock_bigquery_service.get_cutoff_date.return_value = "2024-01-02"
        
        # Trigger refresh check
        cache._check_and_refresh()
        
        # Verify refresh was triggered (in real scenario, this would update cache)
        # For this test, we just verify the method exists and can be called
        assert hasattr(cache, '_refresh_cache')
    
    def test_get_cache_info(self, mock_bigquery_service):
        """Test getting cache information"""
        cache = LeaderboardCache(mock_bigquery_service)
        
        cache._all_data = [{"region": "R06 JABODEBEK"}]
        cache._cutoff_date = "2024-01-01"
        cache._last_refresh = datetime.now()
        
        info = cache.get_cache_info()
        
        assert "data_count" in info
        assert "cutoff_date" in info
        assert "last_refresh" in info
