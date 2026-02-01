
from supabase_client import supabase_request
import json

# Get sample data to compare
res = supabase_request('GET', 'products', params={'limit': 2}, headers_extra={'Accept-Profile': 'master'})
if res.get('data'):
    print("=== SAMPLE DATA FROM DATABASE ===\n")
    for i, product in enumerate(res['data'], 1):
        print(f"Product {i}:")
        print(f"  SKU: {product.get('sku_code')}")
        print(f"  Name: {product.get('product_name')}")
        print(f"  category_id: {product.get('category_id')}")
        print(f"  brand_id: {product.get('brand_id')}")
        print(f"  principal_id: {product.get('principal_id')}")
        print(f"  UOM Medium: {product.get('uom_medium')} ({product.get('isi_pcs_per_medium')})")
        print()
