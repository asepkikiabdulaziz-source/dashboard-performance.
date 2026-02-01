
from supabase_client import supabase_request
import json

def probe():
    tables = ['ref_categories', 'ref_brands', 'ref_principals', 'ref_companies', 'rev_divisi', 'ref_lookup']
    
    for t in tables:
        try:
            res = supabase_request('GET', t, params={'limit': 1}, headers_extra={'Accept-Profile': 'master'})
            data = res.get('data', [])
            if data:
                print(f"[FOUND] {t}: Columns {list(data[0].keys())}")
            else:
                raw = res.get('error', 'No data')
                print(f"[MISSING/EMPTY] {t}: {raw}")
        except Exception as e:
            print(f"[ERROR] {t}: {str(e)}")

if __name__ == "__main__":
    probe()
