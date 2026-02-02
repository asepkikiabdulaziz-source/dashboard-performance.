"""
Compare reference data Excel vs DB
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

excel_principals = set(df['PRINC 2'].dropna().unique())
excel_brands = set(df['BRAND'].dropna().unique())
excel_categories = set(df['CATEGORY'].dropna().unique())

db_principals = get_db_ids('ref_principals', 'id')
db_brands = get_db_ids('ref_brands', 'id')
db_categories = get_db_ids('ref_categories', 'id')

missing_principals = excel_principals - db_principals
missing_brands = excel_brands - db_brands
missing_categories = excel_categories - db_categories

print(f"=== MISSING PRINCIPALS ({len(missing_principals)}) ===")
print(sorted(list(missing_principals)))

print(f"\n=== MISSING BRANDS ({len(missing_brands)}) ===")
print(sorted(list(missing_brands)))

print(f"\n=== MISSING CATEGORIES ({len(missing_categories)}) ===")
print(sorted(list(missing_categories)))
