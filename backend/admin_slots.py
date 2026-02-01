from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from pydantic import BaseModel
from supabase_client import get_supabase_client
from auth import get_current_user
from rbac import require_permission

router = APIRouter(prefix="/api/admin/slots", tags=["admin-slots"])

# --- Models ---
class SlotBase(BaseModel):
    slot_code: str
    sales_code: str
    role_id: str = "salesman" # Default
    parent_slot_code: Optional[str] = None
    scope: str = "DEPO" # DEPO, BRANCH, REGION
    scope_id: Optional[str] = None # The specific ID covered
    is_active: bool = True

# Consolidating SlotCreate below

class SlotUpdate(BaseModel):
    sales_code: Optional[str] = None
    role_id: Optional[str] = None
    parent_slot_code: Optional[str] = None
    scope: Optional[str] = None
    scope_id: Optional[str] = None
    is_active: Optional[bool] = None

class AssignmentRequest(BaseModel):
    nik: str
    reason: Optional[str] = "New Assignment"

class SlotCreate(BaseModel):
    slot_code: str
    sales_code: str
    role: str
    division_id: Optional[str] = None
    depo_id: Optional[str] = None
    scope: str = "DEPO"  # DEPO, BRANCH, REGION
    scope_id: Optional[str] = None
    level: Optional[int] = None
    parent_slot_code: Optional[str] = None

# --- Endpoints ---

