
import asyncio
from supabase_client import get_supabase_admin, get_supabase_client
from dotenv import load_dotenv

load_dotenv()

async def force_super_admin():
    supabase = get_supabase_client()
    supabase_admin = get_supabase_admin()
    
    email = "asep_kiky@pinusmerahabadi.co.id"
    print(f"--- Forcing Super Admin for: {email} ---")
    
    # Get Auth ID
    res = supabase.schema('hr').table('employees').select('auth_user_id').eq('email', email).single().execute()
    auth_id = res.data['auth_user_id']
    
    # Update
    print(f"Updating Auth ID: {auth_id}")
    supabase_admin.auth.admin.update_user_by_id(
        auth_id, 
        {"user_metadata": {"role": "super_admin"}}
    )
    print("SUCCESS: Role updated to 'super_admin'.")

if __name__ == "__main__":
    asyncio.run(force_super_admin())
