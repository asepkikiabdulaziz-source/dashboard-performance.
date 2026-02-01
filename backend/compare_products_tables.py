
from supabase_client import supabase_request
import json

def compare_tables():
    print("--- Checking master.products ---")
    try:
        res = supabase_request('GET', 'products', params={'limit': 2}, headers_extra={'Accept-Profile': 'master'})
        data = res.get('data', [])
        if data:
            print(f"Found {len(data)} items in master.products")
            print(f"Sample row keys: {list(data[0].keys())}")
            print(f"Sample data: {json.dumps(data[0], indent=2)}")
        else:
            print("Table 'master.products' is empty or doesn't exist")
    except Exception as e:
        print(f"Error accessing master.products: {e}")
    
    print("\n--- Checking master.ref_products ---")
    try:
        res = supabase_request('GET', 'ref_products', params={'limit': 2}, headers_extra={'Accept-Profile': 'master'})
        data = res.get('data', [])
        if data:
            print(f"Found {len(data)} items in master.ref_products")
            print(f"Sample row keys: {list(data[0].keys())}")
            print(f"Sample data: {json.dumps(data[0], indent=2)}")
        else:
            print("Table 'master.ref_products' is empty")
    except Exception as e:
        print(f"Error accessing master.ref_products: {e}")

if __name__ == "__main__":
    compare_tables()
