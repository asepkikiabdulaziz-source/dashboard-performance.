
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def apply():
    print("--- Applying Consistency Migration ---")
    # db_url = os.environ.get("DATABASE_URL")
    # URL in env is malformed, attempting to reconstruct valid string
    # Pattern: postgresql://[user]:[password]@[netloc]:[port]/[dbname]
    
    # Extracted Config:
    # User: postgres.mcbrliwcekwhujsiyklk (Standard Supabase Pooler User)
    # Pass: Ak3403090115
    # Host: aws-0-ap-south-1.pooler.supabase.com (Standard Pooler)
    # Port: 6543
    
    # Try Standard Pooler URL First
    # db_url = "postgresql://postgres.mcbrliwcekwhujsiyklk:Ak3403090115@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
    
    # Fallback to the weird user 'postgres403090115' found in string
    db_url = "postgresql://postgres.mcbrliwcekwhujsiyklk:Ak3403090115@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
    # Note: user might be 'postgres.mcbrliwcekwhujsiyklk', but let's try 'aws-1' host first.
    # Ref: env had 'postgres403090115', maybe that IS the user?
    # Let's try combining: User=postgres.mcbrliwcek... Host=aws-1...
    # If that fails, I'll try User=postgres403090115
    
    # Attempt 2: Valid User + aws-1 Host
    db_url = "postgresql://postgres.mcbrliwcekwhujsiyklk:Ak3403090115@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
    
    print(f"Using Connection String: {db_url.split('@')[1]}") # Hide password

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        with open('migration_drop_role_level.sql', 'r') as f:
            sql = f.read()
            
        print("Executing SQL block...")
        cur.execute(sql)
        conn.commit()
        
        cur.close()
        conn.close()
        print("SUCCESS: Migration applied.")
        
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    apply()
