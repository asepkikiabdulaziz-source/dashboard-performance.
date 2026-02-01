import os
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_URL = os.getenv('DATABASE_URL')
MIGRATION_FILE = 'migration_rpc_get_slots.sql'

def get_connection_string_6543(url):
    if not url: return None
    # Ensure port 6543 for Transaction Pooler (or Direct if needed, but 6543 matches previous pattern)
    if ':5432' in url:
        return url.replace(':5432', ':6543')
    return url # Assume correct if not 5432

def run_migration():
    try:
        db_url_6543 = get_connection_string_6543(DB_URL)
        if not db_url_6543:
            print("❌ DATABASE_URL missing!")
            return

        print(f"🔄 Connecting to Database...")
        
        # Connect
        conn = psycopg2.connect(db_url_6543)
        conn.autocommit = True
        cur = conn.cursor()
        
        print(f"📖 Reading migration file: {MIGRATION_FILE}")
        with open(MIGRATION_FILE, 'r') as f:
            sql_script = f.read()
            
        print("🚀 Executing Migration...")
        cur.execute(sql_script)
        
        print("✅ RPC Function Created Successfully!")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration Failed: {e}")

if __name__ == "__main__":
    run_migration()
