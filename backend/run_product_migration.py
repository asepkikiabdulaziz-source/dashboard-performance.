
import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def apply_migration_and_seed():
    print("--- Applying Product Migration & Seeding ---")
    
    # Connection String (Stable one from previous successes)
    db_url = "postgresql://postgres.mcbrliwcekwhujsiyklk:Ak3403090115@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
    
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # 1. Run SQL Migration
        print("1. Creating Table 'master.ref_products'...")
        with open('backend/migration_products.sql', 'r') as f:
            sql = f.read()
        cur.execute(sql)
        conn.commit()
        print("[OK] Table created.")
        
        # 2. Seed from _master_item.xlsx
        print("\n2. Seeding from _master_item.xlsx...")
        file_path = "_master_item.xlsx"
        if not os.path.exists(file_path):
             print(f"[ERR] File not found: {file_path}")
             return
             
        df = pd.read_excel(file_path)
        
        # Map values
        # STATUS_PRODUK: 'Active' -> True, others -> False
        df['is_active'] = df['STATUS_PRODUK'].apply(lambda x: True if str(x).strip().lower() == 'active' else False)
        
        # Prepare records
        # Columns in Excel: ['KD_SKU', 'NAMA_SKU', 'CATEGORY', 'BRAND', 'DIVISI', 'STATUS_PRODUK']
        # Columns in DB: product_code, product_name, category, brand, division, is_active, company_id
        
        success_count = 0
        error_count = 0
        
        print(f"Processing {len(df)} rows...")
        
        # Using execute_values would be faster, but let's just do a clean loop for validation
        for _, row in df.iterrows():
            try:
                cur.execute("""
                    INSERT INTO master.ref_products (product_code, product_name, category, brand, division, is_active, company_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (product_code) DO UPDATE SET
                        product_name = EXCLUDED.product_name,
                        category = EXCLUDED.category,
                        brand = EXCLUDED.brand,
                        division = EXCLUDED.division,
                        is_active = EXCLUDED.is_active,
                        updated_at = NOW();
                """, (
                    str(row['KD_SKU']),
                    str(row['NAMA_SKU']),
                    str(row['CATEGORY']),
                    str(row['BRAND']),
                    str(row['DIVISI']),
                    row['is_active'],
                    'ID001'
                ))
                success_count += 1
            except Exception as e:
                # print(f"Error row {row['KD_SKU']}: {e}")
                error_count += 1
                conn.rollback()
        
        conn.commit()
        print(f"[OK] Seeding complete. Success: {success_count}, Errors: {error_count}")
        
        cur.close()
        conn.close()
        print("\nSUCCESS: Migration and Seeding finished.")
        
    except Exception as e:
        print(f"CRITICAL FAILED: {e}")

if __name__ == "__main__":
    apply_migration_and_seed()
