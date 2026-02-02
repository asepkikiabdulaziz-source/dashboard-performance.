
import asyncio
from supabase_client import get_supabase_client
from dotenv import load_dotenv

load_dotenv()

async def check_counts():
    print("--- Checking Import Progress ---")
    supabase = get_supabase_client()
    try:
        # Check counts for each table
        tables = ['ref_branches', 'ref_distributors', 'ref_pma']
        for t in tables:
            res = supabase.schema('master').table(t).select("*", count='exact').limit(1).execute()
            print(f"Table '{t}': {res.count} rows")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_counts())
