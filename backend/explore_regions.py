# Explore Region and Area structure
import os
from google.cloud import bigquery
import pandas as pd

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'bigquery-credentials.json'
client = bigquery.Client()

print("=" * 80)
print("🌍 EXPLORING REGION AND AREA STRUCTURE")
print("=" * 80)
print()

# 1. Get unique regions
print("📍 Unique Regions:")
print("-" * 80)
query_regions = """
SELECT 
    region,
    COUNT(*) as salesman_count,
    COUNT(DISTINCT area) as area_count,
    SUM(Omset_P4) as total_omset,
    AVG(Total_Score_Final) as avg_score
FROM `myproject-482315.pma.FINAL_SCORECARD_RANKED`
GROUP BY region
ORDER BY region
"""

df_regions = client.query(query_regions).to_dataframe()
print(df_regions.to_string(index=False))
print()

# 2. Sample data per region
print("📊 Sample Records by Region (first 2 per region):")
print("-" * 80)
query_sample = """
SELECT 
    region,
    area,
    nm_sls as salesman_name,
    Omset_P1,
    Omset_P2,
    Omset_P3,
    Omset_P4,
    Total_Score_Final,
    Ranking_Regional
FROM `myproject-482315.pma.FINAL_SCORECARD_RANKED`
ORDER BY region, Ranking_Regional
LIMIT 10
"""

df_sample = client.query(query_sample).to_dataframe()
print(df_sample.to_string(index=False))
print()

# 3. Check if we can aggregate by region for dashboard
print("💰 Aggregated Data by Region (Dashboard KPIs):")
print("-" * 80)
query_agg = """
SELECT 
    region,
    COUNT(*) as total_salesman,
    SUM(Omset_P4) as total_revenue,
    SUM(target_oms) as total_target,
    ROUND(SUM(Omset_P4) / SUM(target_oms) * 100, 2) as achievement_rate,
    AVG(Total_Score_Final) as avg_score
FROM `myproject-482315.pma.FINAL_SCORECARD_RANKED`
GROUP BY region
ORDER BY total_revenue DESC
"""

df_agg = client.query(query_agg).to_dataframe()
print(df_agg.to_string(index=False))
print()

# 4. Check column types for dashboard requirements
print("📋 Columns Available for Dashboard Mapping:")
print("-" * 80)
print("Revenue Metrics:")
print("  - Omset_P1, Omset_P2, Omset_P3, Omset_P4 (Period 1-4)")
print("  - target_oms (Target Omset)")
print()
print("Performance Metrics:")
print("  - ROA_P1, ROA_P2, ROA_P3, ROA_P4 (Reach of Availability)")
print("  - Total_CB (Customer Base)")
print("  - EC_Akumulasi (Effective Call)")
print()
print("Scoring & Ranking:")
print("  - Total_Score_Final")
print("  - Ranking_Regional")
print("  - Various pts_* (Point columns)")
print()
print("Identifiers:")
print("  - region, area")
print("  - kd_sls (Salesman Code), nm_sls (Salesman Name)")
print()

print("=" * 80)
print("✅ Exploration Complete!")
print("=" * 80)
