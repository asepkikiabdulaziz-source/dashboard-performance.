
from supabase_client import supabase_request
import json

# Get full column details
res = supabase_request('GET', 'products', params={'limit': 1}, headers_extra={'Accept-Profile': 'master'})
if res.get('data'):
    sample = res['data'][0]
    print("=== ACTUAL COLUMN STRUCTURE ===\n")
    print(f"sku_code: {sample.get('sku_code')}")
    print(f"product_name: {sample.get('product_name')}")
    print(f"short_name: {sample.get('short_name')}")
    print(f"parent_sku_code: {sample.get('parent_sku_code')}")
    print(f"parent_sku_name: {sample.get('parent_sku_name')}")
    print(f"principal_id: {sample.get('principal_id')} <- INI APA?")
    print(f"brand_id: {sample.get('brand_id')}")
    print(f"category_id: {sample.get('category_id')}")
    print(f"variant: {sample.get('variant')}")
    print(f"price_segment: {sample.get('price_segment')}")
    print()
    print("Jadi 'principal_id' itu sebenarnya adalah PRINCIPAL (perusahaan prinsipal),")
    print("BUKAN division. Tidak ada kolom 'division' di tabel ini.")
