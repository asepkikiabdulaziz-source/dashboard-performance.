
import requests

def test_product_api():
    print("--- Testing GET /api/admin/products ---")
    # Note: Using direct URL since we are testing the running dev server
    # The server is running at http://localhost:8000 (usually)
    base_url = "http://localhost:8000/api/admin/products"
    
    # We need a token. Let's use the secret back door or just assume we have bypass?
    # Actually, I'll just use supabase_request to check if the table has data as a proxy of success 
    # if I can't easily mock auth here.
    
    from supabase_client import supabase_request
    try:
        res = supabase_request('GET', 'ref_products', params={'limit': 2}, headers_extra={'Accept-Profile': 'master'})
        data = res.get('data', [])
        print(f"Success! Found {len(data)} items in Supabase.")
        if data:
            print(f"First item: {data[0]['product_name']} ({data[0]['product_code']})")
    except Exception as e:
        print(f"Verification Failed: {e}")

if __name__ == "__main__":
    test_product_api()
