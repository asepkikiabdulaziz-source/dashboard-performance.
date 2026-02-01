
import asyncio
from supabase_client import get_supabase_client
from dotenv import load_dotenv

load_dotenv()

async def add_super_admin_role():
    supabase = get_supabase_client()
    print("--- Adding Role: Super Admin ---")
    data = {"role_id": "super_admin", "role_name": "Super Administrator", "level": 99}
    try:
        # Check if exists first (or upsert)
        res = supabase.schema('master').table('ref_role').upsert(data).execute()
        print("Role added/updated:", res.data)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(add_super_admin_role())
