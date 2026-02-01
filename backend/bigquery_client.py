"""
BigQuery Client for Dashboard
Handles all BigQuery queries with Row-Level Security
"""
import os
from google.cloud import bigquery
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd


class BigQueryClient:
    """BigQuery client with RLS support"""
    
    def __init__(self):
        """Initialize BigQuery client with credentials"""
        # Set credentials path
        credentials_path = os.path.join(
            os.path.dirname(__file__), 
            'bigquery-credentials.json'
        )
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        # Initialize client
        self.client = bigquery.Client()
        self.project_id = "myproject-482315"
        self.dataset_id = "pma"
        self.table_id = "all_prc"
    
    def get_sales_summary(
        self, 
        user_region: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get sales summary data with RLS applied
        
        Args:
            user_region: User's region (A, B, C, D) or "ALL" for admin
            start_date: Start date (YYYY-MM-DD), default 90 days ago
            end_date: End date (YYYY-MM-DD), default today
        
        Returns:
            List of sales data dictionaries
        """
        # Default date range: last 90 days
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        
        # Build query with RLS
        region_filter = "" if user_region == "ALL" else "AND pma = @user_region"
        
        query = f"""
        SELECT 
            tgl as date,
            pma as region,
            SUM(qty) as total_quantity,
            SUM(value) as total_revenue,
            SUM(value_nett) as total_revenue_nett,
            COUNT(DISTINCT no_faktur) as transaction_count
        FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        WHERE tgl BETWEEN @start_date AND @end_date
        {region_filter}
        GROUP BY tgl, pma
        ORDER BY tgl DESC, pma
        """
        
        # Query parameters
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
                bigquery.ScalarQueryParameter("user_region", "STRING", user_region)
            ]
        )
        
        # Execute query
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        
        # Convert to list of dicts
        df = results.to_dataframe()
        return df.to_dict('records')
    
    def get_kpis(
        self, 
        user_region: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get KPI metrics for dashboard
        
        Args:
            user_region: User's region or "ALL"
            days: Number of days to calculate (default 30)
        
        Returns:
            Dictionary of KPI values
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        region_filter = "" if user_region == "ALL" else "AND pma = @user_region"
        
        query = f"""
        SELECT 
            SUM(value) as total_revenue,
            SUM(qty) as total_quantity,
            COUNT(DISTINCT no_faktur) as total_transactions,
            COUNT(DISTINCT kode_outlet) as total_outlets,
            COUNT(DISTINCT kode_salesman) as total_salesman
        FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        WHERE tgl BETWEEN @start_date AND @end_date
        {region_filter}
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
                bigquery.ScalarQueryParameter("user_region", "STRING", user_region)
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = list(query_job.result())
        
        if results:
            row = results[0]
            return {
                "total_revenue": float(row.total_revenue or 0),
                "total_quantity": float(row.total_quantity or 0),
                "total_transactions": int(row.total_transactions or 0),
                "total_outlets": int(row.total_outlets or 0),
                "total_salesman": int(row.total_salesman or 0)
            }
        
        return {
            "total_revenue": 0,
            "total_quantity": 0,
            "total_transactions": 0,
            "total_outlets": 0,
            "total_salesman": 0
        }
    
    def get_top_products(
        self, 
        user_region: str,
        limit: int = 10,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get top performing products
        
        Args:
            user_region: User's region or "ALL"
            limit: Number of top products to return
            days: Number of days to analyze
        
        Returns:
            List of top products with metrics
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        region_filter = "" if user_region == "ALL" else "AND pma = @user_region"
        
        query = f"""
        SELECT 
            kd_brg as product_code,
            ANY_VALUE(nm_brg) as product_name,
            SUM(qty) as total_quantity,
            SUM(value) as total_revenue
        FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        WHERE tgl BETWEEN @start_date AND @end_date
        {region_filter}
        GROUP BY kd_brg
        ORDER BY total_revenue DESC
        LIMIT @limit
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
                bigquery.ScalarQueryParameter("user_region", "STRING", user_region),
                bigquery.ScalarQueryParameter("limit", "INT64", limit)
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        
        df = results.to_dataframe()
        return df.to_dict('records')


# Singleton instance
_bigquery_client = None

def get_bigquery_client() -> BigQueryClient:
    """Get BigQuery client singleton"""
    global _bigquery_client
    if _bigquery_client is None:
        _bigquery_client = BigQueryClient()
    return _bigquery_client
