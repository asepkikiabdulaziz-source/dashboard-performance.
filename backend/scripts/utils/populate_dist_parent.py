
import asyncio
import csv
import os
from supabase_client import get_supabase_client
from dotenv import load_dotenv

load_dotenv()

CSV_FILE = "../Supabase Snippet Complete Hierarchy View.csv"

async def populate_parent_dist():
    print("--- Populating parent_kd_dist ---")
    supabase = get_supabase_client()
    
    if not os.path.exists(CSV_FILE):
        print(f"❌ CSV file not found at {CSV_FILE}")
        return

    updates = {} # Map kd_dist -> parent_kd_dist
    
    with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # CSV Headers: ..., parent_kd_dist, ..., kd_dist_ori, ...
            # we assume DB kd_dist matches CSV kd_dist_ori or distributor_id?
            # Let's try matching on 'kd_dist' = row['kd_dist_ori']
            
            kd_dist = row.get('kd_dist_ori')
            parent = row.get('parent_kd_dist')
            
            if kd_dist and parent:
                updates[kd_dist] = parent

    print(f"Found {len(updates)} distributors to update.")
    
    # Batch update? Supabase doesn't support bulk update easily without loop or case.
    # We will loop for now, it's only ~100 distributors likely.
    
    count = 0
    for kd, parent in updates.items():
        try:
            # Update where kd_dist = kd
            res = supabase.schema('master').table('ref_distributors')\
                .update({'parent_kd_dist': parent})\
                .eq('kd_dist', kd)\
                .execute()
            if res.data:
                count += 1
                if count % 10 == 0:
                    print(f"Updated {count}...")
        except Exception as e:
            print(f"Failed to update {kd}: {e}")

    print(f"✅ Finished. Updated {count} distributors.")

if __name__ == "__main__":
    asyncio.run(populate_parent_dist())
