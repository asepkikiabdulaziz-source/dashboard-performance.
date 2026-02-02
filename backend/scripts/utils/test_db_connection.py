"""
Test database connection and show connection info
Helps diagnose connection issues before running migrations
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

load_dotenv()

def get_database_url():
    """Get database URL from various possible sources"""
    # Try different environment variable names
    db_url = (
        os.getenv("DATABASE_URL") or
        os.getenv("SUPABASE_DB_URL") or
        os.getenv("POSTGRES_URL") or
        os.getenv("POSTGRES_CONNECTION_STRING")
    )
    
    # If no URL found, try to use known working connection string from other scripts
    # This is a fallback - user should set DATABASE_URL in .env
    if not db_url:
        # Check if we have the pattern from working scripts
        # This is just for testing - production should use .env
        known_host = "aws-1-ap-south-1.pooler.supabase.com"
        known_user = "postgres.mcbrliwcekwhujsiyklk"
        known_pass = os.getenv("SUPABASE_DB_PASSWORD") or "Ak3403090115"
        
        if known_pass:
            db_url = f"postgresql://{known_user}:{known_pass}@{known_host}:6543/postgres"
            print(f"[INFO] Using fallback connection string (from known config)")
            print(f"       Please set DATABASE_URL in .env for production use")
    
    return db_url

def build_connection_string_from_supabase():
    """Build connection string from Supabase environment variables"""
    # Supabase provides these in dashboard
    db_host = os.getenv("SUPABASE_DB_HOST")
    db_port = os.getenv("SUPABASE_DB_PORT", "6543")
    db_name = os.getenv("SUPABASE_DB_NAME", "postgres")
    db_user = os.getenv("SUPABASE_DB_USER")
    db_password = os.getenv("SUPABASE_DB_PASSWORD")
    
    if db_host and db_user and db_password:
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    return None

def normalize_connection_string(url):
    """Normalize connection string to use port 6543 (pooler) and correct hostname"""
    if not url:
        return None
    
    # Parse URL
    parsed = urlparse(url)
    
    # Ensure postgresql:// scheme
    if not parsed.scheme:
        url = f"postgresql://{url}"
        parsed = urlparse(url)
    
    # Fix hostname: if using db.project.supabase.co, try to convert to pooler format
    # Format: db.projectid.supabase.co -> aws-X-region.pooler.supabase.com
    hostname = parsed.hostname or ""
    
    # If hostname is in format db.xxx.supabase.co, we need pooler format
    # But we can't auto-detect, so we'll try to use what's provided
    # User should use pooler connection string from Supabase dashboard
    
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

def test_connection(url, show_details=True):
    """Test database connection"""
    try:
        if show_details:
            # Hide password in display
            display_url = url.split('@')[1] if '@' in url else url
            print(f"[*] Testing connection to: {display_url}")
        
        conn = psycopg2.connect(url, connect_timeout=10)
        cur = conn.cursor()
        
        # Test query
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        
        # Test schema access
        cur.execute("SELECT current_schema();")
        schema = cur.fetchone()[0]
        
        # Test hr schema exists
        cur.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name = 'hr'
        """)
        hr_exists = cur.fetchone() is not None
        
        cur.close()
        conn.close()
        
        print("[OK] Connection successful!")
        print(f"     PostgreSQL version: {version.split(',')[0]}")
        print(f"     Current schema: {schema}")
        print(f"     HR schema exists: {'Yes' if hr_exists else 'No'}")
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"[ERROR] Connection failed: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    print("=" * 60)
    print("Database Connection Test")
    print("=" * 60)
    print()
    
    # Try to get connection string
    db_url = get_database_url()
    
    # Check if using wrong format (Direct connection instead of Pooler)
    if db_url and 'db.' in db_url and '.supabase.co' in db_url:
        print("[WARN] Detected Direct connection format (db.xxx.supabase.co)")
        print("       This may not work. Trying to use Pooler format...")
        print()
        # Try to extract project ID and build pooler URL
        # For now, use known working format
        known_host = "aws-1-ap-south-1.pooler.supabase.com"
        known_user = "postgres.mcbrliwcekwhujsiyklk"
        parsed = urlparse(db_url)
        password = parsed.password or os.getenv("SUPABASE_DB_PASSWORD") or "Ak3403090115"
        
        if password:
            db_url = f"postgresql://{known_user}:{password}@{known_host}:6543/postgres"
            print(f"[INFO] Using Pooler connection format")
    
    if not db_url:
        print("[WARN] DATABASE_URL not found in environment variables")
        print()
        print("Trying to build from Supabase variables...")
        db_url = build_connection_string_from_supabase()
    
    if not db_url:
        print("[ERROR] Could not determine database connection string")
        print()
        print("Please set one of these in .env file:")
        print()
        print("Option 1: Full connection string (RECOMMENDED)")
        print("  DATABASE_URL=postgresql://postgres.xxx:password@aws-X-region.pooler.supabase.com:6543/postgres")
        print()
        print("Option 2: Supabase-specific variables")
        print("  SUPABASE_DB_HOST=aws-1-ap-south-1.pooler.supabase.com")
        print("  SUPABASE_DB_PORT=6543")
        print("  SUPABASE_DB_USER=postgres.mcbrliwcekwhujsiyklk")
        print("  SUPABASE_DB_PASSWORD=your-password")
        print("  SUPABASE_DB_NAME=postgres")
        print()
        print("IMPORTANT: Use Pooler connection string, not Direct connection!")
        print("You can find this in Supabase Dashboard:")
        print("  Settings > Database > Connection string > Pooler mode")
        print()
        print("Format should be:")
        print("  postgresql://postgres.xxx:password@aws-X-region.pooler.supabase.com:6543/postgres")
        print("  NOT: postgresql://postgres:password@db.xxx.supabase.co:5432/postgres")
        return False
    
    # Normalize connection string
    normalized_url = normalize_connection_string(db_url)
    
    print(f"[*] Connection string found")
    print(f"    Original: {db_url[:50]}..." if len(db_url) > 50 else f"    Original: {db_url}")
    print(f"    Normalized: {normalized_url[:50]}..." if len(normalized_url) > 50 else f"    Normalized: {normalized_url}")
    print()
    
    # Test connection
    success = test_connection(normalized_url)
    
    print()
    if success:
        print("=" * 60)
        print("[OK] Connection test passed! Ready for migration.")
        print("=" * 60)
        print()
        print("You can now run:")
        print("  python backend/scripts/utils/run_user_context_rpc_migration.py")
    else:
        print("=" * 60)
        print("[ERROR] Connection test failed!")
        print("=" * 60)
        print()
        print("Troubleshooting:")
        print("1. Check connection string format")
        print("2. Verify database is accessible")
        print("3. Check firewall/network settings")
        print("4. Try direct connection (port 5432) instead of pooler (6543)")
    
    return success

if __name__ == "__main__":
    main()
