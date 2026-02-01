
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from auth import get_current_user
from supabase_client import supabase_request # Updated import
from models import (
    RefLookup, RefLookupCreate, RefLookupUpdate,
    RefBranch, RefBranchCreate, RefBranchUpdate,
    RefPMA, RefPMACreate, RefPMAUpdate,
    RefDistributor, RefDistributorCreate, RefDistributorUpdate,
    RefRole, RefRoleCreate, RefRoleUpdate,
    RefDivision, RefDivisionCreate, RefDivisionUpdate,
    RefRegion, RefRegionCreate, RefRegionUpdate, # NEW
    RefGRBM, RefGRBMCreate, RefGRBMUpdate        # NEW
)

from rbac import require_permission, get_role_permissions

router = APIRouter(
    prefix="/api/admin/master",
    tags=["admin-master"],
    responses={404: {"description": "Not found"}},
)

# Constants
ROLE_SUPER_ADMIN = "super_admin"

# Common Headers for Master schema
HEADERS_READ = {'Accept-Profile': 'master'}
HEADERS_WRITE = {'Content-Profile': 'master', 'Accept-Profile': 'master', 'Prefer': 'return=representation'}

# ==========================================
# 0. COMPANY MANAGEMENT (Super Admin Only)
# ==========================================
@router.get("/companies")
async def get_companies(
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.company.manage'))
):
    try:
        res = supabase_request('GET', 'ref_companies', params={'limit': 1000}, headers_extra=HEADERS_READ)
        return res.get('data', [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/companies")
async def create_company(
    item: dict,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.company.manage'))
):
    try:
        data = item.copy()
        res = supabase_request('POST', 'ref_companies', json_data=data, headers_extra=HEADERS_WRITE)
        return res.get('data', [])[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==========================================
# 0.1 ROLE MANAGEMENT
# ==========================================
@router.get("/roles", response_model=List[RefRole])
async def get_roles(
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.view'))
):
    try:
        res = supabase_request('GET', 'ref_role', params={'limit': 1000}, headers_extra=HEADERS_READ)
        return res.get('data', [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/roles", response_model=RefRole)
async def create_role(
    item: RefRoleCreate,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.manage'))
):
    try:
        res = supabase_request('POST', 'ref_role', json_data=item.dict(), headers_extra=HEADERS_WRITE)
        return res.get('data', [])[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==========================================
# 0.2 DIVISION MANAGEMENT
# ==========================================
@router.get("/divisions", response_model=List[RefDivision])
async def get_divisions(
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.view'))
):
    try:
        res = supabase_request('GET', 'rev_divisi', params={'limit': 1000}, headers_extra=HEADERS_READ)
        return res.get('data', [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 1. UNIVERSAL LOOKUP ENDPOINTS
# ==========================================

@router.get("/lookup/{category}", response_model=List[RefLookup])
async def get_lookups(
    category: str,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.view'))
):
    """
    Get all items for a specific category (e.g. REGION, GRBM).
    """
    try:
        # Filter by category
        res = supabase_request('GET', 'ref_lookup', params={'category': f"eq.{category.upper()}"}, headers_extra=HEADERS_READ)
        return res.get('data', [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/lookup", response_model=RefLookup)
async def create_lookup(
    item: RefLookupCreate,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.manage'))
):
    """Create a new lookup item"""
    try:
        # Force uppercase category
        data = item.dict()
        data['category'] = data['category'].upper()
        
        # Determine Company ID
        target_company_id = current_user.get('company_id', 'ID001')
        
        # Super Admin Override
        role_perms = get_role_permissions(current_user.get('role'))
        if 'master.company.manage' in role_perms and item.company_id:
             target_company_id = item.company_id
             
        data['company_id'] = target_company_id
        
        res = supabase_request('POST', 'ref_lookup', json_data=data, headers_extra=HEADERS_WRITE)
        return res.get('data', [])[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create lookup: {str(e)}")

@router.put("/lookup/{category}/{code}", response_model=RefLookup)
async def update_lookup(
    category: str,
    code: str,
    item: RefLookupUpdate,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.manage'))
):
    """Update lookup item"""
    try:
        data = item.dict(exclude_unset=True)
        res = supabase_request(
            'PATCH', 
            'ref_lookup', 
            params={'category': f"eq.{category.upper()}", 'code': f"eq.{code}"},
            json_data=data,
            headers_extra=HEADERS_WRITE
        )
        
        if not res.get('data'):
             raise HTTPException(status_code=404, detail="Item not found")
        return res.get('data', [])[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/lookup/{category}/{code}")
async def delete_lookup(
    category: str,
    code: str,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.manage'))
):
    try:
        # Prevent deleting REGION/GRBM via generic lookup endpoint to avoid confusion
        if category.upper() in ['REGION', 'GRBM']:
             raise HTTPException(status_code=400, detail=f"Please use specific /{category.lower()} endpoints")

        # Use return=representation (HEADER_WRITE) to get 200 OK
        res = supabase_request(
            'DELETE', 
            'ref_lookup', 
            params={'category': f"eq.{category.upper()}", 'code': f"eq.{code}"},
            headers_extra=HEADERS_WRITE
        )
        return {"message": "Deleted successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# SPECIAL LOOKUP: REGIONS (Joined with GRBM)
# ==========================================
@router.get("/regions", response_model=List[RefRegion])
async def get_regions(
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.view'))
):
    try:
        res = supabase_request('GET', 'ref_regions', params={'limit': 1000}, headers_extra=HEADERS_READ)
        return res.get('data', [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/grbm", response_model=List[RefGRBM])
async def get_grbm(
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.view'))
):
    try:
        res = supabase_request('GET', 'ref_grbm', params={'limit': 1000}, headers_extra=HEADERS_READ)
        return res.get('data', [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/regions", response_model=RefRegion)
async def create_region(
    item: RefRegionCreate, 
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.manage'))
):
    try:
        data = item.dict()
        data['company_id'] = 'ID001' # Default
        
        res = supabase_request('POST', 'ref_regions', json_data=data, headers_extra=HEADERS_WRITE)
        return res.get('data', [])[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/regions/{code}", response_model=RefRegion)
async def update_region(
    code: str,
    item: RefRegionUpdate, 
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.manage'))
):
    try:
        data = item.dict(exclude_unset=True)
        res = supabase_request(
            'PATCH', 
            'ref_regions',
            params={'region_code': f"eq.{code}"},
            json_data=data,
            headers_extra=HEADERS_WRITE
        )
        
        if not res.get('data'):
            raise HTTPException(status_code=404, detail="Region not found")
        return res.get('data', [])[0]
    except Exception as e:
         raise HTTPException(status_code=400, detail=str(e))

@router.delete("/regions/{code}")
async def delete_region(
    code: str,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.manage'))
):
    try:
        supabase_request(
            'DELETE', 
            'ref_regions', 
            params={'region_code': f"eq.{code}"},
            headers_extra=HEADERS_WRITE
        )
        return {"message": "Deleted successfully"}
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

# --- GRBM CRUD ---
@router.post("/grbm", response_model=RefGRBM)
async def create_grbm(
    item: RefGRBMCreate, 
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.manage'))
):
    try:
        data = item.dict()
        data['company_id'] = 'ID001'
        res = supabase_request('POST', 'ref_grbm', json_data=data, headers_extra=HEADERS_WRITE)
        return res.get('data', [])[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/grbm/{code}", response_model=RefGRBM)
async def update_grbm(
    code: str,
    item: RefGRBMUpdate, 
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.manage'))
):
    try:
        data = item.dict(exclude_unset=True)
        res = supabase_request(
            'PATCH', 
            'ref_grbm',
            params={'grbm_code': f"eq.{code}"},
            json_data=data,
            headers_extra=HEADERS_WRITE
        )
        
        if not res.get('data'):
            raise HTTPException(status_code=404, detail="GRBM not found")
        return res.get('data', [])[0]
    except Exception as e:
         raise HTTPException(status_code=400, detail=str(e))

@router.delete("/grbm/{code}")
async def delete_grbm(
    code: str,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.manage'))
):
    try:
        supabase_request(
            'DELETE', 
            'ref_grbm', 
            params={'grbm_code': f"eq.{code}"},
            headers_extra=HEADERS_WRITE
        )
        return {"message": "Deleted successfully"}
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# SPECIAL LOOKUP: HIERARCHY
# ==========================================
@router.get("/lookup/hierarchy/REGION_GRBM")
async def get_region_grbm_hierarchy(
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.view'))
):
    try:
        res = supabase_request('GET', 'ref_branches', params={'select': 'region_code,grbm_code', 'limit': 10000}, headers_extra=HEADERS_READ)
        
        mapping = {}
        for row in res.get('data', []):
            r = row.get('region_code')
            g = row.get('grbm_code')
            if r and g:
                mapping[r] = g
                
        result = [{"region_code": k, "grbm_code": v} for k, v in mapping.items()]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 2. BRANCH ENDPOINTS
# ==========================================

@router.get("/branches", response_model=List[RefBranch])
async def get_branches(
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.manage'))
):
    try:
        res = supabase_request('GET', 'ref_branches', params={'limit': 10000}, headers_extra=HEADERS_READ)
        return res.get('data', [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/branches", response_model=RefBranch)
async def create_branch(
    item: RefBranchCreate,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.manage'))
):
    try:
        data = item.dict()
        data['company_id'] = 'ID001'
        
        # Auto-fill GRBM from Region (New Table ref_regions)
        if data.get('region_code'):
            reg_res = supabase_request('GET', 'ref_regions', params={'region_code': f"eq.{data['region_code']}"}, headers_extra=HEADERS_READ)
            if reg_res.get('data'):
                # In ref_regions, the column IS grbm_code. No parent_code.
                data['grbm_code'] = reg_res['data'][0].get('grbm_code')

        res = supabase_request('POST', 'ref_branches', json_data=data, headers_extra=HEADERS_WRITE)
        return res.get('data', [])[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/branches/{branch_id}", response_model=RefBranch)
async def update_branch(
    branch_id: str,
    item: RefBranchUpdate,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.manage'))
):
    try:
        data = item.dict(exclude_unset=True)
        
        # Auto-fill GRBM from Region if Region is changed
        if data.get('region_code'):
            reg_res = supabase_request('GET', 'ref_regions', params={'region_code': f"eq.{data['region_code']}"}, headers_extra=HEADERS_READ)
            if reg_res.get('data'):
                data['grbm_code'] = reg_res['data'][0].get('grbm_code')

        res = supabase_request('PATCH', 'ref_branches', params={'id': f"eq.{branch_id}"}, json_data=data, headers_extra=HEADERS_WRITE)
        if not res.get('data'):
            raise HTTPException(status_code=404, detail="Branch not found")
        return res.get('data', [])[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 4. DISTRIBUTOR ENDPOINTS
# ==========================================

@router.get("/distributors", response_model=List[dict])
async def get_distributors(
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.view'))
):
    try:
        # Join with ref_branches
        params = {
            'select': '*, ref_branches:ref_branches!fk_distributors_branch(name, region_code, grbm_code)',
            'limit': 10000
        }
        res = supabase_request('GET', 'ref_distributors', params=params, headers_extra=HEADERS_READ)
        return res.get('data', [])
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@router.post("/distributors", response_model=dict)
async def create_distributor(
    item: dict,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.manage'))
):
    try:
        data = item.copy()
        data['company_id'] = 'ID001'
        res = supabase_request('POST', 'ref_distributors', json_data=data, headers_extra=HEADERS_WRITE)
        return res.get('data', [])[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/distributors/{kd_dist}", response_model=dict)
async def update_distributor(
    kd_dist: str,
    item: dict,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.manage'))
):
    try:
        data = item.copy()
        res = supabase_request('PATCH', 'ref_distributors', params={'kd_dist': f"eq.{kd_dist}"}, json_data=data, headers_extra=HEADERS_WRITE)
        if not res.get('data'):
            raise HTTPException(status_code=404, detail="Distributor not found")
        return res.get('data', [])[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 3. PRICE ZONES
# ==========================================
@router.get("/price_zones")
async def get_price_zones(
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.view'))
):
    try:
        res = supabase_request('GET', 'price_zones', headers_extra=HEADERS_READ)
        return res.get('data', [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/price_zones")
async def create_price_zone(
    item: dict,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.manage'))
):
    try:
        data = item.copy()
        data['company_id'] = 'ID001'
        res = supabase_request('POST', 'price_zones', json_data=data, headers_extra=HEADERS_WRITE)
        return res.get('data', [])[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/price_zones/{id}")
async def update_price_zone(
    id: str,
    item: dict,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.manage'))
):
    try:
        data = item.copy()
        data.pop('company_id', None)
        res = supabase_request('PATCH', 'price_zones', params={'id': f"eq.{id}"}, json_data=data, headers_extra=HEADERS_WRITE)
        return res.get('data', [])[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==========================================
# 5. PMA ENDPOINTS
# ==========================================

@router.get("/pma", response_model=List[RefPMA])
async def get_pma(
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.view'))
):
    try:
        # Deep join
        params = {
            'select': "*, ref_distributors:ref_distributors!fk_pma_distributor(name, parent_kd_dist, ref_branches:ref_branches!fk_distributors_branch(id, name, region_code, grbm_code))"
        }
        res = supabase_request('GET', 'ref_pma', params=params, headers_extra=HEADERS_READ)
        
        data = res.get('data', [])
        # Flatten parent_kd_dist
        for row in data:
            dist = row.get('ref_distributors')
            if dist and 'parent_kd_dist' in dist:
                row['parent_kd_dist'] = dist['parent_kd_dist']
                
        return data
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@router.post("/pma", response_model=RefPMA)
async def create_pma(
    item: RefPMACreate,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.manage'))
):
    try:
        data = item.dict()
        data['company_id'] = 'ID001'
        res = supabase_request('POST', 'ref_pma', json_data=data, headers_extra=HEADERS_WRITE)
        return res.get('data', [])[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/pma/{pma_code}", response_model=RefPMA)
async def update_pma(
    pma_code: str,
    item: RefPMAUpdate,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.manage'))
):
    try:
        data = item.dict(exclude_unset=True)
        
        # --- Handle Side-Effect: Update Distributor Parent ---
        parent_kd_dist = data.pop('parent_kd_dist', None)
        if parent_kd_dist is not None:
            dist_id = data.get('distributor_id')
            if not dist_id:
                curr_res = supabase_request('GET', 'ref_pma', params={'pma_code': f"eq.{pma_code}"}, headers_extra=HEADERS_READ)
                if curr_res.get('data'):
                     dist_id = curr_res['data'][0].get('distributor_id')
            
            if dist_id:
                supabase_request('PATCH', 'ref_distributors', params={'kd_dist': f"eq.{dist_id}"}, json_data={'parent_kd_dist': parent_kd_dist}, headers_extra=HEADERS_WRITE)

        # Update PMA
        if data: 
            res = supabase_request('PATCH', 'ref_pma', params={'pma_code': f"eq.{pma_code}"}, json_data=data, headers_extra=HEADERS_WRITE)
            if not res.get('data'):
                raise HTTPException(status_code=404, detail="PMA not found")
            return res.get('data', [])[0]
        else:
            # Return current
            res = supabase_request('GET', 'ref_pma', params={'pma_code': f"eq.{pma_code}"}, headers_extra=HEADERS_READ)
            return res.get('data', [])[0]
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
