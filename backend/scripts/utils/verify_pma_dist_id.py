
import asyncio
from supabase_client import get_supabase_client
from dotenv import load_dotenv
import json

load_dotenv()

async def verify_dist_id():
    print("--- Verifying Distributor ID vs Kd Dist Ori ---")
    supabase = get_supabase_client()
    
    # Check P243
    print("Checking P243...")
    res = supabase.schema('master').table('ref_pma')\
        .select("pma_code, distributor_id, kd_dist_ori")\
        .eq('pma_code', 'P243')\
        .execute()
        
    print(json.dumps(res.data, indent=2))

if __name__ == "__main__":
    asyncio.run(verify_dist_id())
