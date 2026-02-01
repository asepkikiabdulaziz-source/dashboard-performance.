
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
service_key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

# Standard Client (Anon) - For regular user operations
def get_supabase_client() -> Client:
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("⚠️ WARNING: SUPABASE_URL or SUPABASE_KEY is missing from environment!")
        raise ValueError("Supabase configuration missing")
    
    return create_client(supabase_url, supabase_key)

# Admin Client (Service Role) - For User Management
def get_supabase_admin() -> Client:
    supabase_url = os.environ.get("SUPABASE_URL")
    admin_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not admin_key:
        print("⚠️ WARNING: SUPABASE_URL or Admin Key is missing from environment!")
        raise ValueError("Supabase admin configuration missing")
        
    return create_client(supabase_url, admin_key)

# --- Fallback HTTP Client (Bypasses supabase-py/gotrue proxy bug) ---
import requests

def supabase_request(method, endpoint, params=None, json_data=None, headers_extra=None):
    """
    Execute a raw HTTP request to Supabase REST API.
    Endpoint examples: 'sales_slots', 'rpc/func_name'
    """
    if not url or not service_key:
        raise ValueError("Supabase Config missing")
    
    base_url = f"{url}/rest/v1/{endpoint}"
    
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": "count=exact" # Default for lists
    }
    if headers_extra:
        headers.update(headers_extra)
        
    print(f"[Supabase] {method} {base_url} | Params: {params} | JSON: {json_data}")
    try:
        response = requests.request(method, base_url, params=params, json=json_data, headers=headers)
        if response.status_code >= 400:
             print(f"[Supabase] ERROR {response.status_code}: {response.text}")
        response.raise_for_status()
        
        # Handle count header
        count = None
        content_range = response.headers.get('Content-Range')
        if content_range:
            # Example: 0-9/100
            parts = content_range.split('/')
            if len(parts) > 1 and parts[1].isdigit():
                count = int(parts[1])
        
        # PATCH/DELETE might not return JSON if Prefer: return=minimal
        try:
            data = response.json()
        except:
            data = {}
            
        return {"data": data, "count": count}
        
    except Exception as e:
        print(f"Supabase HTTP Error: {e}")
        # Return empty structure to match supabase-pyish
        raise e

def supabase_auth_admin_request(method, endpoint, json_data=None):
    """
    Execute a raw HTTP request to Supabase Auth Admin API.
    Endpoint examples: 'users', 'users/{uuid}'
    """
    if not url or not service_key:
        raise ValueError("Supabase Config missing")
    
    # Auth API is usually at /auth/v1/
    base_url = f"{url}/auth/v1/admin/{endpoint}"
    
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json"
    }
        
    try:
        response = requests.request(method, base_url, json=json_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Supabase Auth Admin Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"Error Response: {e.response.text}")
        raise e

