"""
Authentication and authorization utilities using Supabase
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, Header
from supabase_client import get_supabase_client, supabase_request
from gotrue.errors import AuthApiError

def resolve_user_slot_context(email: str) -> Dict[str, Any]:
    """
    Dynamically resolve user role, region, and department from slot assignment.
    """
    print(f"[AUTH] Resolving context for email: {email}")
    try:
        # 1. Resolve NIK from email
        headers_hr = {'Accept-Profile': 'hr'}
        emp_res = supabase_request('GET', 'employees', params={'email': f"ilike.{email}", 'select': 'nik,full_name'}, headers_extra=headers_hr)
        print(f"[AUTH] Employee search result: {emp_res}")
        
        if not emp_res.get('data'):
            print(f"[AUTH] No employee found for email: {email}")
            return {}
            
        emp = emp_res['data'][0]
        nik = emp['nik']
        full_name = emp['full_name']
        
        # 2. Resolve active assignment
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        
        assign_res = supabase_request(
            'GET', 
            'assignments', 
            params={
                'nik': f"eq.{nik}", 
                'or': f"(end_date.is.null,end_date.gt.{today})",
                'select': 'slot_code'
            }, 
            headers_extra=headers_hr
        )
        
        if not assign_res.get('data'):
            print(f"[AUTH] No active assignment for NIK: {nik}")
            return {"name": full_name, "nik": nik}
            
        slot_code = assign_res['data'][0]['slot_code']
        
        # 3. Resolve Slot Details
        headers_master = {'Accept-Profile': 'master'}
        slot_res = supabase_request(
            'GET', 
            'sales_slots', 
            params={'slot_code': f"eq.{slot_code}", 'select': '*'}, 
            headers_extra=headers_master
        )
        
        if not slot_res.get('data'):
            print(f"[AUTH] Slot {slot_code} not found in master.sales_slots")
            return {"name": full_name, "nik": nik, "slot_code": slot_code}
            
        slot = slot_res['data'][0]
        print(f"[AUTH] Found slot data: {slot}")
        
        # 4. Resolve Full Region Name (for BigQuery compatibility)
        region_resolved = slot.get('scope_id')
        if not region_resolved or slot.get('scope') == 'NATIONAL':
            region_resolved = 'ALL'
            
        grbm_code = None
        if slot.get('scope') == 'REGION' and region_resolved != 'ALL':
            region_res = supabase_request(
                'GET', 
                'ref_regions', 
                params={'region_code': f"eq.{region_resolved}", 'select': 'name,grbm_code'}, 
                headers_extra=headers_master
            )
            if region_res.get('data'):
                region_resolved = region_res['data'][0]['name']
                grbm_code = region_res['data'][0].get('grbm_code')
                print(f"[AUTH] Resolved full region name: {region_resolved} | GRBM: {grbm_code}")

        # 5. Resolve Competition Zones (ZONA_RBM, ZONA_BM) from BigQuery
        zona_rbm = grbm_code
        zona_bm = None
        
        if region_resolved != 'ALL':
            try:
                from bigquery_service import get_bigquery_service
                bq = get_bigquery_service()
                # Query mapping for this region
                zone_query = f"""
                SELECT DISTINCT ZONA_RBM, ZONA_BM 
                FROM `{bq.project_id}.{bq.dataset}.rank_ass` 
                WHERE REGION = '{region_resolved}' 
                LIMIT 1
                """
                zone_df = bq.client.query(zone_query).to_dataframe()
                if not zone_df.empty:
                    zona_rbm = zone_df.iloc[0]['ZONA_RBM']
                    zona_bm = zone_df.iloc[0]['ZONA_BM']
                    print(f"[AUTH] Resolved BQ Zones: RBM={zona_rbm}, BM={zona_bm}")
            except Exception as bqe:
                print(f"[AUTH] BigQuery Zone Resolution Error: {bqe}")

        return {
            "name": full_name,
            "nik": nik,
            "slot_code": slot_code,
            "role": slot.get('role', 'viewer'),
            "region": region_resolved,
            "zona_rbm": zona_rbm,
            "zona_bm": zona_bm,
            "scope": slot.get('scope'),
            "scope_id": slot.get('scope_id'),
            "depo_id": slot.get('depo_id'),
            "division_id": slot.get('division_id')
        }
        
    except Exception as e:
        print(f"[AUTH] Error resolving slot context: {e}")
        return {}

def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify JWT token using Supabase Auth (Raw HTTP to bypass library issues)
    """
    # supabase = get_supabase_client() # Removed due to proxy crash
    
    import os
    import requests
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        raise HTTPException(status_code=500, detail="Server misconfiguration: Missing Supabase URL/Key")

    try:
        # Call Supabase Auth API Directly
        # Endpoint: GET /auth/v1/user
        api_url = f"{url}/auth/v1/user"
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(api_url, headers=headers)
        
        if response.status_code != 200:
             print(f"Auth verify failed: {response.text}")
             raise HTTPException(status_code=401, detail="Invalid token or expired session")
             
        user_data = response.json()
        
        # User object might be nested or direct depending on endpoint version, usually its direct or inside 'data'?
        # /auth/v1/user returns User object directly.
        # But let's check structure safe access.
        
        # NOTE: GoTrue API returns User object.
        # Structure: { "id": "...", "email": "...", "user_metadata": { ... } }
        
        user_id = user_data.get("id")
        email = user_data.get("email")
        metadata = user_data.get("user_metadata", {})
        
        if not user_id:
             raise HTTPException(status_code=401, detail="Invalid token response structure")

        # Map Supabase User Metadata to our app's expected format
        res = {
            "sub": email,
            "email": email,
            "id": user_id,
            "name": metadata.get("name", "Unknown User"),
            "region": metadata.get("region", "UNKNOWN"),
            "role": metadata.get("role", "viewer")
        }

        # DYNAMIC RESOLUTION: Prioritize Slot-based attributes
        slot_context = resolve_user_slot_context(email)
        if slot_context:
            print(f"[AUTH] Resolved dynamic context for {email}: {slot_context}")
            res.update(slot_context)
            
        return res
    
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Token verification failed (Internal): {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate user using Supabase Auth (Raw HTTP)
    Returns dict with access_token and user info if successful
    """
    # supabase = get_supabase_client()
    import os
    import requests
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("Missing Supabase URL/Key")
        return None

    try:
        # POST /auth/v1/token?grant_type=password
        api_url = f"{url}/auth/v1/token?grant_type=password"
        headers = {
            "apikey": key,
            "Content-Type": "application/json"
        }
        payload = {
            "email": email,
            "password": password
        }
        
        response = requests.post(api_url, headers=headers, json=payload)
        
        if response.status_code != 200:
            print(f"Auth Login Error: {response.text}")
            return None
            
        data = response.json()
        access_token = data.get("access_token")
        user = data.get("user")
        
        if not access_token or not user:
            return None
            
        metadata = user.get("user_metadata", {})
        
        res = {
            "access_token": access_token,
            "email": user.get("email"),
            "name": metadata.get("name", "Unknown User"),
            "region": metadata.get("region", "UNKNOWN"),
            "role": metadata.get("role", "viewer")
        }

        # DYNAMIC RESOLUTION: Prioritize Slot-based attributes
        slot_context = resolve_user_slot_context(user.get("email"))
        if slot_context:
            print(f"[AUTH] Resolved dynamic context for {user.get('email')}: {slot_context}")
            res.update(slot_context)
            
        return res
        
    # except AuthApiError as e: # AuthApiError might not be importable if not using lib
    except Exception as e:
        print(f"Unexpected Auth Error (HTTP): {str(e)}")
        return None


def get_user_region(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract user region from JWT token (using Supabase validation)
    Returns 'ALL' for admin users or users without assigned region
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        
        payload = verify_token(token)
        region = payload.get("region")
        
        # Return 'ALL' for users without specific region (e.g., admin users)
        if not region:
            return "ALL"
        
        return region
    
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")


def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Get current user from JWT token
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        scheme, token = authorization.split()
        
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        
        return verify_token(token)
    
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
