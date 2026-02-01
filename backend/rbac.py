
from fastapi import HTTPException, Depends
from auth import get_current_user
from supabase_client import get_supabase_client

# Cache permissions to avoid hitting DB on every request (Basic In-Memory Cache)
# In production, use Redis. For now: Global Dict with TTL or just simple cache.
# Let's simple caching: Map Role -> Permissions List
ROLE_PERMISSIONS_CACHE = {}

def get_role_permissions(role_id: str) -> list:
    """
    Fetch permissions for a role from DB (with caching)
    """
    if role_id in ROLE_PERMISSIONS_CACHE:
        return ROLE_PERMISSIONS_CACHE[role_id]
        
    if role_id in ROLE_PERMISSIONS_CACHE:
        return ROLE_PERMISSIONS_CACHE[role_id]
        
    from supabase_client import supabase_request
    
    try:
        # Fetch permissions via HTTP
        # Schema: master
        headers = {'Accept-Profile': 'master'}
        res = supabase_request(
            'GET', 
            'trx_role_permissions', 
            params={'role_id': f"eq.{role_id}", 'select': 'permission_code'},
            headers_extra=headers
        )
            
        perms = [item['permission_code'] for item in res.get('data', [])]
        ROLE_PERMISSIONS_CACHE[role_id] = perms
        return perms
    except Exception as e:
        print(f"Error fetching permissions (HTTP) for role {role_id}: {e}")
        return []

def require_permission(permission_code: str):
    """
    Dependency to enforce permission requirement
    """
    def permission_checker(current_user: dict = Depends(get_current_user)):
        role_id = current_user.get('role')
        email = current_user.get('email', 'unknown')
        print(f"[RBAC] Checking '{permission_code}' for user: {email} (role: {role_id})")
        
        if not role_id:
             print(f"[RBAC] REJECTED: User {email} has no role!")
             raise HTTPException(status_code=403, detail="User has no role")
             
        # Super Admin Bypass (Optimization)
        if role_id == 'super_admin' or role_id == 'SUPER_ADMIN':
            print(f"[RBAC] BYPASS: Super Admin access granted for {email}")
            return True

        user_perms = get_role_permissions(role_id)
        print(f"[RBAC] User permissions: {user_perms}")
        
        if permission_code not in user_perms:
            print(f"[RBAC] REJECTED: User {email} lacks '{permission_code}' permission")
            raise HTTPException(
                status_code=403, 
                detail=f"Permission denied. Required: {permission_code}"
            )
        print(f"[RBAC] GRANTED: Permission '{permission_code}' verified for {email}")
        return True
        
    return permission_checker
