
import sys
sys.path.insert(0, 'd:/PROJECT/dashboard-performance/backend')

from supabase_client import supabase_request
import json

res = supabase_request('GET', 'products', params={'limit': 1}, headers_extra={'Accept-Profile': 'master'})
if res.get('data'):
    sample = res['data'][0]
    print("FULL SCHEMA:")
    print(json.dumps(sample, indent=2))
    print(f"\nColumn Count: {len(sample)}")
    print(f"Columns: {', '.join(sample.keys())}")
