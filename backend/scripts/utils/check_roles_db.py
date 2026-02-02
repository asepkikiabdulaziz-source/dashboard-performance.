
from supabase_client import supabase_request
import json

def check_roles():
    headers = {'Accept-Profile': 'master'}
    try:
        res = supabase_request('GET', 'ref_role', headers_extra=headers)
        print("=== ROLE IDs IN DATABASE ===")
        roles = [r.get('role_id') for r in res.get('data', [])]
        for rid in sorted(roles):
            print(f"- {rid}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_roles()
