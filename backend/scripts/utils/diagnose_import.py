"""
Diagnostic script to find why 81 products fail to import
"""
import pandas as pd
from supabase_client import supabase_request

# Read Excel
df = pd.read_excel('_master_item.xlsx')

def get_db_ids(table, id_col='id'):
    try:
        res = supabase_request('GET', table, headers_extra={'Accept-Profile': 'master'})
        return {str(r[id_col]).strip() for r in res.get('data', [])}
    except Exception as e:
        print(f"Error fetching {table}: {e}")
        return set()

db_principals = get_db_ids('ref_principals', 'id')
db_brands = get_db_ids('ref_brands', 'id')
db_categories = get_db_ids('ref_categories', 'id')

print(f"DB Principals: {len(db_principals)}")
print(f"DB Brands: {len(db_brands)}")
print(f"DB Categories: {len(db_categories)}")

failing_rows = []

for idx, row in df.iterrows():
    sku = str(row['KD_SKU']).strip()
    if not sku or sku == 'nan':
        continue
        
    princ = str(row.get('PRINC 2', '')).strip()
    brand = str(row.get('BRAND', '')).strip()
    cat = str(row.get('CATEGORY', '')).strip()
    
    issues = []
    if princ and princ != 'nan' and princ not in db_principals:
        issues.append(f"Principal '{princ}' missing")
    if brand and brand != 'nan' and brand not in db_brands:
        issues.append(f"Brand '{brand}' missing")
    if cat and cat != 'nan' and cat not in db_categories:
        issues.append(f"Category '{cat}' missing")
        
    if issues:
        failing_rows.append({
            'row': idx + 2, # Excel row number
            'sku': sku,
            'name': row.get('NAMA_SKU'),
            'issues': "; ".join(issues)
        })

print(f"\nFound {len(failing_rows)} rows with potential FK issues:")
for fr in failing_rows[:20]:
    print(f"Row {fr['row']} (SKU {fr['sku']}): {fr['issues']}")

if len(failing_rows) > 20:
    print(f"... and {len(failing_rows)-20} more.")

# Also check for company_id ID001 existence if it's a FK
try:
    res = supabase_request('GET', 'ref_companies', headers_extra={'Accept-Profile': 'master'})
    companies = {r['id'] for r in res.get('data', [])}
    print(f"\nValid companies: {companies}")
except:
    print("\nCould not check ref_companies")
