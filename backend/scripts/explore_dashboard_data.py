"""
Comprehensive Exploration Script for Dashboard Real Implementation
STEP 0: Exploration & Verification
"""
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from google.cloud import bigquery
from supabase_client import get_supabase_client
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("STEP 0: EXPLORATION & VERIFICATION")
print("=" * 80)
print()

# ============================================================================
# PART 1: BIGQUERY EXPLORATION
# ============================================================================
print("PART 1: BIGQUERY DATA EXPLORATION")
print("=" * 80)
print()

try:
    # Initialize BigQuery client
    credentials_path = os.path.join(os.path.dirname(__file__), '..', 'bigquery-credentials.json')
    if os.path.exists(credentials_path):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        print(f"[OK] Using credentials: {credentials_path}")
    else:
        print("[WARN] Credentials file not found, using ADC (Application Default Credentials)")
    
    bq_client = bigquery.Client()
    project_id = "myproject-482315"
    dataset_id = "pma"
    
    print(f"Project: {project_id}")
    print(f"Dataset: {dataset_id}")
    print()
    
    # 1.1 Check FINAL_SCORECARD_RANKED
    print("1. FINAL_SCORECARD_RANKED Table")
    print("-" * 80)
    try:
        table_ref = f"{project_id}.{dataset_id}.FINAL_SCORECARD_RANKED"
        table = bq_client.get_table(table_ref)
        
        print(f"   [OK] Table exists")
        print(f"   Total Rows: {table.num_rows:,}")
        print(f"   Total Columns: {len(table.schema)}")
        print()
        
        # Key columns for dashboard
        key_columns = ['region', 'nik', 'kd_sls', 'nm_sls', 'Omset_P4', 'target_oms', 
                      'Total_Score_Final', 'Ranking_Regional']
        print("   Key Columns for Dashboard:")
        for field in table.schema:
            if field.name in key_columns or any(kw in field.name.lower() for kw in ['omset', 'target', 'score', 'rank', 'nik', 'region']):
                print(f"      • {field.name:30} {field.field_type:15} {field.mode or 'NULLABLE'}")
        print()
        
        # Sample data
        query = f"""
        SELECT 
            region,
            nik,
            kd_sls,
            nm_sls,
            Omset_P4,
            target_oms,
            Total_Score_Final,
            Ranking_Regional
        FROM `{table_ref}`
        LIMIT 3
        """
        df_sample = bq_client.query(query).to_dataframe()
        print("   Sample Data:")
        print(df_sample.to_string(index=False))
        print()
        
        # Region summary
        query_regions = f"""
        SELECT 
            region,
            COUNT(*) as salesman_count,
            SUM(Omset_P4) as total_revenue,
            AVG(Total_Score_Final) as avg_score
        FROM `{table_ref}`
        GROUP BY region
        ORDER BY region
        LIMIT 10
        """
        df_regions = bq_client.query(query_regions).to_dataframe()
        print("   Region Summary:")
        print(df_regions.to_string(index=False))
        print()
        
    except Exception as e:
        print(f"   [ERROR] {e}")
        print()
    
    # 1.2 Check all_prc (raw transactions)
    print("2. all_prc Table (Raw Transactions)")
    print("-" * 80)
    try:
        table_ref = f"{project_id}.{dataset_id}.all_prc"
        table = bq_client.get_table(table_ref)
        
        print(f"   [OK] Table exists")
        print(f"   Total Rows: {table.num_rows:,}")
        print(f"   Total Columns: {len(table.schema)}")
        print()
        
        # Key columns
        key_columns = ['tgl', 'pma', 'kd_brg', 'kode_salesman', 'kode_outlet', 'qty', 'value']
        print("   Key Columns for Dashboard:")
        for field in table.schema:
            if field.name in key_columns or any(kw in field.name.lower() for kw in ['tgl', 'date', 'pma', 'region', 'salesman', 'outlet', 'qty', 'value']):
                print(f"      • {field.name:30} {field.field_type:15} {field.mode or 'NULLABLE'}")
        print()
        
        # Date range
        query_dates = f"""
        SELECT 
            MIN(tgl) as earliest_date,
            MAX(tgl) as latest_date,
            COUNT(DISTINCT tgl) as total_days,
            COUNT(DISTINCT pma) as total_regions,
            COUNT(DISTINCT kode_salesman) as total_salesman
        FROM `{table_ref}`
        """
        df_dates = bq_client.query(query_dates).to_dataframe()
        print("   Data Range & Summary:")
        print(df_dates.to_string(index=False))
        print()
        
        # Sample data
        query = f"""
        SELECT 
            tgl,
            pma,
            kd_brg,
            kode_salesman,
            qty,
            value
        FROM `{table_ref}`
        ORDER BY tgl DESC
        LIMIT 3
        """
        df_sample = bq_client.query(query).to_dataframe()
        print("   Sample Data:")
        print(df_sample.to_string(index=False))
        print()
        
    except Exception as e:
        print(f"   [ERROR] {e}")
        print()
    
    # 1.3 Check for other relevant tables
    print("3. Other Tables in Dataset")
    print("-" * 80)
    try:
        dataset_ref = bq_client.dataset(dataset_id, project=project_id)
        tables = list(bq_client.list_tables(dataset_ref))
        
        print(f"   Total Tables: {len(tables)}")
        print("   Table List:")
        for table in tables[:10]:  # Show first 10
            print(f"      • {table.table_id}")
        if len(tables) > 10:
            print(f"      ... and {len(tables) - 10} more")
        print()
        
    except Exception as e:
        print(f"   [WARN] Could not list tables: {e}")
        print()

