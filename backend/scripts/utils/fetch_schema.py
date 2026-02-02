"""
Fetch schema metadata from Supabase REST API
"""
import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

base_url = f"{url}/rest/v1/"
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Accept-Profile": "master"
}

try:
    # Most PostgREST servers return the OpenAPI spec at the root
    response = requests.get(base_url, headers=headers)
    response.raise_for_status()
    spec = response.json()
    
    print("=== AVAILABLE TABLES IN master SCHEMA ===\n")
    # In OpenAPI spec, tables are usually in 'definitions' or 'paths'
    paths = spec.get('paths', {})
    tables = [p.strip('/') for p in paths.keys() if '/' not in p.strip('/')[1:]]
    
    for table in sorted(tables):
        print(f"- {table}")
        
except Exception as e:
    print(f"Error fetching schema: {e}")
    # Backup: try to query information_schema if enabled (usually not via REST)
