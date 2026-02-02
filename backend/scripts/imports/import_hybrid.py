"""
Hybrid import script: Batching + Row-level Retry
Fast and diagnostic.
"""
import pandas as pd
from supabase_client import supabase_request

# Read Excel
df = pd.read_excel('_master_item.xlsx')
print(f"Total products to import: {len(df)}")

# Prepare results
success_count = 0
error_count = 0
errors = []

# Clear existing products
try:
    supabase_request('DELETE', 'products', params={'company_id': 'eq.ID001'}, headers_extra={'Accept-Profile': 'master', 'Content-Profile': 'master', 'Prefer': 'return=minimal'})
    print("Old products cleared.")
except Exception as e:
    print(f"Warning: Could not clear products: {e}")

# Process rows into list
products = []
for idx, row in df.iterrows():
    sku = str(row['KD_SKU']).strip()
    if not sku or sku == 'nan':
        continue
    
    is_active = True if row.get('STATUS_PRODUK') == 'Active' else False
    product = {
        'company_id': 'ID001',
        'sku_code': sku,
        'product_name': str(row['NAMA_SKU']).strip() if pd.notna(row['NAMA_SKU']) else None,
        'short_name': str(row.get('MARK', '')).strip() if pd.notna(row.get('MARK')) else None,
        'parent_sku_code': str(row['KD_SKU_PARENT']).strip() if pd.notna(row['KD_SKU_PARENT']) else sku,
        'parent_sku_name': str(row['NAMA_SKU_PARENT']).strip() if pd.notna(row['NAMA_SKU_PARENT']) else None,
        'principal_id': str(row.get('PRINC 2', '')).strip() if pd.notna(row.get('PRINC 2')) else None,
        'brand_id': str(row.get('BRAND', '')).strip() if pd.notna(row.get('BRAND')) else None,
        'category_id': str(row.get('CATEGORY', '')).strip() if pd.notna(row.get('CATEGORY')) else None,
        'variant': str(row.get('FLAVOUR', '')).strip() if pd.notna(row.get('FLAVOUR')) else None,
        'price_segment': str(row.get('ECERAN (KSNI)', '')).strip() if pd.notna(row.get('ECERAN (KSNI)')) else None,
        'uom_small': 'PCS',
        'uom_medium': str(row.get('UOM 2', '')).strip() if pd.notna(row.get('UOM 2')) and str(row.get('UOM 2', '')).strip() != '' else 'BOX',
        'isi_pcs_per_medium': int(row.get('BOX / PCS', 0)) if pd.notna(row.get('BOX / PCS')) and row.get('BOX / PCS', 0) > 0 else None,
        'uom_large': str(row.get('UOM 3', '')).strip() if pd.notna(row.get('UOM 3')) and str(row.get('UOM 3', '')).strip() != '' else 'KRT',
        'isi_pcs_per_large': int(row.get('BOX / CRT', 0)) if pd.notna(row.get('BOX / CRT')) and row.get('BOX / CRT', 0) > 0 else None,
        'is_active': is_active,
        'is_npl': True if row.get('NPL') == 'NPL' else False,
    }
    if product['isi_pcs_per_large'] and product['isi_pcs_per_medium']:
        product['isi_pcs_per_large'] *= product['isi_pcs_per_medium']
    products.append(product)

def import_single(p):
    global success_count, error_count
    try:
        supabase_request('POST', 'products', json_data=p, headers_extra={'Accept-Profile': 'master', 'Content-Profile': 'master', 'Prefer': 'return=minimal'})
        success_count += 1
        return True
    except Exception as e:
        error_count += 1
        detail = e.response.text if hasattr(e, 'response') and e.response else str(e)
        msg = f"SKU {p['sku_code']}: {detail}"
        errors.append(msg)
        print(f"  FAILED: {msg}")
        return False

# Import in batches
batch_size = 50
for i in range(0, len(products), batch_size):
    batch = products[i:i+batch_size]
    try:
        supabase_request('POST', 'products', json_data=batch, headers_extra={'Accept-Profile': 'master', 'Content-Profile': 'master', 'Prefer': 'return=minimal'})
        success_count += len(batch)
        print(f"Imported {success_count}/{len(products)}...")
    except Exception:
        # Batch failed, retry one by one
        print(f"Batch {i//batch_size + 1} failed, retrying row-by-row...")
        for p in batch:
            import_single(p)

print(f"\nFinal Result: {success_count} success, {error_count} errors.")
if errors:
    with open('import_errors_final.txt', 'w') as f:
        f.write("\n".join(errors))
