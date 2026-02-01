
import asyncio
from supabase_client import get_supabase_client
from dotenv import load_dotenv

load_dotenv()

async def verify():
    print("--- Verifying PMA FK Constraints ---")
    supabase = get_supabase_client()
    
    try:
        # Test if we can join ref_pma with ref_distributors
        print("Testing Join: ref_pma + ref_distributors")
        
        # Simple join attempt
        try:
             res = supabase.schema('master').table('ref_pma')\
                .select("*, ref_distributors(distributor_name)").limit(1).execute()
             print("✅ Join Worked! (FK exists)")
        except Exception as e:
            print(f"❌ Join Failed: {e}")
            print("Reason: ID 'ref_distributors' not found likely means no FK detected.")

    except Exception as e:
        print(f"General Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
