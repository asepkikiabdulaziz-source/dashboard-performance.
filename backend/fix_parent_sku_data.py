"""
Fix parent SKU data by populating from _master_item.xlsx
This will correctly set parent_sku_code and parent_sku_name for product lineage
"""
import pandas as pd
from supabase_client import supabase_request

# Read master data
df = pd.read_excel('_master_item.xlsx')
df.columns = df.columns.str.upper()

print("=== FIXING PARENT SKU DATA ===\n")
print(f"Total products in Excel: {len(df)}")

# Get current products from database
res = supabase_request('GET', 'products', params={'select': 'sku_code,product_name'}, headers_extra={'Accept-Profile': 'master'})
db_products = {p['sku_code']: p['product_name'] for p in res.get('data', [])}
print(f"Total products in database: {len(db_products)}")

# Prepare updates
updates = []
skipped = []

for idx, row in df.iterrows():
    sku_code = str(row['KD_SKU'])
    parent_sku_code = str(row['KD_SKU_PARENT'])
    parent_sku_name = row.get('NAMA_SKU_PARENT', '')
    
    # Skip if SKU not in database
    if sku_code not in db_products:
        skipped.append(sku_code)
        continue
    
    # Only update if parent is different from self
    if sku_code != parent_sku_code:
        updates.append({
            'sku_code': sku_code,
            'parent_sku_code': parent_sku_code,
            'parent_sku_name': parent_sku_name if pd.notna(parent_sku_name) else None
        })

print(f"\nProducts to update: {len(updates)}")
print(f"Products skipped (not in DB): {len(skipped)}")

if len(updates) > 0:
    print(f"\n=== SAMPLE UPDATES (first 5) ===")
    for update in updates[:5]:
        print(f"SKU {update['sku_code']} -> Parent: {update['parent_sku_code']} ({update['parent_sku_name']})")
    
    confirm = input(f"\nProceed to update {len(updates)} products? (yes/no): ")
    
    if confirm.lower() == 'yes':
        success_count = 0
        error_count = 0
        
        for update in updates:
            try:
                supabase_request(
                    'PATCH',
                    'products',
                    params={'sku_code': f"eq.{update['sku_code']}"},
                    json_data={
                        'parent_sku_code': update['parent_sku_code'],
                        'parent_sku_name': update['parent_sku_name']
                    },
                    headers_extra={'Accept-Profile': 'master', 'Content-Profile': 'master', 'Prefer': 'return=minimal'}
                )
                success_count += 1
                if success_count % 100 == 0:
                    print(f"Updated {success_count} products...")
            except Exception as e:
                error_count += 1
                print(f"Error updating {update['sku_code']}: {e}")
        
        print(f"\n=== RESULTS ===")
        print(f"Successfully updated: {success_count}")
        print(f"Errors: {error_count}")
    else:
        print("Update cancelled.")
else:
    print("\nNo updates needed - all products already have correct parent SKU.")
