
from supabase_client import supabase_request
import json

def inspect_potential_tables():
    # 1. Price Zones
    print("--- Inspecting 'price_zones' ---")
    try:
        res = supabase_request('GET', 'price_zones', params={'limit': 1}, headers_extra={'Accept-Profile': 'master'})
        if res.get('data'):
            print(f"Sample Row: {res['data'][0]}")
        else:
            print("Table 'price_zones' is empty.")
    except Exception as e:
        print(f"Error checking price_zones: {e}")

    # 2. Broad Search for names
    # We can try to list tables if there's a common RPC or just guess common ones
    common_names = ['ref_sku', 'ref_produk', 'ref_barang', 'ms_sku', 'ms_produk', 'ms_item', 'ref_item_master']
    print("\n--- Broad Probe for SKU/Product Tables ---")
    for name in common_names:
        try:
            res = supabase_request('GET', name, params={'limit': 1}, headers_extra={'Accept-Profile': 'master'})
            print(f"[FOUND] master.{name}")
            print(f"Sample: {res['data'][0] if res.get('data') else 'Empty'}")
        except:
            pass

if __name__ == "__main__":
    inspect_potential_tables()
