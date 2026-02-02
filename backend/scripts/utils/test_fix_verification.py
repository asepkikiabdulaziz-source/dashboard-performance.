
import os
import sys
import pandas as pd
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from bigquery_service import BigQueryService
from cache_manager import LeaderboardCache

def test_national_ranking():
    print("🧪 Testing National Ranking Logic...")
    svc = BigQueryService()
    
    # Mock BigQuery Client
    mock_client = MagicMock()
    svc.client = mock_client
    
    # Mock data with database-defined ranks
    mock_df = pd.DataFrame([
        {'rank_ASS': 17, 'rank_zona': 1, 'total_Point': 1000, 'ach_oms': 0.95, 'NAMA_ASS': 'Winner A', 'REGION': 'Region 1'},
        {'rank_ASS': 48, 'rank_zona': 1, 'total_Point': 900, 'ach_oms': 0.90, 'NAMA_ASS': 'Winner B', 'REGION': 'Region 2'},
        {'rank_ASS': 58, 'rank_zona': 2, 'total_Point': 850, 'ach_oms': 0.85, 'NAMA_ASS': 'Second A', 'REGION': 'Region 1'},
    ])
    
    mock_query_job = MagicMock()
    mock_query_job.to_dataframe.return_value = mock_df
    mock_client.query.return_value = mock_query_job
    
    # Test Ranking (following DB columns)
    results = svc.get_competition_ranks(
        level='ass',
        competition_id='amo_jan_2026',
        region='ALL',
        role='HEAD'
    )
    
    print(f"✅ Received {len(results)} results")
    for r in results:
        print(f"Rank: #{r['rank']}, Name: {r['name']}, Points: {r['total_point']}")
    
    # Assert ranks follow DB exactly
    ranks = [r['rank'] for r in results]
    assert ranks == [17, 48, 58], f"Expected ranks [17, 48, 58], got {ranks}"
    assert results[0]['name'] == 'Winner A'
    assert results[1]['name'] == 'Winner B'
    print("✨ National Ranking Logic Test PASSED")

def test_cache_expansion():
    print("\n🧪 Testing Cache Expansion for Competitions...")
    svc = BigQueryService()
    # Mock get_cutoff_date, get_leaderboard, get_competition_ranks
    svc.get_cutoff_date = MagicMock(return_value="2026-01-31")
    svc.get_leaderboard = MagicMock(return_value=pd.DataFrame())
    
    comp_results = [{'rank': 1, 'name': 'Cached Winner', 'total_point': 100, 'omset_ach': 90}]
    svc.get_competition_ranks = MagicMock(return_value=comp_results)
    
    cache = LeaderboardCache(svc)
    # Manually trigger refresh to avoid waiting for thread
    cache._refresh_cache()
    
    # Test fetching from cache
    cached_data = cache.get_competition_ranks_cached(
        level='ass',
        competition_id='amo_jan_2026',
        region='ALL'
    )
    
    assert cached_data == comp_results, "Data should be served from cache"
    assert svc.get_competition_ranks.call_count >= 1
    
    # Second call should NOT trigger bigquery_service.get_competition_ranks if using cache
    # But wait, our get_competition_ranks_cached calls it ONLY if data is missing.
    # So call_count should remain the same.
    prev_count = svc.get_competition_ranks.call_count
    cached_data_2 = cache.get_competition_ranks_cached(
        level='ass',
        competition_id='amo_jan_2026',
        region='ALL'
    )
    assert cached_data_2 == comp_results
    assert svc.get_competition_ranks.call_count == prev_count, "Second call should have used cache"
    print("✨ Competition Caching Test PASSED")

if __name__ == "__main__":
    try:
        test_national_ranking()
        test_cache_expansion()
        print("\n🚀 ALL TESTS PASSED SUCCESSFULLY!")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
