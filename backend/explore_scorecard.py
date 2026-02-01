# Explore FINAL_SCORECARD_RANKED Table Structure
# This script helps us understand the table schema and sample data

import os
from google.cloud import bigquery
import pandas as pd

# Set credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'bigquery-credentials.json'

# Initialize client
client = bigquery.Client()

print("=" * 80)
print("🔍 EXPLORING FINAL_SCORECARD_RANKED TABLE")
print("=" * 80)
print()

# 1. Get table schema
print("📋 Table Schema:")
print("-" * 80)
table_ref = "myproject-482315.pma.FINAL_SCORECARD_RANKED"
table = client.get_table(table_ref)

print(f"Total Rows: {table.num_rows:,}")
print(f"Total Columns: {len(table.schema)}")
print()

for field in table.schema:
    print(f"  • {field.name:30} {field.field_type:15} {field.mode}")
print()

# 2. Get sample data
print("📊 Sample Data (5 rows):")
print("-" * 80)
query = """
SELECT *
FROM `myproject-482315.pma.FINAL_SCORECARD_RANKED`
LIMIT 5
"""

df = client.query(query).to_dataframe()
print(df.to_string())
print()

# 3. Check available regions/PMA
print("🌍 Available Regions (PMA):")
print("-" * 80)
query_regions = """
SELECT DISTINCT pma
FROM `myproject-482315.pma.FINAL_SCORECARD_RANKED`
ORDER BY pma
"""

regions = client.query(query_regions).to_dataframe()
print(regions.to_string(index=False))
print()

# 4. Check date range
print("📅 Date Range:")
print("-" * 80)
query_dates = """
SELECT 
    MIN(tgl) as earliest_date,
    MAX(tgl) as latest_date,
    COUNT(DISTINCT tgl) as total_days
FROM `myproject-482315.pma.FINAL_SCORECARD_RANKED`
"""

dates = client.query(query_dates).to_dataframe()
print(dates.to_string(index=False))
print()

# 5. Check data summary by region
print("💰 Summary by Region:")
print("-" * 80)
query_summary = """
SELECT 
    pma as region,
    COUNT(*) as total_records,
    SUM(value) as total_value,
    AVG(value) as avg_value
FROM `myproject-482315.pma.FINAL_SCORECARD_RANKED`
GROUP BY pma
ORDER BY total_value DESC
"""

summary = client.query(query_summary).to_dataframe()
summary['total_value'] = summary['total_value'].apply(lambda x: f"Rp {x:,.0f}")
summary['avg_value'] = summary['avg_value'].apply(lambda x: f"Rp {x:,.0f}")
print(summary.to_string(index=False))
print()

print("=" * 80)
print("✅ Exploration Complete!")
print("=" * 80)
