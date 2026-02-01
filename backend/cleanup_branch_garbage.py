
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
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    if headers_extra: headers.update(headers_extra)
    
    resp = requests.request(method, base_url, json=json_data, params=params, headers=headers)
    if resp.status_code >= 400:
        print(f"FAILED {method} {endpoint}: {resp.status_code} - {resp.text}")
    return resp

def check_and_cleanup():
    print("Checking ref_lookup for redundant BRANCH data...")
    headers = {'Content-Profile': 'master', 'Accept-Profile': 'master'}
    
    # Check
    res = supabase_request_debug('GET', 'ref_lookup', params={'category': 'eq.BRANCH'}, headers_extra=headers)
    if res.status_code == 200:
        data = res.json()
        if data:
            print(f"FAILED: Found {len(data)} redundant BRANCH entries in ref_lookup!")
            print("Cleaning up...")
            del_res = supabase_request_debug('DELETE', 'ref_lookup', params={'category': 'eq.BRANCH'}, headers_extra=headers)
            if del_res.status_code == 200 or del_res.status_code == 204:
                print("SUCCESS: Cleaned redundant BRANCH entries.")
        else:
            print("SUCCESS: No redundant BRANCH entries found in ref_lookup.")

if __name__ == "__main__":
    check_and_cleanup()
