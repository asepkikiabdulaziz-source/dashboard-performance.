
import pandas as pd
from supabase_client import supabase_request
import os

def analyze_excel():
    print("--- Analyzing _master_item.xlsx ---")
    file_path = "d:/PROJECT/dashboard-performance/_master_item.xlsx"
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    try:
        df = pd.read_excel(file_path)
        print(f"Columns: {df.columns.tolist()}")
        print("\nFirst 5 rows:")
        print(df.head())
        print(f"\nTotal rows: {len(df)}")
    except Exception as e:
        print(f"Error reading Excel: {e}")

def probe_supabase():
    print("\n--- Probing Supabase for Product/Item tables ---")
    schemas = ['master', 'public', 'hr']
    possible_names = ['ref_products', 'ref_items', 'products', 'items', 'ref_item']
    
    found = []
    for schema in schemas:
        for name in possible_names:
            try:
                res = supabase_request('GET', name, params={'limit': 1}, headers_extra={'Accept-Profile': schema})
                print(f"[FOUND] {schema}.{name}")
                found.append(f"{schema}.{name}")
            except Exception as e:
                # Silence 404s
                pass
    
    if not found:
        print("No product-related tables found in standard names.")

if __name__ == "__main__":
    analyze_excel()
    probe_supabase()
