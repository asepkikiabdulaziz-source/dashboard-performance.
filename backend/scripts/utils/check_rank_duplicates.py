
import os
import sys
from google.oauth2 import service_account
from google.cloud import bigquery
import json

def check_duplicates():
    credentials_path = 'd:\\PROJECT\\dashboard-performance\\backend\\bigquery-credentials.json'
    if not os.path.exists(credentials_path):
        print("Credentials not found")
        return

    client = bigquery.Client.from_service_account_json(credentials_path)
    
    tables = {
        'rank_ass': 'rank_ASS',
        'rank_bm': 'rank_zona',
        'rank_rbm': 'rank_zona'
    }
    
    project = "nabati-cuan"
    dataset = "amo_jan_2026"
    
    for table, rank_col in tables.items():
        print(f"\n📊 Checking {table} (column: {rank_col}) for duplicates...")
        query = f"""
            SELECT {rank_col}, COUNT(*) as count
            FROM `{project}.{dataset}.{table}`
            GROUP BY {rank_col}
            HAVING count > 1
            ORDER BY count DESC
            LIMIT 5
        """
        try:
            results = client.query(query).to_dataframe()
            if results.empty:
                print(f"✅ No duplicates found in {rank_col}. It seems to be a unique/national rank.")
            else:
                print(f"❌ Found duplicates in {rank_col}:")
                print(results)
        except Exception as e:
            print(f"⚠️ Error checking {table}: {e}")

if __name__ == "__main__":
    check_duplicates()