@router.get("/", response_model=dict)
async def get_slots(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=10000),
    search: Optional[str] = None,
    role: Optional[str] = None,
    # Slicers
    region_id: Optional[str] = None,
    branch_id: Optional[str] = None,
    depo_id: Optional[str] = None,
    division_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.view'))
):
    """
    Get all slots with pagination and hierarchical slicers.
    Uses Direct DB Columns for Filtering + Lookups for Names.
    """
    from supabase_client import supabase_request
    
    # Common Headers for Master Data schema
    master_headers = {'Accept-Profile': 'master'}

    try:
        # Pre-Query: Resolve Hierarchy using Recursion
        # Region/Branch -> requires expanding to Depo IDs for filtering heterogeneous scopes
        allowed_depo_ids = set()
        allowed_scope_ids = set()
        hierarchy_active = False

        if depo_id:
            allowed_depo_ids.add(depo_id)
            allowed_scope_ids.add(depo_id)
            hierarchy_active = True
            
        elif branch_id:
            hierarchy_active = True
            allowed_scope_ids.add(branch_id)
            d_res = supabase_request('GET', 'ref_distributors', params={'branch_id': f"eq.{branch_id}", 'select': 'kd_dist'}, headers_extra=master_headers)
            d_ids = [d['kd_dist'] for d in d_res.get('data', [])]
            allowed_depo_ids.update(d_ids)

        elif region_id:
            hierarchy_active = True
            allowed_scope_ids.add(region_id)
            # Branches of Region
            b_res = supabase_request('GET', 'ref_branches', params={'region_code': f"eq.{region_id}", 'select': 'id'}, headers_extra=master_headers)
            b_ids = [b['id'] for b in b_res.get('data', [])]
            allowed_scope_ids.update(b_ids)
            
            # Distributors of Branches
            if b_ids:
                vals = ",".join(b_ids)
                d_res = supabase_request('GET', 'ref_distributors', params={'branch_id': f"in.({vals})", 'select': 'kd_dist'}, headers_extra=master_headers)
                d_ids = [d['kd_dist'] for d in d_res.get('data', [])]
                allowed_depo_ids.update(d_ids)
                 
        # --- Build Query Params ---
        start = (page - 1) * page_size
        end = start + page_size - 1
        
        params = {
            'select': '*',
            'limit': page_size,
            'offset': start,
            'order': 'slot_code.asc'
        }
        
        headers_extra = {
            'Range': f"{start}-{end}",
            'Accept-Profile': 'master'
        }
        
        # --- Filters ---
        
        # 1. Enhanced Search (Employee Name, NIK, Depo Name, Slot Code, Sales Code)
        search_slot_codes = set()  # Collect slot codes from various search sources
        
        if search:
            # Search in employees (name or NIK) to find active assignments
            try:
                headers_hr = {'Accept-Profile': 'hr'}
                emp_search_res = supabase_request(
                    'GET', 
                    'employees',
                    params={
                        'or': f"(full_name.ilike.*{search}*,nik.ilike.*{search}*)",
                        'select': 'nik'
                    },
                    headers_extra=headers_hr
                )
                
                matching_niks = [e['nik'] for e in emp_search_res.get('data', [])]
                
                if matching_niks:
                    # Find active assignments for these employees
                    from datetime import datetime
                    today = datetime.now().strftime('%Y-%m-%d')
                    
                    nik_vals = ",".join(matching_niks)
                    assign_search_res = supabase_request(
                        'GET',
                        'assignments',
                        params={
                            'nik': f"in.({nik_vals})",
                            'or': f"(end_date.is.null,end_date.gt.{today})",
                            'select': 'slot_code'
                        },
                        headers_extra=headers_hr
                    )
                    
                    for a in assign_search_res.get('data', []):
                        search_slot_codes.add(a['slot_code'])
            except Exception as e:
                print(f"Employee search warning: {e}")
            
            # Search in distributors (depo names)
            try:
                depo_search_res = supabase_request(
                    'GET',
                    'ref_distributors',
                    params={
                        'name': f"ilike.*{search}*",
                        'select': 'kd_dist'
                    },
                    headers_extra=master_headers
                )
                
                matching_depo_ids = [d['kd_dist'] for d in depo_search_res.get('data', [])]
                
                if matching_depo_ids:
                    # Find slots with these depo_ids
                    depo_vals = ",".join(matching_depo_ids)
                    depo_slot_res = supabase_request(
                        'GET',
                        'sales_slots',
                        params={
                            'depo_id': f"in.({depo_vals})",
                            'select': 'slot_code'
                        },
                        headers_extra=master_headers
                    )
                    
                    for s in depo_slot_res.get('data', []):
                        search_slot_codes.add(s['slot_code'])
            except Exception as e:
                print(f"Depo search warning: {e}")
            
            # Build final search query
            # Combine: direct slot/sales code match OR slot_code in found codes
            search_parts = [f"slot_code.ilike.*{search}*", f"sales_code.ilike.*{search}*"]
            
            if search_slot_codes:
                slot_vals = ",".join(list(search_slot_codes))
                search_parts.append(f"slot_code.in.({slot_vals})")
            
            params['or'] = f"({','.join(search_parts)})"
             
        # 2. Direct Column Filters (Verified via Inspection)
        if role:
            # Map frontend role names to DB values if needed, otherwise direct
            # DB values are like 'SO', 'SM' etc. Frontend sends 'salesman'?
            # Let's use ILIKE pattern to be safe.
            params['role'] = f"ilike.*{role}*"
            
        if division_id:
            params['division_id'] = f"eq.{division_id}"

        # 3. Hierarchy Slicer (Complex Logic)
        if hierarchy_active:
             print(f"DEBUG SLICER ACTIVE: Region={region_id}, Branch={branch_id}, Depo={depo_id}")
             print(f"DEBUG ALLOWED DEPOS: {len(allowed_depo_ids)}")
             
             # Logic: (depo_id IN allowed_depos) OR (scope_id IN allowed_scopes)
             
             or_parts = []
             if allowed_depo_ids:
                vals = ",".join(list(allowed_depo_ids))
                or_parts.append(f"depo_id.in.({vals})")
                
             if allowed_scope_ids:
                vals = ",".join(list(allowed_scope_ids))
                or_parts.append(f"scope_id.in.({vals})")
            
             if or_parts:
                hierarchy_or = ",".join(or_parts)
                # Force replace OR for hierarchy
                params['or'] = f"({hierarchy_or})"
                print(f"DEBUG PARAMS OR: {params['or']}")
                
                # RE-ADD Search as single column filter?
                # If search is present, let's try to filter `sales_code` only?
                # params['sales_code'] = f"ilike.*{search}*"
                # This restores some search capability.
                if search:
                    params['sales_code'] = f"ilike.*{search}*"
            
             elif not allowed_depo_ids and not allowed_scope_ids:
                 # Hierarchy selected but nothing found (e.g. Region with no branches)
                 params['slot_code'] = "eq.INVALID_FORCE_EMPTY"
                  
        # Execute Main Query (Support for fetching >1000 records)
        all_slots = []
        current_offset = start
        total = 0  # Initialize total to prevent UnboundLocalError
        
        while len(all_slots) < page_size:
            # Calculate chunk size (max 1000 for PostgREST)
            chunk_size = min(1000, page_size - len(all_slots))
            params['limit'] = chunk_size
            params['offset'] = current_offset
            
            # Update Range header for Supabase
            chunk_end = current_offset + chunk_size - 1
            headers_extra['Range'] = f"{current_offset}-{chunk_end}"
            
            response = supabase_request('GET', 'sales_slots', params=params, headers_extra=headers_extra)
            data = response.get('data', [])
            total = response.get('count', total) # Update total if returned
            
            if not data:
                break
                
            all_slots.extend(data)
            current_offset += len(data)
            
            # If we got fewer than 1000, it means we reached the end of the DB
            if len(data) < 1000:
                break
        
        slots = all_slots
        
        # 4. Resolve Names (Lookups)
        # This handles the "columns don't exist" (names) part
        try:
            dist_ids = set()
            branch_ids = set()
            region_codes = set()
            
            for s in slots:
                if s.get('depo_id'): dist_ids.add(s['depo_id'])
                if s.get('scope') == 'BRANCH' and s.get('scope_id'): branch_ids.add(s['scope_id'])
                if s.get('scope') == 'REGION' and s.get('scope_id'): region_codes.add(s['scope_id'])
            
            names_map = {}
            if dist_ids:
                vals = ",".join(list(dist_ids))
                res = supabase_request('GET', 'ref_distributors', params={'kd_dist': f"in.({vals})", 'select': 'kd_dist,name'}, headers_extra=master_headers)
                for row in res.get('data', []): names_map[f"DIST:{row['kd_dist']}"] = row['name']
            
            if branch_ids:
                vals = ",".join(list(branch_ids))
                res = supabase_request('GET', 'ref_branches', params={'id': f"in.({vals})", 'select': 'id,name'}, headers_extra=master_headers)
                for row in res.get('data', []): names_map[f"BRANCH:{row['id']}"] = row['name']
                
            if region_codes:
                vals = ",".join(list(region_codes))
                # OLD: ref_lookup
                # NEW: ref_regions
                res = supabase_request('GET', 'ref_regions', params={'region_code': f"in.({vals})", 'select': 'region_code,name'}, headers_extra=master_headers)
                for row in res.get('data', []): names_map[f"REGION:{row['region_code']}"] = row['name']

            for s in slots:
                if s.get('depo_id'): s['depo_name'] = names_map.get(f"DIST:{s['depo_id']}", s['depo_id'])
                if s.get('scope_id'): 
                    key = f"{s.get('scope')}:{s.get('scope_id')}"
                    s['scope_name'] = names_map.get(key, s.get('scope_id'))
                    
        except Exception as e:
            print(f"Name resolution warning: {e}")
            
        # 5. Fetch Assignments
        # ... (Existing code for assignments is fine) ...
        # Need to ensure we get assignment info
        slot_codes = [s['slot_code'] for s in slots]
        if slot_codes:
             vals = ",".join(slot_codes)
             
             # Optimization: Chunk assignment fetching if too many slots
             # PostgREST URL length limit might be an issue with 2000+ slots
             # Let's fetch assignments in chunks of 500
             
             assignments_map = {}
             
             chunk_size = 200
             for i in range(0, len(slot_codes), chunk_size):
                 chunk = slot_codes[i:i + chunk_size]
                 vals = ",".join(chunk)
                 
                 # Fetch assignments
                 headers_hr = {'Accept-Profile': 'hr'}
                 a_res = supabase_request('GET', 'assignments', params={'slot_code': f"in.({vals})", 'select': '*', 'order': 'start_date.desc'}, headers_extra=headers_hr)
                 
                 # Process assignments...
                 for a in a_res.get('data', []):
                     sc = a['slot_code']
                     if sc not in assignments_map: # Only take latest because of order desc
                         assignments_map[sc] = a
                         
             # Merge back
             for s in slots:
                 assign = assignments_map.get(s['slot_code'])
                 if assign:
                     s['current_nik'] = assign.get('nik')
                     s['current_name'] = assign.get('employee_name') # View might act differently
                     s['assigned_since'] = assign.get('start_date')
                     
                     # Need to fetch employee name if not in assignment view?
                     # Let's assume assignment view has it or we fetch it?
                     # Standard table might not have name via foreign key expand?
                     # For now let's leave it, frontend handles missing name?
                     # Better: fetch employee names for these NIKs
                     pass
        
        # Resolve Employee Names for assignments (Optimization)
        niks = set()
        for s in slots:
            if s.get('current_nik'): niks.add(s['current_nik'])
            
        if niks:
            # Chunk fetch employees
            names_map = {}
            nik_list = list(niks)
            chunk_size = 200
            for i in range(0, len(nik_list), chunk_size):
                 chunk = nik_list[i:i + chunk_size]
                 vals = ",".join(chunk)
                 
                 headers_hr = {'Accept-Profile': 'hr'}
                 emp_res = supabase_request('GET', 'employees', params={'nik': f"in.({vals})", 'select': 'nik,full_name'}, headers_extra=headers_hr)
                 for e in emp_res.get('data', []):
                     names_map[e['nik']] = e['full_name']
                     
            for s in slots:
                if s.get('current_nik'):
                    s['current_name'] = names_map.get(s['current_nik'], s['current_nik'])

        return {
            "data": slots,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"CRITICAL ERROR IN GET_SLOTS: {str(e)}")
        print(error_msg)
        with open("slots_error.log", "w") as f:
            f.write(error_msg)
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")

