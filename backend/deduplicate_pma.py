
import asyncio
from supabase_client import get_supabase_client
from dotenv import load_dotenv

load_dotenv()

async def deduplicate_pma():
    print("--- Deduplicating PMA Entries ---")
    supabase = get_supabase_client()
    
    # Fetch all IDs and Codes
    response = supabase.schema('master').table('ref_pma').select("id, pma_code").execute()
    data = response.data
    
    seen = {}
    duplicates = []
    
    for row in data:
        code = row['pma_code']
        if code in seen:
            duplicates.append(row['id'])
        else:
            seen[code] = row['id']
            
    print(f"Found {len(duplicates)} duplicates. Deleting...")
    
    if duplicates:
        for dup_id in duplicates:
            print(f"Deleting duplicate ID: {dup_id}")
            supabase.schema('master').table('ref_pma').delete().eq('id', dup_id).execute()
            
    print("Deduplication complete.")

if __name__ == "__main__":
    asyncio.run(deduplicate_pma())
