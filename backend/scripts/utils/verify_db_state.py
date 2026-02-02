
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

async def verify():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        return

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Accept-Profile": "master",
        "Content-Profile": "master"
    }

    async with httpx.AsyncClient() as client:
        print("--- VERIFYING DB STATE ---")

        # 1. Check ref_lookup
        try:
            resp = await client.get(f"{SUPABASE_URL}/rest/v1/ref_lookup?select=count", headers=headers)
            if resp.status_code == 200:
                print("[OK] Table 'ref_lookup' exists.")
            else:
                print(f"[MISSING] Table 'ref_lookup' NOT found (Status: {resp.status_code})")
        except:
             print("[ERROR] Check ref_lookup failed")

        # 2. Check ref_branches columns
        try:
            # Try to select the new column
            resp = await client.get(f"{SUPABASE_URL}/rest/v1/ref_branches?select=region_code&limit=1", headers=headers)
            if resp.status_code == 200:
                print("[OK] Column 'region_code' in 'ref_branches' exists.")
            else:
                print(f"[MISSING] Column 'region_code' in 'ref_branches' NOT found.")
        except:
            print("[ERROR] Check ref_branches failed")
            
        # 3. Check ref_pma columns (from simplified migration)
        try:
            resp = await client.get(f"{SUPABASE_URL}/rest/v1/ref_pma?select=distributor_id&limit=1", headers=headers)
            if resp.status_code == 200:
                print("[OK] Column 'distributor_id' in 'ref_pma' exists.")
            else:
                print(f"[MISSING] Column 'distributor_id' in 'ref_pma' NOT found.")
        except:
             print("[ERROR] Check ref_pma failed")

if __name__ == "__main__":
    asyncio.run(verify())
