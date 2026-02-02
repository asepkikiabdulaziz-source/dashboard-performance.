# Simple schema check
import os
from google.cloud import bigquery

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'bigquery-credentials.json'
client = bigquery.Client()

print("Getting table schema...")
table = client.get_table("myproject-482315.pma.FINAL_SCORECARD_RANKED")

print(f"\nTable: FINAL_SCORECARD_RANKED")
print(f"Rows: {table.num_rows:,}")
print(f"\nColumns ({len(table.schema)}):")
print("-" * 60)

for field in table.schema:
    print(f"{field.name:30} {field.field_type:15}")

# Get first row to see data
print("\n" + "="*60)
print("Sample data (first row):")
print("="*60)

query = "SELECT * FROM `myproject-482315.pma.FINAL_SCORECARD_RANKED` LIMIT 1"
df = client.query(query).to_dataframe()

for col in df.columns:
    print(f"{col}: {df[col].iloc[0]}")
