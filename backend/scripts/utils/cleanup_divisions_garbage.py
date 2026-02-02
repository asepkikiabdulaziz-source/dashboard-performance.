
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

def cleanup():
    print("Cleaning up ref_lookup DIVISION garbage...")
    headers = {'Content-Profile': 'master', 'Accept-Profile': 'master'}
    
    # Check count first?
    # DELETE
    del_res = supabase_request_debug('DELETE', 'ref_lookup', params={'category': 'eq.DIVISION'}, headers_extra=headers)
    if del_res.status_code == 200 or del_res.status_code == 204:
        print("  Cleaned ref_lookup DIVISION entries.")
        if del_res.status_code == 200:
            print(f"  Deleted: {len(del_res.json())} items.")

if __name__ == "__main__":
    cleanup()
