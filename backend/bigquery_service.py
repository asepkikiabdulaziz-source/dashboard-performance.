"""
BigQuery Service Layer for Dashboard Performance
Handles all BigQuery operations with Row-Level Security
"""
import os
from google.cloud import bigquery
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime
from logger import get_logger

logger = get_logger(__name__)


class BigQueryService:
    """Service for BigQuery operations with RLS support"""
    
    def __init__(self):
        """Initialize BigQuery client"""
        # Set credentials from environment or default location
        credentials_path = os.getenv(
            'GOOGLE_APPLICATION_CREDENTIALS',
            'bigquery-credentials.json'
        )
        
        # Only set override if file exists locally
        if credentials_path and os.path.exists(credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            logger.info(f"Using credentials from {credentials_path}")
        else:
            # IMPORTANT: If file doesn't exist, we must UNSET the env var
            # otherwise the BQ client will try to find a missing file and CRASH
            if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
                logger.info(f"Credentials file '{credentials_path}' not found. Unsetting GOOGLE_APPLICATION_CREDENTIALS to use ADC (Cloud Run Identity).")
                del os.environ['GOOGLE_APPLICATION_CREDENTIALS']
            else:
                logger.info("Credentials file not found, using environment default identity (ADC)")
        
        # Initialize client with error handling
        try:
            self.client = bigquery.Client()
            logger.info("BigQuery Client successfully initialized")
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery Client: {e}")
            self.client = None
        
        # Configuration - NO HARDCODED DEFAULTS
        # All values must be set via environment variables
        self.project_id = os.getenv('BIGQUERY_PROJECT_ID', '').strip()
        self.dataset = os.getenv('BIGQUERY_DATASET', '').strip()
        self.table = os.getenv('BIGQUERY_TABLE', '').strip()
        
        # Validate all required values are set - NO DEFAULTS ALLOWED
        if not self.project_id:
            logger.error("BIGQUERY_PROJECT_ID is not set")
            raise ValueError("BIGQUERY_PROJECT_ID environment variable is required. Please set it in your deployment configuration.")
        if not self.dataset:
            logger.error("BIGQUERY_DATASET is not set")
            raise ValueError("BIGQUERY_DATASET environment variable is required. Please set it in your deployment configuration.")
        if not self.table:
            logger.error("BIGQUERY_TABLE is not set")
            raise ValueError("BIGQUERY_TABLE environment variable is required. Please set it in your deployment configuration.")
        
        self.full_table_id = f"`{self.project_id}.{self.dataset}.{self.table}`"
        logger.info(f"BigQuery configured: {self.full_table_id}")
    
    def _apply_region_filter(self, region: str) -> str:
        """
        Apply Row-Level Security filter based on region
        
        Args:
            region: User's region code (e.g., 'R06 JABODEBEK') or 'ALL' for admin
            
        Returns:
            SQL WHERE clause for region filtering
        """
        if region == "ALL":
            return ""  # Admin sees all regions
        else:
            return f"WHERE region = '{region}'"
    
    def get_leaderboard(
        self, 
        region: str, 
        limit: Optional[int] = None,
        division: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get salesman leaderboard with ranking
        
        Args:
            region: User's region code or 'ALL'
            limit: Maximum number of results (None = all)
            division: Filter by division (div_sls), optional
            
        Returns:
            DataFrame with salesman ranking and performance metrics
        """
        # Build WHERE clause
        where_clauses = []
        
        region_filter = self._apply_region_filter(region)
        if region_filter:
            where_clauses.append(region_filter.replace("WHERE ", ""))
        
        if division:
            where_clauses.append(f"div_sls = '{division}'")
        
        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Build LIMIT clause
        limit_clause = f"LIMIT {limit}" if limit else ""
        
        # Query
        query = f"""
        SELECT 
            region,
            kd_dist,
            area,
            kd_sls as salesman_code,
            nm_sls as salesman_name,
            div_sls as division,
            nik,
            
            -- Revenue Metrics
            Omset_P1 as omset_p1,
            Omset_P2 as omset_p2,
            Omset_P3 as omset_p3,
            Omset_P4 as omset_p4,
            target_oms as target,
            ROUND(Omset_P4 / NULLIF(target_oms, 0) * 100, 2) as achievement_rate,
            
            -- Omset Points (actual points earned)
            pts_Omset_P1 as pts_omset_p1,
            pts_Omset_P2 as pts_omset_p2,
            pts_Omset_P3 as pts_omset_p3,
            pts_Omset_P4 as pts_omset_p4,
            
            -- ROA Metrics
            ROA_P1 as roa_p1,
            ROA_P2 as roa_p2,
            ROA_P3 as roa_p3,
            ROA_P4 as roa_p4,
            
            -- ROA Points (actual points earned)
            pts_ROA_P1 as pts_roa_p1,
            pts_ROA_P2 as pts_roa_p2,
            pts_ROA_P3 as pts_roa_p3,
            
            -- Customer & Call Metrics
            Total_CB as total_customer,
            EC_Akumulasi as effective_calls,
            Poin_EC as pts_ec,
            
            -- ROA PARETO (3 items)
            roa_WFR_E02K, roa_NXT_E02K, roa_NXC_E02K,
            pts_roa_WFR_E02K, pts_roa_NXT_E02K, pts_roa_NXC_E02K,
            
            -- ROA PERANG (3 items)
            roa_WFR_E05K, roa_CSD_E02K, roa_ROL_E500,
            pts_roa_WFR_E05K, pts_roa_CSD_E02K, pts_roa_ROL_E500,
            
            -- ROA FUTURE (2 items)
            roa_TBK_E01K, roa_ROL_E01K,
            pts_roa_TBK_E01K, pts_roa_ROL_E01K,
            
            -- Scoring & Ranking
            Total_Score_Final as total_score,
            Raw_Month_Score as month_score,
            Ranking_Regional as rank_regional,
            
            -- Additional Metrics
            saldo_point as points_balance
            
        FROM {self.full_table_id}
        {where_clause}
        ORDER BY Ranking_Regional ASC, Total_Score_Final DESC
        {limit_clause}
        """
        
        try:
            if not self.client:
                raise Exception("BigQuery client is not initialized")
            if not self.full_table_id:
                raise Exception(f"BigQuery table not configured. project_id={self.project_id}, dataset={self.dataset}, table={self.table}")
            
            df = self.client.query(query).to_dataframe()
            return df
        except Exception as e:
            logger.error(f"Error fetching leaderboard: {e}")
            logger.error(f"Query was: {query[:200]}...")
            raise
    
    def get_kpis(self, region: str) -> Dict[str, Any]:
        """
        Get KPI summary for region
        
        Args:
            region: User's region code or 'ALL'
            
        Returns:
            Dictionary with KPI metrics
        """
        region_filter = self._apply_region_filter(region)
        
        query = f"""
        SELECT 
            SUM(Omset_P4) as total_revenue,
            SUM(target_oms) as total_target,
            ROUND(SUM(Omset_P4) / NULLIF(SUM(target_oms), 0) * 100, 2) as achievement_rate,
            ROUND((SUM(Omset_P4) - SUM(Omset_P3)) / NULLIF(SUM(Omset_P3), 0) * 100, 2) as growth_rate,
            COUNT(*) as total_salesman,
            AVG(Total_CB) as avg_customer_base,
            AVG(ROA_P4) as avg_roa
        FROM {self.full_table_id}
        {region_filter}
        """
        
        try:
            df = self.client.query(query).to_dataframe()
            
            if df.empty:
                return {
                    "total_revenue": 0,
                    "total_target": 0,
                    "achievement_rate": 0,
                    "growth_rate": 0,
                    "total_salesman": 0,
                    "avg_customer_base": 0,
                    "avg_roa": 0
                }
            
            row = df.iloc[0]
            
            # Calculate forecast (simple projection based on growth)
            forecast = row['total_revenue'] * (1 + row['growth_rate'] / 100) if row['growth_rate'] else row['total_revenue']
            
            return {
                "total_revenue": float(row['total_revenue']) if pd.notna(row['total_revenue']) else 0,
                "total_target": float(row['total_target']) if pd.notna(row['total_target']) else 0,
                "achievement_rate": float(row['achievement_rate']) if pd.notna(row['achievement_rate']) else 0,
                "growth_rate": float(row['growth_rate']) if pd.notna(row['growth_rate']) else 0,
                "forecast": float(forecast),
                "total_salesman": int(row['total_salesman']) if pd.notna(row['total_salesman']) else 0,
                "avg_customer_base": float(row['avg_customer_base']) if pd.notna(row['avg_customer_base']) else 0,
                "avg_roa": float(row['avg_roa']) if pd.notna(row['avg_roa']) else 0
            }
        except Exception as e:
            print(f"Error fetching KPIs: {e}")
            raise
    
    def get_sales_trend(self, region: str) -> pd.DataFrame:
        """
        Get sales trend by period (P1-P4)
        
        Args:
            region: User's region code or 'ALL'
            
        Returns:
            DataFrame with period-based sales data
        """
        region_filter = self._apply_region_filter(region)
        
        query = f"""
        SELECT 
            'Period 1' as period,
            SUM(Omset_P1) as total_sales,
            AVG(ROA_P1) as avg_roa,
            COUNT(*) as salesman_count
        FROM {self.full_table_id}
        {region_filter}
        
        UNION ALL
        
        SELECT 
            'Period 2' as period,
            SUM(Omset_P2) as total_sales,
            AVG(ROA_P2) as avg_roa,
            COUNT(*) as salesman_count
        FROM {self.full_table_id}
        {region_filter}
        
        UNION ALL
        
        SELECT 
            'Period 3' as period,
            SUM(Omset_P3) as total_sales,
            AVG(ROA_P3) as avg_roa,
            COUNT(*) as salesman_count
        FROM {self.full_table_id}
        {region_filter}
        
        UNION ALL
        
        SELECT 
            'Period 4' as period,
            SUM(Omset_P4) as total_sales,
            AVG(ROA_P4) as avg_roa,
            COUNT(*) as salesman_count
        FROM {self.full_table_id}
        {region_filter}
        
        ORDER BY period
        """
        
        try:
            df = self.client.query(query).to_dataframe()
            return df
        except Exception as e:
            print(f"Error fetching sales trend: {e}")
            raise
    
    def get_top_performers(self, region: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top performing salesman
        
        Args:
            region: User's region code or 'ALL'
            limit: Number of top performers to return
            
        Returns:
            List of top performers with key metrics
        """
        df = self.get_leaderboard(region, limit=limit)
        
        if df.empty:
            return []
        
        # Convert to list of dicts
        result = []
        for _, row in df.iterrows():
            result.append({
                "rank": int(row['rank_regional']),
                "name": row['salesman_name'],
                "division": row['division'],
                "region": row['region'],
                "sales": float(row['omset_p4']),
                "achievement_rate": float(row['achievement_rate']) if pd.notna(row['achievement_rate']) else 0,
                "score": float(row['total_score'])
            })
        
        return result
    
    def get_region_comparison(self) -> pd.DataFrame:
        """
        Get comparison across all regions (admin only)
        
        Returns:
            DataFrame with regional performance comparison
        """
        query = f"""
        SELECT 
            region,
            COUNT(*) as total_salesman,
            SUM(Omset_P4) as total_revenue,
            SUM(target_oms) as total_target,
            ROUND(SUM(Omset_P4) / NULLIF(SUM(target_oms), 0) * 100, 2) as achievement_rate,
            AVG(Total_Score_Final) as avg_score,
            AVG(ROA_P4) as avg_roa
        FROM {self.full_table_id}
        GROUP BY region
        ORDER BY total_revenue DESC
        """
        
        try:
            df = self.client.query(query).to_dataframe()
            return df
        except Exception as e:
            print(f"Error fetching region comparison: {e}")
            raise
    
    def get_cutoff_date(self) -> str:
        """
        Get latest cut-off date from cut_off table
        
        Returns:
            Latest cut-off date as string
        """
        query = f"""
        SELECT MAX(tgl_update) as latest_date
        FROM `{self.project_id}.{self.dataset}.cut_off`
        """
        
        try:
            df = self.client.query(query).to_dataframe()
            if df.empty or pd.isna(df.iloc[0]['latest_date']):
                return datetime.now().strftime('%Y-%m-%d')
            return df.iloc[0]['latest_date'].strftime('%Y-%m-%d')
        except Exception as e:
            print(f"Error fetching cutoff date: {e}")
            return datetime.now().strftime('%Y-%m-%d')
    
    def get_divisions(self, region: str) -> List[str]:
        """
        Get list of divisions in a region
        
        Args:
            region: User's region code or 'ALL'
            
        Returns:
            List of division codes
        """
        region_filter = self._apply_region_filter(region)
        
        query = f"""
        SELECT DISTINCT div_sls
        FROM {self.full_table_id}
        {region_filter}
        ORDER BY div_sls
        """
        
        try:
            df = self.client.query(query).to_dataframe()
            return df['div_sls'].tolist()
        except Exception as e:
            print(f"Error fetching divisions: {e}")
            raise


    def get_cutoff_metadata(self) -> Dict[str, Any]:
        """
        Fetch global metadata from cut_off table.
        Returns tgl_update and ideal target.
        """
        try:
            table_id = f"{self.project_id}.{self.dataset}.cut_off"
            query = f"""
                SELECT 
                    tgl_update,
                    ideal
                FROM `{table_id}`
                LIMIT 1
            """
            
            df = self.client.query(query).to_dataframe()
            
            if df.empty:
                return {"tgl_update": None, "ideal": None}
            
            row = df.iloc[0]
            return {
                "tgl_update": row['tgl_update'].strftime('%Y-%m-%d') if pd.notna(row['tgl_update']) else None,
                "ideal": float(row['ideal']) if pd.notna(row['ideal']) else None
            }
            
        except Exception as e:
            print(f"Error fetching cutoff metadata: {e}")
            return {"tgl_update": None, "ideal": None}


    def get_competition_ranks(
        self,
        level: str,
        competition_id: str = "amo_jan_2026",
        region: str = "ALL",
        role: str = "viewer",
        user_nik: Optional[str] = None,
        scope: Optional[str] = None,
        scope_id: Optional[str] = None,
        zona_rbm: Optional[str] = None,
        zona_bm: Optional[str] = None,
        limit: Optional[int] = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get competition ranking with hierarchical RLS and Zone-level visibility
        """
        from competition_config import get_competition_config
        
        config = get_competition_config(competition_id)
        if not config:
            raise ValueError(f"Invalid competition ID: {competition_id}")
            
        table_map = config.get("tables", {})
        
        if level.lower() not in table_map:
            raise ValueError(f"Invalid level: {level}")
            
        table_name = table_map[level.lower()]
        full_table_id = f"`{self.project_id}.{self.dataset}.{table_name}`"
        
        # --- Advanced RLS Filtering (NUANCED & ZONE-BASED) ---
        where_clauses = []
        user_role_lower = role.lower()
        active_level_lower = level.lower()
        
        is_admin = user_role_lower in ['super_admin', 'admin', 'master', 'head']
        
        if not is_admin:
            if active_level_lower == 'rbm':
                # Filter by ZONA_RBM (e.g. 'DP')
                if zona_rbm:
                    where_clauses.append(f"ZONA_RBM = '{zona_rbm}'")
                elif region != "ALL":
                    where_clauses.append(f"REGION = '{region}'")
                    
            elif active_level_lower == 'bm':
                # Filter by ZONA_BM (e.g. 'DP EAST')
                if zona_bm:
                    where_clauses.append(f"ZONA_BM = '{zona_bm}'")
                elif zona_rbm:
                    where_clauses.append(f"ZONA_RBM = '{zona_rbm}'")
                elif region != "ALL":
                    where_clauses.append(f"REGION = '{region}'")
                    
            elif active_level_lower == 'ass':
                # Filter by specific context
                if user_role_lower == 'bm' and scope_id:
                    where_clauses.append(f"(ZONA_BM = '{scope_id}' OR CABANG = '{scope_id}')")
                elif region != "ALL":
                    where_clauses.append(f"REGION = '{region}'")
        else:
            # Admin can filter manually if region is provided
            if region != "ALL":
                where_clauses.append(f"REGION = '{region}'")
                
        # Construct final WHERE
        where_clause = ""
        if where_clauses:
            where_clause = "WHERE " + " AND ".join(where_clauses)
            
        # Determine columns based on level/config
        name_col = "CABANG"
        rank_col = "rank_ASS"
        
        if level.lower() == 'ass':
            name_col = "NAMA_ASS"
            rank_col = "rank_ASS"
        elif level.lower() == 'bm':
            name_col = "CABANG" 
            rank_col = "rank_zona" 
        elif level.lower() == 'rbm':
            name_col = "ZONA_RBM"
            rank_col = "rank_zona"
            
        query = f"""
        SELECT 
            *
        FROM {full_table_id}
        {where_clause}
        ORDER BY {rank_col} ASC
        LIMIT {limit}
        """
        
        try:
            df = self.client.query(query).to_dataframe()
            if df.empty:
                return []
                
            # Normalize columns
            result = []
            for i, row in df.iterrows():
                # Flexible name resolution
                name_val = row.get(name_col, row.get('ZONA_BM', row.get('ZONA_RBM', row.get('CABANG', 'Unknown'))))
                
                # Handles rank column variations 
                rank_raw = row.get(rank_col)
                # Fallback if specific rank col is missing
                if pd.isna(rank_raw):
                    rank_raw = row.get('rank_regional', row.get('rank_zona', 999))
                rank_val = int(rank_raw) if pd.notna(rank_raw) else 999
                
                result.append({
                    "rank": rank_val,
                    "name": name_val,
                    "nik": row.get('NIK_ASS', ''),
                    "cabang": row.get('CABANG', ''),
                    "region": row.get('REGION', ''),
                    "zona_bm": row.get('ZONA_BM', ''),  # For BM filtering
                    "zona_rbm": row.get('ZONA_RBM', ''),  # For RBM filtering
                    "omset_ach": float(row.get('ach_oms', 0)) * 100,  # Convert to percentage
                    "roa_ach": float(row.get('ach_ROA', 0)) * 100,    # Convert to percentage
                    "total_point": int(row.get('total_Point', 0)),
                    "reward": int(row.get('REWARD', 0)),
                    "target": float(row.get('TARGET', 0)),
                    "omset": float(row.get('OMSET', 0)),
                    
                    # Point Breakdown - Detailed
                    "point_oms": int(row.get('point_oms', 0)),
                    "point_roa": int(row.get('point_ROA', 0)),
                    "point_roa_10krt": int(row.get('point_roa_10krt', 0)),
                    
                    # Additional breakdown fields
                    "cb": int(row.get('CB', 0)),
                    "act_roa": float(row.get('act_roa', 0)),
                    "total_roa_10krt": int(row.get('total_roa_10krt', 0)),
                    
                    "_raw_name": name_val
                })
                
            return result
            
        except Exception as e:
            print(f"Error fetching competition ranks: {e}")
            raise
            
        except Exception as e:
            print(f"Error fetching competition ranks: {e}")
            raise


# Singleton instance
_bigquery_service = None

def get_bigquery_service() -> BigQueryService:
    """Get or create BigQuery service instance"""
    global _bigquery_service
    if _bigquery_service is None:
        _bigquery_service = BigQueryService()
    return _bigquery_service
