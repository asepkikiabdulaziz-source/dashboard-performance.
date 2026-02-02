
import asyncio
from supabase_client import get_supabase_client
from dotenv import load_dotenv
import json

load_dotenv()

async def verify_pma_endpoint():
    print("--- Verifying PMA Endpoint (Deep Join) ---")
    supabase = get_supabase_client()
    try:
        # Replicating the query in admin_master.py
        # ref_pma -> ref_distributors -> ref_branches
        response = supabase.schema('master').table('ref_pma')\
            .select("*, ref_distributors(distributor_name, ref_branches:ref_branches!fk_distributors_branch(name, region_code, grbm_code))")\
            .limit(1)\
            .execute()
        
        print("✅ Query Successful!")
        if response.data:
            print("Sample Data:", json.dumps(response.data[0], indent=2))
        else:
            print("No data found (Table might be empty if import failed).")

    except Exception as e:
        print(f"❌ Query Failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_pma_endpoint())