@router.post("/")
async def create_slot(
    slot: SlotCreate,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.manage'))
):
    """
    Create a new slot
    """
    from supabase_client import supabase_request
    import traceback
    import requests
    
    try:
        print(f"[CREATE_SLOT] Received data: {slot.dict()}")
        
        headers = {'Accept-Profile': 'master', 'Content-Profile': 'master', 'Prefer': 'return=representation'}
        
        # Check if slot_code already exists
        print(f"[CREATE_SLOT] Checking if slot_code exists: {slot.slot_code}")
        check_res = supabase_request(
            'GET',
            'sales_slots',
            params={'slot_code': f"eq.{slot.slot_code}", 'select': 'slot_code'},
            headers_extra=headers
        )
        
        if check_res.get('data'):
            print(f"[CREATE_SLOT] Slot code already exists: {slot.slot_code}")
            raise HTTPException(status_code=400, detail=f"Slot code '{slot.slot_code}' already exists")
        
        # Create slot
        slot_data = slot.dict()
        print(f"[CREATE_SLOT] Prepared slot data: {slot_data}")
        
        # Auto-set scope_id based on scope type
        if slot.scope == 'DEPO' and slot.depo_id:
            slot_data['scope_id'] = slot.depo_id
        # For BRANCH/REGION, scope_id should already be set from frontend
        
        print(f"[CREATE_SLOT] Sending POST request to Supabase...")
        res = supabase_request(
            'POST',
            'sales_slots',
            json_data=slot_data,
            headers_extra=headers
        )
        
        print(f"[CREATE_SLOT] Success! Response: {res}")
        return {"message": "Slot created successfully", "data": res.get('data')}
        
    except requests.exceptions.HTTPError as he:
        err_body = he.response.text if hasattr(he, 'response') else str(he)
        print(f"[CREATE_SLOT] Database HTTP Error: {err_body}")
        raise HTTPException(status_code=400, detail=f"Database error: {err_body}")
    except HTTPException as he:
        print(f"[CREATE_SLOT] HTTP Exception: {he.detail}")
        raise
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"[CREATE_SLOT] CRITICAL ERROR: {str(e)}")
        print(f"[CREATE_SLOT] Traceback:\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@router.post("/{slot_code}/assign")
async def assign_employee(
    slot_code: str,
    req: AssignmentRequest,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.manage'))
):
    """
    Assign an employee to a slot.
    Automatically 'ends' the previous assignment for this slot.
    """
    from supabase_client import supabase_request
    from datetime import datetime
    import requests
    import traceback
    
    try:
        now_str = datetime.now().strftime('%Y-%m-%d')
        print(f"[ASSIGN_EMPLOYEE] Assigning {req.nik} to {slot_code}")
        
        # Headers for HR schema operations
        headers_hr = {
            'Content-Profile': 'hr',
            'Accept-Profile': 'hr',
            'Prefer': 'return=representation' # To get data back
        }
        
        # 1. End current assignment (if any)
        # PATCH /assignments?slot_code=eq.X&end_date=is.null
        print(f"[ASSIGN_EMPLOYEE] Ending previous assignments for {slot_code}")
        patch_params = {
            'slot_code': f"eq.{slot_code}",
            'end_date': 'is.null'
        }
        patch_body = {'end_date': now_str}
        
        try:
            supabase_request('PATCH', 'assignments', params=patch_params, json_data=patch_body, headers_extra=headers_hr)
        except Exception as patch_err:
            print(f"[ASSIGN_EMPLOYEE] Warning patching previous assignments: {patch_err}")
            # We continue even if no previous assignment found or patch fails
            
        # 2. Create new assignment
        new_assign = {
            "slot_code": slot_code,
            "nik": req.nik,
            "start_date": now_str,
            "reason": req.reason
            # "created_by" removed as it doesn't exist in schema
        }
        
        print(f"[ASSIGN_EMPLOYEE] Sending POST request to Supabase with data: {new_assign}")
        # POST /assignments
        res = supabase_request('POST', 'assignments', json_data=new_assign, headers_extra=headers_hr)
        
        print(f"[ASSIGN_EMPLOYEE] Success! Response: {res}")
        return {"message": "Assignment successful", "data": res.get('data')}
        
    except requests.exceptions.HTTPError as he:
        err_body = he.response.text if hasattr(he, 'response') else str(he)
        print(f"[ASSIGN_EMPLOYEE] Database HTTP Error: {err_body}")
        raise HTTPException(status_code=400, detail=f"Database error: {err_body}")
    except HTTPException as he:
        print(f"[ASSIGN_EMPLOYEE] HTTP Exception: {he.detail}")
        raise
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"[ASSIGN_EMPLOYEE] CRITICAL ERROR: {str(e)}")
        print(f"[ASSIGN_EMPLOYEE] Traceback:\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
        

class SlotUpdate(BaseModel):
    sales_code: Optional[str] = None
    role: Optional[str] = None
    division_id: Optional[str] = None
    depo_id: Optional[str] = None
    scope: Optional[str] = None
    scope_id: Optional[str] = None
    level: Optional[int] = None
    parent_slot_code: Optional[str] = None

@router.put("/{slot_code}")
async def update_slot(
    slot_code: str,
    slot: SlotUpdate,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.manage'))
):
    """
    Update slot details (Division, Depo, etc.)
    """
    from supabase_client import supabase_request
    
    update_data = {k: v for k, v in slot.dict().items() if v is not None}
    if not update_data:
         raise HTTPException(status_code=400, detail="No fields to update")
         
    # Logic to maintain consistency:
    # If scope is changd to DEPO, or depo_id is changed while scope is DEPO:
    # scope_id must equal depo_id.
    
    # We might need current slot state if not all fields are provided, 
    # but for simplicity, if frontend sends both, we prefer `depo_id` as source for `scope_id` in DEPO case.
    
    # New scope provided?
    new_scope = update_data.get('scope')
    new_depo = update_data.get('depo_id')
    
    if new_scope == 'DEPO':
        # If switching to DEPO, scope_id MUST be depo_id
        if new_depo:
            update_data['scope_id'] = new_depo
        # If new_depo not provided, we assume it's valid or relies on existing? 
        # Ideally frontend sends full context or strict validation.
        # But if depo_id is updated without scope change, and existing scope is DEPO? 
        # We'd need to fetch existing. Let's trust frontend sends consistent pairs for now.
        
    elif new_depo and not new_scope:
        # Updating depo_id only. If current logical scope is DEPO (implied), update scope_id too?
        # Safety: implicitly update scope_id if it looks like a depo update
        update_data['scope_id'] = new_depo 
        # Refinement: This assumes if you update depo_id you want scope_id updated. 
        # For BRANCH/REGION managers, depo_id is usually NULL or irrelevant to scope_id.
        # So this might be risky if we don't know current scope.
        # Let's rely on Frontend sending explicit scope_id values or DB constraint catching it.
        pass

    # Explicit override: If updating DEPO, ensure scope_id matches
    if 'depo_id' in update_data and (new_scope == 'DEPO' or ('scope' not in update_data)):
         # If we are potentially in DEPO scope (or moving to it), sync scope_id
         # Optimistic approach:
         if new_scope == 'DEPO' or (not new_scope): 
             # note: verifying "current scope is DEPO" would require a fetch.
             # cost-benefit: fetch is safer.
             pass

    # Re-logic: Fetch current slot to be safe?
    # Or just let DB constraint fail if invalid?
    # Let's add a fetch for safety if scope-related fields are touched.
    if 'scope' in update_data or 'depo_id' in update_data or 'scope_id' in update_data:
        # Fetch current
         from supabase_client import supabase_request
         curr_res = supabase_request('GET', 'sales_slots', params={'slot_code': f"eq.{slot_code}"}, headers_extra={'Accept-Profile': 'master'})
         if curr_res.get('data'):
             curr = curr_res['data'][0]
             # Determine final state
             final_scope = update_data.get('scope', curr.get('scope'))
             final_depo = update_data.get('depo_id', curr.get('depo_id'))
             
             if final_scope == 'DEPO':
                 update_data['scope_id'] = final_depo
    
    try:
        # Update sales_slots
        # PATCH /sales_slots?slot_code=eq.{slot_code}
        headers = {'Accept-Profile': 'master', 'Content-Profile': 'master'}
        res = supabase_request(
            'PATCH', 
            'sales_slots', 
            params={'slot_code': f"eq.{slot_code}"}, 
            json_data=update_data,
            headers_extra=headers
        )
        return {"message": "Slot updated successfully", "data": update_data}
        
    except Exception as e:
        print(f"Error updating slot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{slot_code}/history")
async def get_slot_history(
    slot_code: str,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('master.data.view'))
):
    """
    Get assignment history for a slot.
    """
    from supabase_client import supabase_request
    
    try:
        headers_hr = {'Accept-Profile': 'hr'}
        # Fetch from assignments table, order by start_date desc
        res = supabase_request(
            'GET', 
            'assignments', 
            params={
                'slot_code': f"eq.{slot_code}", 
                'select': '*,employees(full_name)', 
                'order': 'start_date.desc'
            },
            headers_extra=headers_hr
        )
        
        history = res.get('data', [])
        # Flatten employee name if possible, PostgREST returns nested object
        for h in history:
            if h.get('employees'):
                 h['employee_name'] = h['employees'].get('full_name', 'Unknown')
            else:
                 h['employee_name'] = 'Unknown'
                 
        return {"data": history}
        
    except Exception as e:
        print(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
