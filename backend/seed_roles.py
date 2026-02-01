
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

DATA_ROLES = [
    {"role_id": "salesman", "role_name": "Salesman", "description": "Frontline sales"},
    {"role_id": "driver", "role_name": "Driver", "description": "Delivery driver"},
    {"role_id": "helper", "role_name": "Helper", "description": "Driver assistant"},
    {"role_id": "admin_depo", "role_name": "Admin Depo", "description": "Depo administrator"},
    {"role_id": "admin_ho", "role_name": "Admin HO", "description": "Head office administrator"},
    {"role_id": "super_admin", "role_name": "Super Administrator", "description": "Full system access"}
]

def seed():
    print("Seeding Ref Role...")
    headers = {'Content-Profile': 'master', 'Accept-Profile': 'master', 'Prefer': 'return=representation'}
    
    for item in DATA_ROLES:
        # Check exists
        exists = supabase_request_debug('GET', 'ref_role', params={'role_id': f"eq.{item['role_id']}"}, headers_extra=headers)
        if exists.status_code == 200 and exists.json():
            print(f"  Skipping {item['role_id']} (exists)")
            # Optional: Update level/name?
        else:
            res = supabase_request_debug('POST', 'ref_role', json_data=item, headers_extra=headers)
            if res.status_code == 201:
                print(f"  Created {item['role_id']}")
    
    # Cleanup ref_lookup ROLE garbage if any?
    # We can delete from ref_lookup where category='ROLE'
    print("Cleaning up ref_lookup ROLE garbage...")
    del_res = supabase_request_debug('DELETE', 'ref_lookup', params={'category': 'eq.ROLE'}, headers_extra=headers)
    if del_res.status_code == 200: # 200 or 204
        print("  Cleaned ref_lookup ROLE entries.")

if __name__ == "__main__":
    seed()
