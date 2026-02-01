"""
Robust auto-fix missing references in DB
Ensures all IDs are stripped and consistent
"""
import pandas as pd
from supabase_client import supabase_request

# Read Excel
df = pd.read_excel('_master_item.xlsx')

def get_db_ids(table, id_col='id'):
    try:
        res = supabase_request('GET', table, headers_extra={'Accept-Profile': 'master'})
        # Return stripped IDs
        return {str(r[id_col]).strip() for r in res.get('data', [])}
    except Exception as e:
        print(f"Error fetching {table}: {e}")
        return set()

def insert_missing(table, missing_ids, id_col='id', default_fields=None):
    if not missing_ids:
        print(f"No missing items for {table}")
        return
    
    print(f"Inserting {len(missing_ids)} missing items into {table}...")
    batch = []
    for mid in missing_ids:
        # mid is already stripped
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

# Columns for reference tables
# ref_principals: company_id, id, name
# ref_brands: company_id, id, name
# ref_categories: company_id, id, name

# Get unique values from Excel, stripped
excel_principals = {str(v).strip() for v in df['PRINC 2'].dropna().unique()}
excel_brands = {str(v).strip() for v in df['BRAND'].dropna().unique()}
excel_categories = {str(v).strip() for v in df['CATEGORY'].dropna().unique()}

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
