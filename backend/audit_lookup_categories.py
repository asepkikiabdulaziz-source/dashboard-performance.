
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def supabase_request_debug(method, endpoint, params=None, json_data=None, headers_extra=None):
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")
    base_url = f"{url}/rest/v1/{endpoint}"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
    }
    if headers_extra: headers.update(headers_extra)
    
    resp = requests.request(method, base_url, json=json_data, params=params, headers=headers)
    return resp

def audit():
    print("Auditing ref_lookup categories...")
    headers = {'Accept-Profile': 'master'}
    
    # Select distinct? PostgREST handling of distinct is tricky, usually need explicit select
    # or just fetch all logic
    res = supabase_request_debug('GET', 'ref_lookup', params={'select': 'category'}, headers_extra=headers)
    if res.status_code == 200:
        data = res.json()
        cats = sorted(list(set(item['category'] for item in data if item.get('category'))))
        print(f"Categories Found ({len(cats)}):")
        for c in cats:
            print(f"- {c}")
    else:
        print(f"Error: {res.status_code}")

if __name__ == "__main__":
    audit()
