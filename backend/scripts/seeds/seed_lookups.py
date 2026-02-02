
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://localhost:8000/api/admin/master/lookup"
# For seeding, we might need a super admin token, or we can use the supabase_request helper directly 
# to bypass API auth for the script (cleaner), or just use the DB directly.
# Let's use supabase_request from supabase_client to insert directly to Table 'ref_lookup'.

from supabase_client import supabase_request

DATA_TO_SEED = {
    "DIVISION": [
        {"code": "TX2DA", "name": "TX2DA", "description": "Division TX2DA"},
        {"code": "AEPDA", "name": "AEPDA", "description": "Division AEPDA"},
        {"code": "TSODA", "name": "TSODA", "description": "Division TSODA"},
        {"code": "BCOD", "name": "BCOD", "description": "Division BCOD"},
    ],
    "ROLE": [
        {"code": "salesman", "name": "Salesman", "description": "Sales Representative"},
        {"code": "supervisor", "name": "Supervisor", "description": "Sales Supervisor"},
        {"code": "branch_manager", "name": "Branch Manager", "description": "Branch Head"},
        {"code": "regional_manager", "name": "Regional Manager", "description": "Region Head"},
    ],
    "LEVEL": [
        {"code": "1", "name": "Entry", "description": "Level 1"},
        {"code": "2", "name": "Intermediate", "description": "Level 2"},
        {"code": "3", "name": "Senior", "description": "Level 3"},
        {"code": "4", "name": "Manager", "description": "Level 4"},
        {"code": "99", "name": "Special", "description": "Special Level"},
    ]
}

def supabase_request_debug(method, endpoint, params=None, json_data=None, headers_extra=None):
    # Copy of helper with better logging
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

def seed():
    print("Seeding Reference Lookups...")
    
    # 1. Ensure Company Exists
    print("Checking Company ID001...")
    res = supabase_request_debug('GET', 'ref_companies', params={'id': 'eq.ID001'}, headers_extra={'Accept-Profile': 'master'})
    if res.status_code == 200 and not res.json():
        print("  Creating Company ID001...")
        supabase_request_debug('POST', 'ref_companies', 
                             json_data={"id": "ID001", "name": "Default Company"}, 
                             headers_extra={'Content-Profile': 'master'})
    
    headers = {'Content-Profile': 'master', 'Accept-Profile': 'master', 'Prefer': 'return=representation'}
    
    for category, items in DATA_TO_SEED.items():
        print(f"Processing {category}...")
        for item in items:
            payload = {
                "category": category,
                "code": item["code"],
                "name": item["name"],
                "description": item["description"],
                "company_id": "ID001"
            }
            
            # Check if exists
            exists = supabase_request_debug('GET', 'ref_lookup', 
                                   params={'category': f"eq.{category}", 'code': f"eq.{item['code']}"},
                                   headers_extra={'Accept-Profile': 'master'})
            
            if exists.status_code == 200 and exists.json():
                print(f"  Skipping {item['code']} (exists)")
            else:
                res = supabase_request_debug('POST', 'ref_lookup', json_data=payload, headers_extra=headers)
                if res.status_code == 201:
                    print(f"  Created {item['code']}")

if __name__ == "__main__":
    try:
        seed()
        print("Done!")
    except Exception as e:
        print(f"Error: {e}")
