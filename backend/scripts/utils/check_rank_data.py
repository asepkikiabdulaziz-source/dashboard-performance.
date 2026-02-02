
import os
from google.cloud import bigquery
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

def check_rank_distribution():
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'bigquery-credentials.json'
    client = bigquery.Client()
    project_id = os.getenv('BIGQUERY_PROJECT_ID', 'myproject-482315')
    dataset = os.getenv('BIGQUERY_DATASET', 'pma')
    
    query = f"""
    SELECT ZONA_RBM, rank_zona, COUNT(*) as count
    FROM `{project_id}.{dataset}.rank_rbm`
    WHERE rank_zona = 1
    GROUP BY ZONA_RBM, rank_zona
    """
    
    try:
        df = client.query(query).to_dataframe()
        print("\n=== Rank 1 distribution in rank_rbm ===")
        print(df)
        
        query2 = f"""
        SELECT *
        FROM `{project_id}.{dataset}.rank_rbm`
        ORDER BY total_Point DESC
        LIMIT 10
        """
        df2 = client.query(query2).to_dataframe()
        print("\n=== Top 10 by total_Point in rank_rbm ===")
        print(df2[['ZONA_RBM', 'total_Point', 'rank_zona']])
        
    try:
        query_ass = f"""
        SELECT REGION, rank_ASS, COUNT(*) as count
        FROM `{project_id}.{dataset}.rank_ass`
        WHERE rank_ASS = 1
        GROUP BY REGION, rank_ASS
        """
        df_ass = client.query(query_ass).to_dataframe()
        print("\n=== Rank 1 distribution in rank_ass ===")
        print(df_ass)
    except Exception as e:
        print(f"Error in rank_ass check: {e}")

if __name__ == "__main__":
    check_rank_distribution()
