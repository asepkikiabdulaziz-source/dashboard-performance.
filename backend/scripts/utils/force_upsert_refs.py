"""
Force upsert all references from Excel
"""
import pandas as pd
from supabase_client import supabase_request

# Read Excel
df = pd.read_excel('_master_item.xlsx')

def upsert_refs(table, values, id_col='id', default_fields=None):
    if values is None or (hasattr(values, 'empty') and values.empty):
        return
    
    unique_vals = {str(v).strip() for v in values if pd.notna(v) and str(v).strip() != '' and str(v).strip() != 'nan'}
    print(f"Upserting {len(unique_vals)} items into {table}...")
    
    batch = []
    for val in unique_vals:
        item = {id_col: val, 'name': val}
        if default_fields:
            item.update(default_fields)
        batch.append(item)
    
    # Batch in 50
    for i in range(0, len(batch), 50):
        sub_batch = batch[i:i+50]
        try:
            # PostgREST upsert: POST with resolution=merge-duplicates
            supabase_request(
                'POST', 
                table, 
                json_data=sub_batch, 
                headers_extra={
                    'Accept-Profile': 'master', 
                    'Content-Profile': 'master', 
                    'Prefer': 'resolution=merge-duplicates'
                }
            )
        except Exception as e:
            print(f"Error in batch {i//50}: {e}")

upsert_refs('ref_principals', df['PRINC 2'], default_fields={'company_id': 'ID001'})
upsert_refs('ref_brands', df['BRAND'], default_fields={'company_id': 'ID001'})
excel_categories = df['CATEGORY'] if 'CATEGORY' in df.columns else df['CATEGORY_ID']
upsert_refs('ref_categories', excel_categories, default_fields={'company_id': 'ID001'})

print("\nDone upserting references.")