except Exception as e:
    print(f"[ERROR] BigQuery exploration failed: {e}")
    print()

# ============================================================================
# PART 2: SUPABASE EXPLORATION
# ============================================================================
print()
print("=" * 80)
print("PART 2: SUPABASE MASTER DATA EXPLORATION")
print("=" * 80)
print()

try:
    supabase = get_supabase_client()
    print("[OK] Supabase connection successful")
    print()
    
    # 2.1 Check master.products
    print("1. master.products")
    print("-" * 80)
    try:
        response = supabase.schema('master').table('products').select('*').limit(5).execute()
        if response.data:
            print(f"   [OK] Table exists")
            print(f"   Sample records: {len(response.data)}")
            print(f"   Key Columns:")
            if response.data:
                for key in list(response.data[0].keys())[:10]:
                    print(f"      • {key}")
            print()
        else:
            print("   [WARN] Table exists but no data")
            print()
    except Exception as e:
        print(f"   [ERROR] {e}")
        print()
    
    # 2.2 Check hr.employees
    print("2. hr.employees")
    print("-" * 80)
    try:
        response = supabase.schema('hr').table('employees').select('nik,full_name,email,role_id').limit(5).execute()
        if response.data:
            print(f"   [OK] Table exists")
            print(f"   Sample records: {len(response.data)}")
            print(f"   Key Columns: nik, full_name, email, role_id")
            print("   Sample Data:")
            for emp in response.data[:3]:
                print(f"      • {emp.get('nik')}: {emp.get('full_name')} ({emp.get('email')})")
            print()
        else:
            print("   [WARN] Table exists but no data")
            print()
    except Exception as e:
        print(f"   [ERROR] {e}")
        print()
    
    # 2.3 Check master.ref_regions
    print("3. master.ref_regions")
    print("-" * 80)
    try:
        response = supabase.schema('master').table('ref_regions').select('*').limit(5).execute()
        if response.data:
            print(f"   [OK] Table exists")
            print(f"   Sample records: {len(response.data)}")
            print(f"   Key Columns:")
            if response.data:
                for key in list(response.data[0].keys())[:10]:
                    print(f"      • {key}")
            print()
        else:
            print("   [WARN] Table exists but no data")
            print()
    except Exception as e:
        print(f"   [ERROR] {e}")
        print()
    
    # 2.4 Check master.ref_distributors
    print("4. master.ref_distributors")
    print("-" * 80)
    try:
        response = supabase.schema('master').table('ref_distributors').select('kd_dist,name,branch_id').limit(5).execute()
        if response.data:
            print(f"   [OK] Table exists")
            print(f"   Sample records: {len(response.data)}")
            print()
        else:
            print("   [WARN] Table exists but no data")
            print()
    except Exception as e:
        print(f"   [ERROR] {e}")
        print()

except Exception as e:
    print(f"[ERROR] Supabase exploration failed: {e}")
    print()

# ============================================================================
# PART 3: JOIN ANALYSIS
# ============================================================================
print()
print("=" * 80)
print("PART 3: JOIN ANALYSIS (BigQuery <-> Supabase)")
print("=" * 80)
print()

print("Potential JOINs for Dashboard:")
print()
print("1. all_prc (BQ) -> master.products (Supabase)")
print("   JOIN Key: all_prc.kd_brg = master.products.product_code")
print("   Purpose: Get product names, categories, brands")
print()

print("2. all_prc (BQ) -> hr.employees (Supabase)")
print("   JOIN Key: all_prc.kode_salesman = hr.employees.nik")
print("   Purpose: Get salesman names, roles")
print()

print("3. all_prc (BQ) -> master.ref_regions (Supabase)")
print("   JOIN Key: all_prc.pma = master.ref_regions.region_code")
print("   Purpose: Get region names")
print()

print("4. FINAL_SCORECARD_RANKED (BQ) -> hr.employees (Supabase)")
print("   JOIN Key: FINAL_SCORECARD_RANKED.nik = hr.employees.nik")
print("   Purpose: Enrich leaderboard with employee details")
print()

# ============================================================================
# SUMMARY & RECOMMENDATIONS
# ============================================================================
print()
print("=" * 80)
print("EXPLORATION COMPLETE")
print("=" * 80)
print()
print("Next Steps:")
print("   1. Review findings above")
print("   2. Verify data availability")
print("   3. Proceed to STEP 1: Simple Test Query")
print()
