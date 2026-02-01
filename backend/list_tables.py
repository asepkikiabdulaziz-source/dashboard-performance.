# List all tables in BigQuery dataset
import os
from google.cloud import bigquery

# Set credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'bigquery-credentials.json'

# Initialize client
client = bigquery.Client()

print("=" * 80)
print("📋 LISTING ALL TABLES IN BIGQUERY")
print("=" * 80)
print()

# List all tables in the dataset
dataset_id = "myproject-482315.pma"

print(f"Dataset: {dataset_id}")
print("-" * 80)

tables = client.list_tables(dataset_id)
table_list = []

for table in tables:
    table_full = client.get_table(f"{dataset_id}.{table.table_id}")
    table_list.append({
        'table_name': table.table_id,
        'rows': table_full.num_rows,
        'size_mb': round(table_full.num_bytes / (1024**2), 2)
    })

print(f"\n{'Table Name':<40} {'Rows':<15} {'Size (MB)':<15}")
print("-" * 80)

for t in sorted(table_list, key=lambda x: x['table_name']):
    print(f"{t['table_name']:<40} {t['rows']:<15,} {t['size_mb']:<15,.2f}")

print()
print(f"Total tables found: {len(table_list)}")
print("=" * 80)
