
import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

def list_bq_columns(table_name):
    # Set credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'bigquery-credentials.json'
    
    project_id = os.getenv('BIGQUERY_PROJECT_ID', 'myproject-482315')
    dataset = os.getenv('BIGQUERY_DATASET', 'pma')
    
    client = bigquery.Client()
    table_id = f"{project_id}.{dataset}.{table_name}"
    
    try:
        table = client.get_table(table_id)
        print(f"\n=== COLUMNS IN {table_name} ===")
        for field in table.schema:
            print(f"- {field.name} ({field.field_type})")
    except Exception as e:
        print(f"Error fetching {table_name}: {e}")

if __name__ == "__main__":
    for t in ['rank_ass', 'rank_bm', 'rank_rbm']:
        list_bq_columns(t)
