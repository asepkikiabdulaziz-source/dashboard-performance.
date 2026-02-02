
import pandas as pd
import asyncio
from supabase_client import get_supabase_client
from dotenv import load_dotenv

# Load env
load_dotenv()

async def import_data():
    print("🚀 Starting CSV Import to New Lookup Schema...")
    
    # 1. Read CSV
    try:
        df = pd.read_csv('../Supabase Snippet Complete Hierarchy View.csv')
        print(f"✅ Loaded CSV: {len(df)} rows")
    except Exception as e:
        print(f"❌ Failed to load CSV: {e}")
        return

    supabase = get_supabase_client()

    # 2. Extract and Upload Lookups (GRBM & REGION)
    # Use Set to get unique values
    print("--- Processing Lookups ---")
    
    # GRBM
    grbm_list = df[['grbm_id', 'grbm_name']].drop_duplicates().to_dict('records')
    for item in grbm_list:
        payload = {
            'company_id': 'ID001', # Default
            'category': 'GRBM',
            'code': item['grbm_id'],
            'name': item['grbm_name']
        }
        # Upsert (Insert or Update)
        try:
            supabase.schema('master').table('ref_lookup').upsert(payload).execute()
        except Exception as e:
            print(f"⚠️ Error upserting GRBM {item['grbm_id']}: {e}")
            
    print(f"✅ Processed {len(grbm_list)} GRBMs")

    # REGION
    region_list = df[['region_id', 'region_name']].drop_duplicates().to_dict('records')
    for item in region_list:
        payload = {
            'company_id': 'ID001',
            'category': 'REGION',
            'code': item['region_id'],
            'name': item['region_name']
        }
        try:
            supabase.schema('master').table('ref_lookup').upsert(payload).execute()
        except Exception as e:
             print(f"⚠️ Error upserting REGION {item['region_id']}: {e}")

    print(f"✅ Processed {len(region_list)} Regions")

    # 3. Process Branches (Link to Lookup)
    print("--- Processing Branches ---")
    branch_list = df[['branch_id', 'branch_name', 'region_id', 'grbm_id']].drop_duplicates().to_dict('records')
    
    for item in branch_list:
        payload = {
            'company_id': 'ID001',
            'id': item['branch_id'],
            'name': item['branch_name'],
            'region_code': item['region_id'], # New Flat Link
            'grbm_code': item['grbm_id']      # New Flat Link
        }
        try:
            supabase.schema('master').table('ref_branches').upsert(payload).execute()
        except Exception as e:
            print(f"⚠️ Error upserting Branch {item['branch_id']}: {e}")

    print(f"✅ Processed {len(branch_list)} Branches")
    
    # Optional: Distributors and PMA could be added here too if needed
    # But checking user request, primarily Lookups and Branches are critical for the new UI.
    
    print("\n🎉 Import Finished! The 'ref_lookup' and 'ref_branches' tables are now populated from CSV.")

if __name__ == "__main__":
    asyncio.run(import_data())
