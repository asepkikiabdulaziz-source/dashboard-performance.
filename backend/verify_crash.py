import os
from supabase_client import get_supabase_client
import traceback

def test():
    print("Testing Supabase Client Init...")
    try:
        # Check if proxy env vars exist
        print(f"HTTP_PROXY: {os.environ.get('HTTP_PROXY')}")
        print(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY')}")
        
        client = get_supabase_client()
        print("Client created successfully.")
        
        print("Executing simple query...")
        res = client.table('sales_slots').select("count", count='exact').limit(1).execute()
        print("Query success!")
        print(res)
        
    except Exception as e:
        print("CRASHED:")
        traceback.print_exc()

if __name__ == "__main__":
    test()
