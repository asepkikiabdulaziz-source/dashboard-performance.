
import asyncio
from supabase_client import get_supabase_client
from dotenv import load_dotenv

load_dotenv()

async def find_price_tables():
    supabase = get_supabase_client()
    print("--- Searching for Price/Prize Tables ---")
    # Trick: Try to valid master.ref_price_zones or master.prize_zones
    candidates = ['ref_price_zones', 'prize_zones', 'ref_prize_zones', 'price_zones']
    
    for table in candidates:
        try:
            res = supabase.schema('master').table(table).select("*").limit(1).execute()
            print(f"FOUND TABLE: {table}")
            if res.data:
                print(f"Columns: {list(res.data[0].keys())}")
        except Exception as e:
            # Table likely doesn't exist
            pass

if __name__ == "__main__":
    asyncio.run(find_price_tables())
