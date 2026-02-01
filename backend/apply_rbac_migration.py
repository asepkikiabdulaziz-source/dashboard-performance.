
import asyncio
import os
from supabase_client import get_supabase_client
from dotenv import load_dotenv

load_dotenv()

async def apply_migration():
    supabase = get_supabase_client()
    
    # Read SQL file
    try:
        with open('migration_rbac_init.sql', 'r') as f:
            sql_content = f.read()
            
        print("--- Applying RBAC Migration ---")
        
        # Split by statements if possible, or execute as block if client supports it.
        # Supabase Python client .rpc() usually calls function, .update/select are builders.
        # Direct SQL execution is not standard in js client unless via rpc to sql function,
        # BUT many users use a custom PG conn or similar.
        # Assuming we have a way or must use raw connection locally?
        # Re-using the pattern from previous interactions?
        # Wait, I don't see a clear 'run_sql' tool usage in history other than inspecting files.
        # Inspecting history: "Created a stub Python script for inspecting database constraints..."
        # It seems I might not have direct SQL execution capability via Supabase Client unless I use `postgres` library directly or an RPC.
        
        # Let's try to use the `psql` command line if possible locally?
        # Or look for a helper.
        # Ah, in `admin_employees.py` we use `supabase.table()...`.
        
        # Workaround: Using a helper function if available or just printing instructions?
        # If user has `psql` installed and env vars set...
        
        # Let's look for `db_config.py` or similar for connection string.
        pass
        
    except FileNotFoundError:
        print("Error: SQL file not found.")

# Since I can't be sure about direct SQL execution environment,
# I'll create a Python script that uses `psycopg2` if available, or just asks user.
# ACTUALLY, I see `d:\PROJECT\dashboard-performance\backend\requirements.txt` might have `psycopg2`?
# Let's check `backend` dir.

# FOR NOW: I will assumne I should instruct the user or use a dedicated tool `run_command` with a standard connector.
# However, for Agentic mode, I should probably try to automate.

# Let's write a script that connects using the SUPABASE_CONNECTION_STRING usually found in .env
# If I can't read .env safely/reliably to get the stirng, I might struggle.

# ALTERNATIVE: Use the existing `supabase_client` and see if there is an RPC I can use, or just create the tables via python API (harder).

# BEST PATH: Validated pattern: Writing the SQL file is Step 1.
# Running it: I will try to use `psycopg2` in a python script, reading from `.env`.

import psycopg2
import os

def run_rbac_migration():
    # Load env vars manually or via dotenv
    # url = os.getenv("DATABASE_URL") # This is usually needed
    
    # Let's try to read .env line, assuming specific format
    db_url = None
    print("Reading .env file...")
    if os.path.exists('.env'):
        with open('.env') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                
                parts = line.split("=", 1)
                if len(parts) == 2:
                    key, val = parts[0].strip(), parts[1].strip()
                    if key == "DATABASE_URL":
                        db_url = val
                        # Auto-fix quotes if present
                        if db_url.startswith('"') and db_url.endswith('"'): db_url = db_url[1:-1]
                        if db_url.startswith("'") and db_url.endswith("'"): db_url = db_url[1:-1]
                        print("Found DATABASE_URL")
                        break
    else:
        print(".env file NOT FOUND at " + os.getcwd())
    
    if not db_url:
        print("❌ DATABASE_URL not found in .env")
        return

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        with open('migration_rbac_init.sql', 'r') as f:
            sql = f.read()
            
        cur.execute(sql)
        conn.commit()
        print("✅ RBAC Migration Applied Successfully!")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Migration Failed: {e}")

if __name__ == "__main__":
    run_rbac_migration()
