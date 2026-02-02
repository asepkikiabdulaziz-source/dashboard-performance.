
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def audit_schema():
    print("Auditing Database Schema via PostgREST OpenAPI...")
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")
    base_url = f"{url}/rest/v1/"
    
    schemas = ['public', 'master', 'hr']
    
    for schema in schemas:
        print(f"\nScanning Schema: {schema.upper()}...")
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Accept-Profile": schema,
            "Content-Profile": schema
        }
        
        try:
            resp = requests.get(base_url, headers=headers)
            if resp.status_code == 200:
                spec = resp.json()
                definitions = spec.get('definitions', {})
                tables = sorted(definitions.keys())
                
                if not tables:
                     print("  (No tables found or empty spec)")
                
                for t in tables:
                    full_name = f"{schema}.{t}"
                    # Only print columns for relevant tables
                    if t in ['ref_branches', 'ref_lookup']:
                        print(f"  - {full_name}")
                        props = definitions[t].get('properties', {})
                        print(f"    Columns: {sorted(list(props.keys()))}")
                    else:
                        print(f"  - {full_name}")
            else:
                print(f"  Failed. Status: {resp.status_code}")
                
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    audit_schema()
