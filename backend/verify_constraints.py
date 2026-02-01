
import asyncio
from supabase_client import get_supabase_client
from dotenv import load_dotenv

load_dotenv()

async def verify():
    print("--- Verifying FK Constraints ---")
    supabase = get_supabase_client()
    
    # Check constraints on ref_distributors
    try:
        # We can't query information_schema directly via Supabase client usually (unless exposed).
        # But we can try 'rpc' if we had a function.
        # Alternatively, assume we can't seeing as we are "client".
        # But wait, I can use the 'debug_distributors.py' to try fetching without join first.
        
        # 1. Fetch raw distributors to see if 'branch_id' column even exists
        print("Checking column 'branch_id' in 'ref_distributors'...")
        res = supabase.schema('master').table('ref_distributors').select("*").limit(1).execute()
        if res.data:
            print("Row 1 keys:", res.data[0].keys())
        else:
            print("Table empty, checking headers not possible via data.")
            
        # 2. Try explicit join syntax hints using multiple variations
        # Attempt 1: Standard
        # Attempt 2: !inner
        # Attempt 3: !fk_name
        
        print("\nTesting Query Variations:")
        
        # V1
        try:
             res = supabase.schema('master').table('ref_distributors')\
                .select("*, ref_branches!fk_distributors_branch(name)").limit(1).execute()
             print("✅ V1 (Named FK) Worked!")
        except Exception as e:
            print(f"❌ V1 Failed: {e}")

        # V2: Using column name in join? PostgREST syntax usually infers.
        
    except Exception as e:
        print(f"General Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
