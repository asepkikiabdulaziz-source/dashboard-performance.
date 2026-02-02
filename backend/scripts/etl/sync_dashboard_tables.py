"""
ETL Script: Sync BigQuery Materialized Tables to Supabase
- FINAL_SCORECARD_RANKED → dashboard.leaderboard
- rank_ass, rank_bm, rank_rbm → dashboard.competition_ranks

Note: These tables are already materialized via stored procedure,
so we can query them directly without creating new Materialized Views.
"""
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from google.cloud import bigquery
from supabase_client import get_supabase_client
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from logger import get_logger

load_dotenv()
logger = get_logger("etl_dashboard")

class DashboardETL:
    """
    ETL untuk sync BigQuery materialized tables ke Supabase
    Tables sudah materialized via stored procedure, jadi langsung query saja
    """
    
    def __init__(self):
        # Initialize BigQuery client
        credentials_path = os.path.join(backend_dir, 'bigquery-credentials.json')
        if os.path.exists(credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        else:
            logger.info("Using ADC for BigQuery")
        
        self.bq_client = bigquery.Client()
        self.project_id = os.getenv('BIGQUERY_PROJECT_ID', 'myproject-482315')
        self.dataset = os.getenv('BIGQUERY_DATASET', 'pma')
        
        # Initialize Supabase client
        self.supabase = get_supabase_client()
        
        logger.info(f"ETL initialized - Project: {self.project_id}, Dataset: {self.dataset}")
    
    def sync_all(self, force_refresh: bool = True):
        """
        Sync semua dashboard tables dari BigQuery ke Supabase
        
        Args:
            force_refresh: Jika True, truncate Supabase tables sebelum sync
        
        Returns:
            Status dan timing untuk setiap step
        """
        logger.info("Starting dashboard ETL sync...")
        start_time = datetime.now()
        
        results = {
            "status": "success",
            "steps": {},
            "total_elapsed_seconds": 0
        }
        
        try:
            # Step 1: Sync Leaderboard
            logger.info("Step 1: Syncing leaderboard...")
            step1_start = datetime.now()
            self.sync_leaderboard(force_refresh)
            step1_elapsed = (datetime.now() - step1_start).total_seconds()
            results["steps"]["leaderboard"] = {
                "status": "success",
                "elapsed_seconds": step1_elapsed
            }
            logger.info(f"Leaderboard sync completed in {step1_elapsed:.2f}s")
            
            # Step 2: Sync Competition Ranks
            logger.info("Step 2: Syncing competition ranks...")
            step2_start = datetime.now()
            self.sync_competition_ranks(force_refresh)
            step2_elapsed = (datetime.now() - step2_start).total_seconds()
            results["steps"]["competition_ranks"] = {
                "status": "success",
                "elapsed_seconds": step2_elapsed
            }
            logger.info(f"Competition ranks sync completed in {step2_elapsed:.2f}s")
            
            # Step 3: Update Metadata
            logger.info("Step 3: Updating metadata...")
            self.update_sync_metadata()
            
            # Total elapsed
            total_elapsed = (datetime.now() - start_time).total_seconds()
            results["total_elapsed_seconds"] = total_elapsed
            results["timestamp"] = datetime.now().isoformat()
            
            logger.info(f"ETL sync completed in {total_elapsed:.2f}s")
            return results
            
        except Exception as e:
            logger.error(f"ETL sync failed: {e}", exc_info=True)
            results["status"] = "error"
            results["error"] = str(e)
            raise
    
    def sync_leaderboard(self, force_refresh: bool):
        """
        Sync FINAL_SCORECARD_RANKED ke dashboard.leaderboard
        Table sudah materialized, langsung query saja
        """
        logger.info("  Syncing FINAL_SCORECARD_RANKED to dashboard.leaderboard...")
        
        # Query dari BigQuery (table sudah materialized)
        query = f"""
        SELECT 
            region,
            kd_dist,
            area,
            kd_sls as salesman_code,
            nm_sls as salesman_name,
            div_sls as division,
            nik,
            Omset_P1 as omset_p1,
            Omset_P2 as omset_p2,
            Omset_P3 as omset_p3,
            Omset_P4 as omset_p4,
            target_oms as target,
            ROUND(Omset_P4 / NULLIF(target_oms, 0) * 100, 2) as achievement_rate,
            Total_Score_Final as total_score,
            Raw_Month_Score as month_score,
            Ranking_Regional as rank_regional,
            ROA_P1 as roa_p1,
            ROA_P2 as roa_p2,
            ROA_P3 as roa_p3,
            ROA_P4 as roa_p4,
            Total_CB as total_customer,
            EC_Akumulasi as effective_calls,
            saldo_point as points_balance
        FROM `{self.project_id}.{self.dataset}.FINAL_SCORECARD_RANKED`
        """
        
        df = self.bq_client.query(query).to_dataframe()
        logger.info(f"  Fetched {len(df)} records from BigQuery")
        
        # Convert to dict untuk Supabase
        records = df.to_dict('records')
        
        # Truncate jika force_refresh
        if force_refresh:
            try:
                self.supabase.table('dashboard.leaderboard')\
                    .delete()\
                    .neq('id', '0')\
                    .execute()
                logger.info("  Truncated existing data")
            except Exception as e:
                logger.warning(f"  Could not truncate (table might not exist): {e}")
        
        # Batch upsert
        batch_size = 1000
        total_batches = (len(records) + batch_size - 1) // batch_size
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            batch_num = i // batch_size + 1
            
            try:
                self.supabase.table('dashboard.leaderboard')\
                    .upsert(batch)\
                    .execute()
                logger.info(f"  Upserted batch {batch_num}/{total_batches} ({len(batch)} records)")
            except Exception as e:
                logger.error(f"  Failed to upsert batch {batch_num}: {e}")
                raise
        
        logger.info(f"  Synced {len(records)} leaderboard records to Supabase")
    
    def sync_competition_ranks(self, force_refresh: bool):
        """
        Sync rank_ass, rank_bm, rank_rbm ke dashboard.competition_ranks
        Tables sudah materialized, langsung query saja
        """
        logger.info("  Syncing competition ranks (rank_ass, rank_bm, rank_rbm)...")
        
        from competition_config import COMPETITIONS
        
        all_records = []
        
        for comp_id, comp_config in COMPETITIONS.items():
            table_map = comp_config.get("tables", {})
            
            for level in ['ass', 'bm', 'rbm']:
                if level not in table_map:
                    continue
                
                table_name = table_map[level]
                logger.info(f"    Syncing {comp_id} - {level} from {table_name}...")
                
                # Query dari BigQuery (table sudah materialized)
                query = f"""
                SELECT 
                    '{comp_id}' as competition_id,
                    '{level}' as level,
                    REGION as region,
                    NIK_ASS as nik,
                    NAMA_ASS as name,
                    rank_ASS as rank,
                    OMSET as omset,
                    TARGET as target,
                    total_Point as total_point,
                    point_oms as point_oms,
                    point_ROA as point_roa,
                    ach_oms as ach_oms,
                    ach_ROA as ach_roa,
                    CABANG as cabang,
                    ZONA_BM as zona_bm,
                    ZONA_RBM as zona_rbm,
                    REWARD as reward,
                    CB as cb,
                    act_roa as act_roa
                FROM `{self.project_id}.{self.dataset}.{table_name}`
                """
                
                try:
                    df = self.bq_client.query(query).to_dataframe()
                    records = df.to_dict('records')
                    all_records.extend(records)
                    logger.info(f"      Fetched {len(records)} records from {table_name}")
                except Exception as e:
                    logger.warning(f"      Failed to fetch from {table_name}: {e}")
                    continue
        
        if not all_records:
            logger.warning("  No competition rank records to sync")
            return
        
        logger.info(f"  Total competition rank records: {len(all_records)}")
        
        # Truncate jika force_refresh
        if force_refresh:
            try:
                self.supabase.table('dashboard.competition_ranks')\
                    .delete()\
                    .neq('id', '0')\
                    .execute()
                logger.info("  Truncated existing competition ranks")
            except Exception as e:
                logger.warning(f"  Could not truncate (table might not exist): {e}")
        
        # Batch upsert
        batch_size = 1000
        total_batches = (len(all_records) + batch_size - 1) // batch_size
        
        for i in range(0, len(all_records), batch_size):
            batch = all_records[i:i+batch_size]
            batch_num = i // batch_size + 1
            
            try:
                self.supabase.table('dashboard.competition_ranks')\
                    .upsert(batch)\
                    .execute()
                logger.info(f"  Upserted batch {batch_num}/{total_batches} ({len(batch)} records)")
            except Exception as e:
                logger.error(f"  Failed to upsert batch {batch_num}: {e}")
                raise
        
        logger.info(f"  Synced {len(all_records)} competition rank records to Supabase")
    
    def update_sync_metadata(self):
        """Update metadata table dengan last sync timestamp"""
        try:
            metadata = {
                "key": "last_sync",
                "last_sync_at": datetime.now().isoformat(),
                "sync_status": "success"
            }
            
            self.supabase.table('dashboard.metadata')\
                .upsert(metadata, on_conflict='key')\
                .execute()
            logger.info("  Updated sync metadata")
        except Exception as e:
            logger.warning(f"  Failed to update metadata: {e}")


# Main function untuk dipanggil dari API
def trigger_dashboard_sync(force_refresh: bool = True):
    """
    Main entry point untuk manual trigger dashboard sync
    
    Args:
        force_refresh: Jika True, truncate Supabase tables sebelum sync
    
    Returns:
        Status dan timing results
    """
    etl = DashboardETL()
    return etl.sync_all(force_refresh=force_refresh)


if __name__ == "__main__":
    # For testing
    result = trigger_dashboard_sync(force_refresh=True)
    print(f"\nSync completed: {result}")
