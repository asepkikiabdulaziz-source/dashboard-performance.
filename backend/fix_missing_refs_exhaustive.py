"""
Final robust fix for missing references
Matches import_all_products_CORRECTED.py logic exactly
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

def insert_missing(table, missing_ids, id_col='id', default_fields=None):
    if not missing_ids:
        print(f"No missing items for {table}")
        return
    
    print(f"Inserting {len(missing_ids)} missing items into {table}: {missing_ids}")
    batch = []
    for mid in missing_ids:
        item = {id_col: mid, 'name': mid}
        if default_fields:
            item.update(default_fields)
        batch.append(item)
    
    try:
        supabase_request(
            'POST', 
            table, 
            json_data=batch, 
            headers_extra={'Accept-Profile': 'master', 'Content-Profile': 'master', 'Prefer': 'return=minimal'}
        )
        print(f"Successfully inserted into {table}")
    except Exception as e:
        print(f"Error inserting into {table}: {e}")

# Exact mapping used in import script
excel_principals = {str(row.get('PRINC 2', '')).strip() for _, row in df.iterrows() if pd.notna(row.get('PRINC 2'))}
excel_brands = {str(row.get('BRAND', '')).strip() for _, row in df.iterrows() if pd.notna(row.get('BRAND'))}
excel_categories = {str(row.get('CATEGORY', '')).strip() for _, row in df.iterrows() if pd.notna(row.get('CATEGORY'))}

# Remove empty/nan strings
excel_principals.discard(''); excel_principals.discard('nan')
excel_brands.discard(''); excel_brands.discard('nan')
excel_categories.discard(''); excel_categories.discard('nan')

db_principals = get_db_ids('ref_principals', 'id')
db_brands = get_db_ids('ref_brands', 'id')
db_categories = get_db_ids('ref_categories', 'id')

missing_principals = excel_principals - db_principals
missing_brands = excel_brands - db_brands
missing_categories = excel_categories - db_categories

print(f"Missing Principals: {len(missing_principals)}")
print(f"Missing Brands: {len(missing_brands)}")
print(f"Missing Categories: {len(missing_categories)}")

insert_missing('ref_principals', missing_principals, id_col='id', default_fields={'company_id': 'ID001'})
insert_missing('ref_brands', missing_brands, id_col='id', default_fields={'company_id': 'ID001'})
insert_missing('ref_categories', missing_categories, id_col='id', default_fields={'company_id': 'ID001'})
