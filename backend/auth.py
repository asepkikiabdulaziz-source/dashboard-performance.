"""
Authentication and authorization utilities using Supabase
Optimized for scalability with caching and single-query resolution
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, Header
from supabase_client import get_supabase_client, supabase_request
from gotrue.errors import AuthApiError
from user_context_cache import (
    get_cached_user_context,
    set_cached_user_context,
    invalidate_user_context
)
from zone_resolution_service import resolve_zones_for_region
from logger import get_logger

logger = get_logger("auth")

def resolve_user_slot_context(email: str, use_cache: bool = True) -> Dict[str, Any]:
    """
    Dynamically resolve user role, region, and department from slot assignment.
    Optimized with caching and single-query RPC function.
    
    Args:
        email: User email address
        use_cache: Whether to use cache (default: True)
        
    Returns:
        User context dictionary with role, region, scope, etc.
    """
    # Check cache first
    if use_cache:
        cached = get_cached_user_context(email)
        if cached:
            logger.debug(f"Using cached context for {email}")
            return cached
    
    try:
        # OPTIMIZED: Use single RPC query instead of 4-5 separate queries
        headers_hr = {'Accept-Profile': 'hr'}
        
        # Try optimized RPC function first (if available)
        try:
            # Use RPC endpoint with proper schema prefix
            rpc_res = supabase_request(
                'POST',
                'rpc/get_user_context_by_email',
                json_data={'p_email': email},
                headers_extra=headers_hr
            )
            
            if rpc_res.get('data'):
                context_data = rpc_res['data']
                
                # Process RPC result
                region_resolved = context_data.get('region_name') or context_data.get('region_code')
                if not region_resolved or context_data.get('scope') == 'NATIONAL':
                    region_resolved = 'ALL'
                
                # Resolve zones (moved to separate service, non-blocking)
                zone_data = resolve_zones_for_region(region_resolved) if region_resolved != 'ALL' else {"zona_rbm": None, "zona_bm": None}
                zona_rbm = zone_data.get('zona_rbm') or context_data.get('grbm_code')
                zona_bm = zone_data.get('zona_bm')
                
                result = {
                    "name": context_data.get('name'),
                    "nik": context_data.get('nik'),
                    "slot_code": context_data.get('slot_code'),
                    "role": context_data.get('role', 'viewer'),
                    "region": region_resolved if region_resolved else 'ALL',
                    "zona_rbm": zona_rbm,
                    "zona_bm": zona_bm,
                    "scope": context_data.get('scope'),
                    "scope_id": context_data.get('scope_id'),
                    "depo_id": context_data.get('depo_id'),
                    "division_id": context_data.get('division_id')
                }
                
                # Cache the result
                if use_cache and result.get('nik'):
                    set_cached_user_context(email, result)
                
                logger.info(f"Resolved context via RPC for {email}: role={result.get('role')}, region={result.get('region')}")
                return result
        except Exception as rpc_error:
            logger.warning(f"RPC function not available, falling back to legacy queries: {rpc_error}")
        
        # FALLBACK: Legacy multi-query approach (if RPC not available)
        logger.debug(f"Resolving context (legacy) for email: {email}")
        
        # 1. Resolve NIK from email
        emp_res = supabase_request(
            'GET', 
            'employees', 
            params={'email': f"ilike.{email}", 'select': 'nik,full_name'}, 
            headers_extra=headers_hr
        )
        
        if not emp_res.get('data'):
            logger.warning(f"No employee found for email: {email}")
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
            logger.warning(f"No active assignment for NIK: {nik}")
            result = {"name": full_name, "nik": nik}
            if use_cache:
                set_cached_user_context(email, result)
            return result
            
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
            logger.warning(f"Slot {slot_code} not found in master.sales_slots")
            result = {"name": full_name, "nik": nik, "slot_code": slot_code}
            if use_cache:
                set_cached_user_context(email, result)
            return result
            
        slot = slot_res['data'][0]
        
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
                logger.debug(f"Resolved region: {region_resolved} | GRBM: {grbm_code}")

        # Resolve zones using separate service (non-blocking, cached)
        zone_data = resolve_zones_for_region(region_resolved) if region_resolved != 'ALL' else {"zona_rbm": None, "zona_bm": None}
        zona_rbm = zone_data.get('zona_rbm') or grbm_code
        zona_bm = zone_data.get('zona_bm')

        result = {
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
        
        # Cache the result
        if use_cache:
            set_cached_user_context(email, result)
        
        logger.info(f"Resolved context (legacy) for {email}: role={result.get('role')}, region={result.get('region')}")
        return result
        
    except Exception as e:
        logger.error(f"Error resolving slot context for {email}: {e}", exc_info=True)
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
             logger.warning(f"Auth verify failed: {response.status_code} - {response.text[:200]}")
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

        # DYNAMIC RESOLUTION: Prioritize Slot-based attributes (with caching)
        slot_context = resolve_user_slot_context(email, use_cache=True)
        if slot_context:
            logger.debug(f"Resolved dynamic context for {email}: role={slot_context.get('role')}, region={slot_context.get('region')}")
            res.update(slot_context)
            
        return res
    
    except HTTPException as he:
        raise he
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed (Internal): {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail="Authentication failed")


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate user using Supabase Auth (Raw HTTP)
    Returns dict with access_token and user info if successful
    """
    import os
    from connection_pool import get_http_session
    requests = get_http_session()  # Use pooled session
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        logger.error("Missing Supabase URL/Key - Check environment variables SUPABASE_URL and SUPABASE_KEY")
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
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        
        if response.status_code != 200:
            error_detail = response.text[:500] if response.text else "No error message"
            logger.warning(f"Auth Login Error for {email}: Status {response.status_code} - {error_detail}")
            # Log Supabase URL (without sensitive parts) for debugging
            logger.debug(f"Supabase URL: {url[:30]}... (truncated)")
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

        # DYNAMIC RESOLUTION: Prioritize Slot-based attributes (with caching)
        slot_context = resolve_user_slot_context(user.get("email"), use_cache=True)
        if slot_context:
            logger.debug(f"Resolved dynamic context for {user.get('email')}: role={slot_context.get('role')}, region={slot_context.get('region')}")
            res.update(slot_context)
            
        return res
        
    except Exception as e:
        logger.error(f"Unexpected Auth Error (HTTP): {str(e)}", exc_info=True)
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
