"""
Auto-fix missing references in DB
"""
import pandas as pd
from supabase_client import supabase_request

# Read Excel
df = pd.read_excel('_master_item.xlsx')

def get_db_ids(table, id_col='id'):
    try:
        res = supabase_request('GET', table, headers_extra={'Accept-Profile': 'master'})
        return {r[id_col] for r in res.get('data', [])}
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
        item = {id_col: mid, 'name': mid} # Default name to ID
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
        if hasattr(e, 'response') and e.response is not None:
            print(f"Details: {e.response.text}")

# Actual Columns for reference tables (guesses based on schema)
# ref_principals: company_id, id, name
# ref_brands: company_id, id, name
# ref_categories: company_id, id, name

excel_principals = set(df['PRINC 2'].dropna().unique())
excel_brands = set(df['BRAND'].dropna().unique())
excel_categories = set(df['CATEGORY'].dropna().unique())

db_principals = get_db_ids('ref_principals', 'id')
db_brands = get_db_ids('ref_brands', 'id')
db_categories = get_db_ids('ref_categories', 'id')

missing_principals = excel_principals - db_principals
missing_brands = excel_brands - db_brands
missing_categories = excel_categories - db_categories

insert_missing('ref_principals', missing_principals, id_col='id', default_fields={'company_id': 'ID001'})
insert_missing('ref_brands', missing_brands, id_col='id', default_fields={'company_id': 'ID001'})
insert_missing('ref_categories', missing_categories, id_col='id', default_fields={'company_id': 'ID001'})
