
import asyncio
from supabase_client import get_supabase_client
from dotenv import load_dotenv
import json

load_dotenv()

async def verify_data_presence():
    print("--- Verifying Data Presence ---")
    supabase = get_supabase_client()
    
    # 1. Check ref_pma for kd_dist_ori
    print("\n[ref_pma] Checking kd_dist_ori...")
    pma_res = supabase.schema('master').table('ref_pma').select("pma_code, kd_dist_ori").limit(5).execute()
    print(json.dumps(pma_res.data, indent=2))

    # 2. Check ref_distributors for parent_kd_dist
    print("\n[ref_distributors] Checking parent_kd_dist...")
    dist_res = supabase.schema('master').table('ref_distributors').select("kd_dist, parent_kd_dist").limit(5).execute()
    print(json.dumps(dist_res.data, indent=2))
    
    # 3. Check the Join used in API (admin_master.py)
    # The API does: query = supabase.table(table_name).select(select_query)
    # For PMA: select(*, ref_distributors(*))
    print("\n[API Simulation] Checking Join...")
    join_res = supabase.schema('master').table('ref_pma').select("*, ref_distributors(*)").limit(5).execute()
    # We only print specific fields to avoid huge output
    for row in join_res.data:
        dist = row.get('ref_distributors')
        print(f"PMA: {row.get('pma_code')} | KdOri: {row.get('kd_dist_ori')} | Parent: {dist.get('parent_kd_dist') if dist else 'None'}")

if __name__ == "__main__":
    asyncio.run(verify_data_presence())
