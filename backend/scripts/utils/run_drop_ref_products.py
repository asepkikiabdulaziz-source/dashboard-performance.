
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def drop_ref_products():
    print("--- Dropping master.ref_products ---")
    db_url = "postgresql://postgres.mcbrliwcekwhujsiyklk:Ak3403090115@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
    
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        with open('backend/migration_drop_ref_products.sql', 'r') as f:
            sql = f.read()
        
        print("Executing DROP TABLE...")
        cur.execute(sql)
        conn.commit()
        
        cur.close()
        conn.close()
        print("SUCCESS: ref_products table dropped.")
        
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    drop_ref_products()
