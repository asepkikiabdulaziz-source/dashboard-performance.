"""
Run migration for user context RPC function
Creates optimized RPC function: hr.get_user_context_by_email()
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

load_dotenv()

def get_database_url():
    """Get database URL from various possible sources"""
    from urllib.parse import urlparse
    
    # Try different environment variable names
    db_url = (
        os.getenv("DATABASE_URL") or
        os.getenv("SUPABASE_DB_URL") or
        os.getenv("POSTGRES_URL") or
        os.getenv("POSTGRES_CONNECTION_STRING")
    )
    
    # Check if using wrong format (Direct connection instead of Pooler)
    if db_url and 'db.' in db_url and '.supabase.co' in db_url:
        print("[WARN] Detected Direct connection format (db.xxx.supabase.co)")
        print("       Converting to Pooler format...")
        # Extract password and use known pooler format
        parsed = urlparse(db_url)
        password = parsed.password or os.getenv("SUPABASE_DB_PASSWORD") or "Ak3403090115"
        known_host = "aws-1-ap-south-1.pooler.supabase.com"
        known_user = "postgres.mcbrliwcekwhujsiyklk"
        
        if password:
            db_url = f"postgresql://{known_user}:{password}@{known_host}:6543/postgres"
            print(f"[INFO] Using Pooler connection format")
    
    # Try to build from Supabase-specific variables
    if not db_url:
        db_host = os.getenv("SUPABASE_DB_HOST")
        db_port = os.getenv("SUPABASE_DB_PORT", "6543")
        db_name = os.getenv("SUPABASE_DB_NAME", "postgres")
        db_user = os.getenv("SUPABASE_DB_USER")
        db_password = os.getenv("SUPABASE_DB_PASSWORD")
        
        if db_host and db_user and db_password:
            db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    # Fallback to known working connection string
    if not db_url:
        known_host = "aws-1-ap-south-1.pooler.supabase.com"
        known_user = "postgres.mcbrliwcekwhujsiyklk"
        known_pass = os.getenv("SUPABASE_DB_PASSWORD") or "Ak3403090115"
        
        if known_pass:
            db_url = f"postgresql://{known_user}:{known_pass}@{known_host}:6543/postgres"
            print(f"[INFO] Using fallback connection string")
    
    return db_url

def normalize_connection_string(url):
    """Normalize connection string to use port 6543 (pooler)"""
    if not url:
        return None
    
    from urllib.parse import urlparse
    
    # Parse URL
    parsed = urlparse(url)
    
    # Ensure postgresql:// scheme
    if not parsed.scheme:
        url = f"postgresql://{url}"
        parsed = urlparse(url)
    
    # Use port 6543 (pooler) if not specified or if using 5432
    if not parsed.port or parsed.port == 5432:
        # Replace port 5432 with 6543
        if ':5432' in url:
            url = url.replace(':5432', ':6543')
        elif parsed.port == 5432:
            url = url.replace(f':{parsed.port}', ':6543')
        elif not parsed.port and '@' in url:
            # Add port 6543 if not present
            url = url.replace('@', ':6543@', 1)
    
    return url

def run_migration():
    """Run the user context RPC migration"""
    try:
        db_url = get_database_url()
        
        if not db_url:
            print("[ERROR] DATABASE_URL not found!")
            print("        Please set one of these in .env:")
            print("        - DATABASE_URL")
            print("        - SUPABASE_DB_URL")
            print("        - Or SUPABASE_DB_HOST, SUPABASE_DB_USER, SUPABASE_DB_PASSWORD")
            print()
            print("        You can find connection string in Supabase Dashboard:")
            print("        Settings > Database > Connection string (Pooler mode)")
            return False
        
        normalized_url = normalize_connection_string(db_url)
        
        print(f"[*] Connecting to Database...")
        print(f"    Using: {normalized_url.split('@')[1] if '@' in normalized_url else normalized_url[:50]}")
        
        # Test connection first
        try:
            test_conn = psycopg2.connect(normalized_url, connect_timeout=5)
            test_conn.close()
            print("[OK] Connection test passed")
        except Exception as test_err:
            print(f"[ERROR] Connection test failed: {test_err}")
            print("        Please run test script first:")
            print("        python backend/scripts/utils/test_db_connection.py")
            return False
        
        # Connect
        conn = psycopg2.connect(normalized_url, connect_timeout=10)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Get migration file path (from backend/scripts/utils/)
        script_dir = Path(__file__).parent  # backend/scripts/utils/
        migration_file = script_dir.parent / "migrations" / "migration_user_context_rpc.sql"
        
        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            return False
        
        print(f"[*] Reading migration file: {migration_file.name}")
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        print("[*] Executing Migration...")
        print("    Creating RPC function: hr.get_user_context_by_email()")
        
        cur.execute(sql_script)
        
        print("[OK] Migration Completed Successfully!")
        print("     RPC function 'hr.get_user_context_by_email' is now available")
        print("     System will automatically use this optimized function")
        
        # Verify function exists
        cur.execute("""
            SELECT routine_name 
            FROM information_schema.routines 
            WHERE routine_schema = 'hr' 
            AND routine_name = 'get_user_context_by_email'
        """)
        
        if cur.fetchone():
            print("[OK] Verification: Function exists in database")
        else:
            print("[WARN] Warning: Function not found (may need to check schema)")
        
        cur.close()
        conn.close()
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"[ERROR] Database Connection Error: {e}")
        print()
        print("        Troubleshooting:")
        print("        1. Run connection test: python backend/scripts/utils/test_db_connection.py")
        print("        2. Check DATABASE_URL format in .env")
        print("        3. Verify database is accessible")
        print("        4. Check firewall/network settings")
        print("        5. Try direct connection (port 5432) instead of pooler (6543)")
        return False
    except Exception as e:
        print(f"[ERROR] Migration Failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("User Context RPC Migration")
    print("=" * 60)
    print()
    
    success = run_migration()
    
    if success:
        print()
        print("=" * 60)
        print("[OK] Migration completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Restart your FastAPI application")
        print("2. System will automatically use the optimized RPC function")
        print("3. Check logs for 'Resolved context via RPC' messages")
    else:
        print()
        print("=" * 60)
        print("[ERROR] Migration failed. Please check errors above.")
        print("=" * 60)
        print()
        print("Alternative: Run migration manually in Supabase SQL Editor:")
        print("1. Open Supabase Dashboard")
        print("2. Go to SQL Editor")
        print("3. Copy content from: backend/scripts/migrations/migration_user_context_rpc.sql")
        print("4. Paste and run")
