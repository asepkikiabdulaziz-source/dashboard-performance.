
import asyncio
from supabase_client import get_supabase_client
from dotenv import load_dotenv
import json

load_dotenv()

async def verify_pma_id():
    print("--- Verifying PMA ID Field ---")
    supabase = get_supabase_client()
    try:
        # Fetch 1 PMA row
        # using select("*") should include 'id' now
        response = supabase.schema('master').table('ref_pma')\
            .select("*")\
            .limit(1)\
            .execute()
        
        if response.data:
            row = response.data[0]
            if 'id' in row:
                print(f"✅ ID Found: {row['id']}")
            else:
                print("❌ ID Missing from response!")
                print("Keys:", row.keys())
        else:
            print("No data found.")

    except Exception as e:
        print(f"❌ Query Failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_pma_id())
