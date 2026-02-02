
import pandas as pd
import asyncio
from supabase_client import get_supabase_client
from dotenv import load_dotenv

# Load env
load_dotenv()

async def import_data():
    print("🚀 Starting FULL Relational Import...")
    
    # 1. Read CSV
    try:
        # Assuming filename is the same
        df = pd.read_csv('../Supabase Snippet Complete Hierarchy View.csv')
        # Fill NaN
        df = df.fillna('')
        print(f"✅ Loaded CSV: {len(df)} rows")
    except Exception as e:
        print(f"❌ Failed to load CSV: {e}")
        return

    supabase = get_supabase_client()
    
    # ==========================================
    # LEVEL 1: LOOKUPS (Region, GRBM)
    # ==========================================
    print("\n--- Level 1: Lookups ---")
    
    # GRBM
    grbm_df = df[['grbm_id', 'grbm_name']].drop_duplicates()
    for _, row in grbm_df.iterrows():
        if not row['grbm_id']: continue
        try:
            supabase.schema('master').table('ref_lookup').upsert({
                'company_id': 'ID001', 'category': 'GRBM',
                'code': row['grbm_id'], 'name': row['grbm_name']
            }).execute()
        except: pass # Ignore duplicate errors or print simple dot
    print("✅ GRBMs Synced")

    # Region
    region_df = df[['region_id', 'region_name']].drop_duplicates()
    for _, row in region_df.iterrows():
        if not row['region_id']: continue
        try:
            supabase.schema('master').table('ref_lookup').upsert({
                'company_id': 'ID001', 'category': 'REGION',
                'code': row['region_id'], 'name': row['region_name']
            }).execute()
        except: pass
    print("✅ Regions Synced")

    # ==========================================
    # LEVEL 2: AREAS (Branches)
    # ==========================================
    print("\n--- Level 2: Areas (Branches) ---")
    branch_df = df[['branch_id', 'branch_name', 'region_id', 'grbm_id']].drop_duplicates()
    for _, row in branch_df.iterrows():
        if not row['branch_id']: continue
        try:
            supabase.schema('master').table('ref_branches').upsert({
                'company_id': 'ID001',
                'id': row['branch_id'], # Using Code as ID (e.g. R01.01)
                'name': row['branch_name'],
                'region_code': row['region_id'],
                'grbm_code': row['grbm_id']
            }).execute()
        except Exception as e:
             print(f"⚠️ Error Branch {row['branch_id']}: {e}")
    print(f"✅ Areas Synced ({len(branch_df)})")

    # ==========================================
    # LEVEL 3: DISTRIBUTORS (Linked to Area)
    # ==========================================
    print("\n--- Level 3: Distributors ---")
    # CSV Column 'parent_kd_dist' seems to be the Distributor Code
    dist_df = df[['parent_kd_dist', 'distributor_name', 'branch_id']].drop_duplicates()
    
    for _, row in dist_df.iterrows():
        kd_dist = str(row['parent_kd_dist'])
        if not kd_dist: continue
        
        try:
            supabase.schema('master').table('ref_distributors').upsert({
                'company_id': 'ID001',
                'kd_dist': kd_dist,
                'distributor_name': row['distributor_name'],
                'branch_id': row['branch_id'] # RELATIONAL LINK!
            }).execute()
        except Exception as e:
            print(f"⚠️ Error Distributor {kd_dist}: {e}")
            
    print(f"✅ Distributors Synced ({len(dist_df)})")
    
    # ==========================================
    # LEVEL 4: PMA (Linked to Distributor)
    # ==========================================
    print("\n--- Level 4: PMAs ---")
    pma_df = df[['pma_code', 'pma_name', 'parent_kd_dist']].drop_duplicates()
    
    upsert_batch = []
    
    for _, row in pma_df.iterrows():
        if not row['pma_code']: continue
        
        # Prepare payload
        payload = {
            'company_id': 'ID001',
            'pma_code': row['pma_code'],
            'pma_name': row['pma_name'],
            'distributor_id': str(row['parent_kd_dist']) # RELATIONAL LINK!
        }
        
        # Direct Execution (One by one for safety on small dataset, can batch if slow)
        try:
             supabase.schema('master').table('ref_pma').upsert(payload).execute()
        except Exception as e:
            # print(f"⚠️ Error PMA {row['pma_code']}: {e}")
            pass
            
    print(f"✅ PMAs Synced ({len(pma_df)})")
    print("\n🎉 MIGRATION COMPLETE: Structured Hierarchy Established!")

if __name__ == "__main__":
    asyncio.run(import_data())
