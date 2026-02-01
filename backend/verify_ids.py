
import asyncio
from supabase_client import get_supabase_client
from dotenv import load_dotenv

load_dotenv()

async def verify_specific_ids():
    supabase = get_supabase_client()
    ids_to_check = ['SD-SUM', 'SUM', 'SD-PAPUA']
    print(f"--- Checking for IDs: {ids_to_check} ---")
    
    response = supabase.schema('master').table('price_zones').select("*").in_('id', ids_to_check).execute()
    
    found_ids = [row['id'] for row in response.data]
    print(f"Found in master.price_zones: {found_ids}")
    
    missing = set(ids_to_check) - set(found_ids)
    if missing:
        print(f"MISSING IDs: {missing}")
    else:
        print("All sample IDs found!")

if __name__ == "__main__":
    asyncio.run(verify_specific_ids())
