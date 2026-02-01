
import asyncio
from supabase_client import get_supabase_client
from dotenv import load_dotenv

load_dotenv()

async def find_company_table():
    supabase = get_supabase_client()
    print("--- Searching for Company Tables ---")
    candidates = ['ref_company', 'companies', 'ref_companies', 'organization', 'ref_organization']
    
    for table in candidates:
        try:
            res = supabase.schema('master').table(table).select("*").limit(1).execute()
            print(f"FOUND TABLE: {table}")
            if res.data:
                print(f"Columns: {list(res.data[0].keys())}")
        except Exception as e:
            pass

if __name__ == "__main__":
    asyncio.run(find_company_table())
