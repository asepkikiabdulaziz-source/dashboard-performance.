
from supabase_client import supabase_request

# Check ref_categories
print("=== master.ref_categories ===")
try:
    res = supabase_request('GET', 'ref_categories', params={'limit': 5}, headers_extra={'Accept-Profile': 'master'})
    for item in res.get('data', []):
        print(f"  {item}")
except Exception as e:
    print(f"  Not found: {e}")

# Check if products table has unique values we can use
print("\n=== Unique Values from master.products ===")
try:
    res = supabase_request('GET', 'products', params={'select': 'category,brand,division', 'limit': 50}, 
                          headers_extra={'Accept-Profile': 'master'})
    data = res.get('data', [])
    
    categories = sorted(set(d.get('category', '') for d in data if d.get('category')))
    brands = sorted(set(d.get('brand', '') for d in data if d.get('brand')))
    divisions = sorted(set(d.get('division', '') for d in data if d.get('division')))
    
    print(f"Categories ({len(categories)}): {categories[:10]}")
    print(f"Brands ({len(brands)}): {brands[:10]}")
    print(f"Divisions ({len(divisions)}): {divisions[:10]}")
except Exception as e:
    print(f"Error: {e}")
