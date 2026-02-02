
import asyncio
from supabase_client import get_supabase_client
from dotenv import load_dotenv

load_dotenv()

async def analyze_pairs():
    print("--- Analyzing Region-GRBM Pairs ---")
    supabase = get_supabase_client()
    
    response = supabase.schema('master').table('ref_branches').select('region_code, grbm_code').execute()
    data = response.data
    
    pairs = set()
    region_map = {}
    
    for row in data:
        r = row.get('region_code')
        g = row.get('grbm_code')
        if r and g:
            pairs.add((r, g))
            if r not in region_map:
                region_map[r] = set()
            region_map[r].add(g)
            
    print(f"Total Unique Pairs: {len(pairs)}")
    for r, g in pairs:
        print(f"Region: {r} -> GRBM: {g}")
        
    print("\n--- Consistency Check ---")
    inconsistent = False
    for r, g_set in region_map.items():
        if len(g_set) > 1:
            print(f"CONFLICT: Region {r} has multiple GRBMs: {g_set}")
            inconsistent = True
            
    if not inconsistent:
        print("PERFECT: Each Region maps to exactly one GRBM.")

if __name__ == "__main__":
    asyncio.run(analyze_pairs())
