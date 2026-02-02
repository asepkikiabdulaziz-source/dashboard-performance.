# Save exploration results to file for analysis
import os
from google.cloud import bigquery
import pandas as pd

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'bigquery-credentials.json'
client = bigquery.Client()

# Get summary by region
query = """
SELECT 
    region,
    COUNT(*) as total_salesman,
    SUM(Omset_P4) as total_revenue,
    SUM(target_oms) as total_target,
    ROUND(SUM(Omset_P4) / SUM(target_oms) * 100, 2) as achievement_rate
FROM `myproject-482315.pma.FINAL_SCORECARD_RANKED`
GROUP BY region
ORDER BY region
"""

df = client.query(query).to_dataframe()

print("Region Summary from FINAL_SCORECARD_RANKED:")
print("=" * 80)
print(df.to_string(index=False))
print()
print(f"Total Regions: {len(df)}")
print()

# Save to CSV for reference
df.to_csv('region_summary.csv', index=False)
print("✅ Saved to region_summary.csv")
