
import asyncio
from supabase_client import get_supabase_client
from dotenv import load_dotenv

load_dotenv()

async def audit_schema_consistency():
    supabase = get_supabase_client()
    tables = ['ref_branches', 'ref_distributors', 'ref_pma', 'ref_lookup', 'price_zones']
    
    print("--- 1. Checking company_id Presence ---")
    for table in tables:
        try:
            # excessive limit to just get columns
            res = supabase.schema('master').table(table).select("*").limit(1).execute()
            if res.data:
                cols = res.data[0].keys()
                has_company = 'company_id' in cols
                print(f"{table}: company_id present? {has_company} | Columns: {list(cols)}")
                
                # Check sample content for company_id consistency
                print(f"   Sample company_id: {res.data[0].get('company_id')}")
            else:
                 # Try to get columns even if empty (hard via select *, assume empty means table exists)
                 print(f"{table}: Table exists but is EMPTY.")
        except Exception as e:
            print(f"{table}: ERROR - {e}")

if __name__ == "__main__":
    asyncio.run(audit_schema_consistency())
