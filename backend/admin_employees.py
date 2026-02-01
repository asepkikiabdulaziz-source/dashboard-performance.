from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Optional
from models import Employee, EmployeeCreate, EmployeeUpdate
from supabase_client import supabase_request, supabase_auth_admin_request
from auth import get_current_user
from rbac import require_permission

# Schema Headers
HEADERS_HR = {'Accept-Profile': 'hr', 'Content-Profile': 'hr'}
HEADERS_MASTER = {'Accept-Profile': 'master'}


router = APIRouter(prefix="/api/admin/employees", tags=["admin-employees"])

@router.get("/", response_model=dict)
async def get_employees(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    role: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('auth.user.manage'))
):
    try:
        # --- Build Query Params ---
        start = (page - 1) * page_size
        end = start + page_size - 1
        
        params = {
            'select': '*',
            'limit': page_size,
            'offset': start,
            'order': 'created_at.desc'
        }
        
        # Apply Filters
        if search:
            params['or'] = f"(full_name.ilike.*{search}*,nik.ilike.*{search}*)"
        
        if role and role != 'all':
            params['role_id'] = f"eq.{role}"

        # Execute
        res = supabase_request(
            'GET', 
            'employees', 
            params=params, 
            headers_extra={'Range': f'{start}-{end}', **HEADERS_HR}
        )
        
        employees = res.get('data', [])
        total = res.get('count', 0)
        
        # Fetch Roles for Mapping
        if employees:
            roles_res = supabase_request(
                'GET', 
                'ref_role', 
                params={'select': 'role_id,role_name'}, 
                headers_extra=HEADERS_MASTER
            )
            roles_map = {r['role_id']: r['role_name'] for r in roles_res.get('data', [])}
            
            for item in employees:
                item['role_name'] = roles_map.get(item['role_id'])
        
        return {
            "data": employees,
            "total": total,
            "page": page,
            "pageSize": page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/roles")
async def get_roles(current_user: dict = Depends(get_current_user)):
    res = supabase_request('GET', 'ref_role', headers_extra=HEADERS_MASTER)
    return res.get('data', [])

@router.post("/", response_model=Employee, status_code=201)
async def create_employee(
    employee: EmployeeCreate,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('auth.user.manage'))
):

    # 1. Check if NIK already exists (in schema hr)
    existing = supabase_request('GET', 'employees', params={'nik': f"eq.{employee.nik}", 'select': 'nik'}, headers_extra=HEADERS_HR)
    if existing.get('data'):
        raise HTTPException(status_code=400, detail=f"Employee with NIK '{employee.nik}' already exists")

    # 2. Check if Email already exists (in schema hr)
    if employee.email:
        existing_email = supabase_request('GET', 'employees', params={'email': f"eq.{employee.email}", 'select': 'email'}, headers_extra=HEADERS_HR)
        if existing_email.get('data'):
            raise HTTPException(status_code=400, detail=f"Email '{employee.email}' is already in use")

    auth_user_id = None
    
    # 3. Create Auth User if requested
    if employee.create_auth_user:
        if not employee.email:
             raise HTTPException(status_code=400, detail="Email is required to create a system user")
        
        try:
            # Create user in Supabase Auth via HTTP
            auth_payload = {
                "email": employee.email,
                "password": employee.password,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": employee.full_name,
                    "role": employee.role_id,
                    "nik": employee.nik
                }
            }
            auth_res = supabase_auth_admin_request('POST', 'users', json_data=auth_payload)
            auth_user_id = auth_res.get('id')
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create Auth User: {str(e)}")

    # 4. Insert into hr.employees
    employee_data = employee.dict(exclude={'create_auth_user', 'password'})
    if auth_user_id:
        employee_data['auth_user_id'] = auth_user_id
        
    try:
        # Prefer representation to get data back
        headers = {**HEADERS_HR, 'Prefer': 'return=representation'}
        res = supabase_request('POST', 'employees', json_data=employee_data, headers_extra=headers)
        
        if not res.get('data'):
             raise HTTPException(status_code=500, detail="Failed to insert employee record")
        
        new_employee = res.get('data', [])[0]
        # Fetch role name
        role_res = supabase_request('GET', 'ref_role', params={'role_id': f"eq.{new_employee['role_id']}", 'select': 'role_name'}, headers_extra=HEADERS_MASTER)
        new_employee['role_name'] = role_res.get('data', [{}])[0].get('role_name')
        
        return new_employee

    except Exception as e:
        # Rollback Auth User if DB insert fails
        if auth_user_id:
            try:
                supabase_auth_admin_request('DELETE', f'users/{auth_user_id}')
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{nik}", response_model=Employee)
async def update_employee(
    nik: str,
    employee_update: EmployeeUpdate,
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('auth.user.manage'))
):
    """
    Update employee details
    """
    _ = Depends(require_permission('auth.user.manage'))
         
    
    # Check if exists
    existing = supabase_request('GET', 'employees', params={'nik': f"eq.{nik}"}, headers_extra=HEADERS_HR)
    if not existing.get('data'):
        raise HTTPException(status_code=404, detail="Employee not found")
    existing_emp = existing.get('data', [])[0]
        
    # Handle Grant System Access
    auth_user_id = None
    if employee_update.create_auth_user:
        if existing_emp.get('auth_user_id'):
            # Already has access, ignore
            pass
        elif not employee_update.password:
             raise HTTPException(status_code=400, detail="Password is required to grant system access")
        else:
            # Check email availability
            email_to_use = employee_update.email or existing_emp.get('email')
            if not email_to_use:
                 raise HTTPException(status_code=400, detail="Employee must have an email to be granted access")

            # Create User via HTTP
            try:
                auth_payload = {
                    "email": email_to_use,
                    "password": employee_update.password,
                    "email_confirm": True,
                    "user_metadata": {
                        "full_name": existing_emp.get('full_name'),
                        "role": existing_emp.get('role_id'),
                        "nik": nik
                    }
                }
                auth_res = supabase_auth_admin_request('POST', 'users', json_data=auth_payload)
                auth_user_id = auth_res.get('id')
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to create Auth User: {str(e)}")

    # Prepare database update
    update_data = employee_update.dict(exclude_unset=True, exclude={'create_auth_user', 'password'})
    if auth_user_id:
        update_data['auth_user_id'] = auth_user_id
        
    if not update_data and not auth_user_id:
        return existing_emp

    try:
        # Sync Role to Supabase Auth if role_id changed and user has access
        current_auth_id = existing_emp.get('auth_user_id') or auth_user_id
        new_role = update_data.get('role_id')
        
        if current_auth_id and new_role and new_role != existing_emp.get('role_id'):
            # Fetch current metadata to avoid overwriting other fields? 
            # Actually Supabase Auth update usually merges top-level keys in user_metadata if we send it as such?
            # Safe bet: just send role and full_name (if updated)
            meta_update = {"role": new_role}
            if 'full_name' in update_data:
                meta_update['full_name'] = update_data['full_name']
                
            # Update user via HTTP
            supabase_auth_admin_request('PUT', f'users/{current_auth_id}', json_data={"user_metadata": meta_update})

        # Execute Update
        headers = {**HEADERS_HR, 'Prefer': 'return=representation'}
        res = supabase_request('PATCH', 'employees', params={'nik': f"eq.{nik}"}, json_data=update_data, headers_extra=headers)
        updated_emp = res.get('data', [])[0]
        
        return updated_emp
    except Exception as e:
        # Rollback auth if failed
        if auth_user_id:
            try:
                supabase_auth_admin_request('DELETE', f'users/{auth_user_id}')
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# BULK EXPORT & IMPORT
# ==========================================
from fastapi import UploadFile, File
from fastapi.responses import StreamingResponse
import pandas as pd
from io import BytesIO
from models import CSVUploadResponse

@router.get("/export")
async def export_employees(current_user: dict = Depends(get_current_user)):
    """Export all employees to CSV/Excel"""
    res = supabase_request('GET', 'employees', headers_extra=HEADERS_HR)
    employees = res.get('data', [])
    
    if not employees:
         df = pd.DataFrame(columns=['nik', 'full_name', 'role_id', 'role_name', 'email', 'phone_number', 'is_active'])
    else:
        roles_res = supabase_request('GET', 'ref_role', params={'select': 'role_id,role_name'}, headers_extra=HEADERS_MASTER)
        roles_map = {r['role_id']: r['role_name'] for r in roles_res.get('data', [])}
        
        data_list = []
        for item in employees:
            data_list.append({
                'nik': item.get('nik'),
                'full_name': item.get('full_name'),
                'role_id': item.get('role_id'),
                'role_name': roles_map.get(item.get('role_id'), 'Unknown'),
                'email': item.get('email'),
                'phone_number': item.get('phone_number'),
                'is_active': 'Active' if item.get('is_active') else 'Inactive',
                'system_access': 'Yes' if item.get('auth_user_id') else 'No'
            })
        df = pd.DataFrame(data_list)

    # Convert to CSV
    stream = BytesIO()
    df.to_csv(stream, index=False)
    stream.seek(0)
    
    return StreamingResponse(
        stream, 
        media_type="text/csv", 
        headers={"Content-Disposition": "attachment; filename=employees_export.csv"}
    )

@router.post("/upload", response_model=CSVUploadResponse)
async def upload_employees(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    _: bool = Depends(require_permission('auth.user.manage'))
):
    """
    Bulk upload employees from CSV/Excel.
    Strict Validation:
    1. Check if NIK exists in DB -> Fail row
    2. Check if Role ID exists -> Fail row
    """
    _ = Depends(require_permission('auth.user.manage'))

    # Read File
    try:
        contents = await file.read()
        if file.filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(contents))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(BytesIO(contents))
        else:
             raise HTTPException(status_code=400, detail="Invalid file format. Please upload CSV or Excel.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

    # Normalize Headers
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    required_cols = ['nik', 'full_name', 'role_id']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {missing}")
    
    # Pre-fetch existing NIKs for validation
    res_nik = supabase_request('GET', 'employees', params={'select': 'nik'}, headers_extra=HEADERS_HR)
    existing_niks = {item['nik'] for item in res_nik.get('data', [])}
    
    # Pre-fetch valid roles
    res_roles = supabase_request('GET', 'ref_role', params={'select': 'role_id'}, headers_extra=HEADERS_MASTER)
    valid_roles = {item['role_id'] for item in res_roles.get('data', [])}

    valid_rows = []
    errors = []
    
    # Iterate rows
    # Using df.intertuples() or to_dict('records')
    records = df.to_dict('records')
    
    for idx, row in enumerate(records):
        row_num = idx + 2 # Header is row 1
        
        nik = str(row.get('nik', '')).strip()
        name = str(row.get('full_name', '')).strip()
        role = str(row.get('role_id', '')).strip()
        email = str(row.get('email', '')).strip() if pd.notna(row.get('email')) else None
        
        current_error = None
        
        # Validation Logic
        if not nik:
            current_error = "Missing NIK"
        elif nik in existing_niks:
            current_error = f"NIK '{nik}' already exists"
        elif nik in [r['nik'] for r in valid_rows]: # Check duplicate in file itself
            current_error = f"Duplicate NIK '{nik}' in file"
            
        elif not name or len(name) < 2:
            current_error = "Name too short (min 2 chars)"
        
        elif role not in valid_roles:
            current_error = f"Invalid Role ID '{role}'"
            
        # If Error
        if current_error:
            errors.append({
                "row_number": row_num,
                "row_data": {
                    "nik": nik,
                    "full_name": name,
                    "role_id": role,
                    "email": email
                },
                "error_message": current_error
            })
            continue
            
        # If Valid
        valid_rows.append({
            "nik": nik,
            "full_name": name,
            "role_id": role,
            "email": email,
            "phone_number": str(row.get('phone_number', '')) if pd.notna(row.get('phone_number')) else None,
            "is_active": True
        })

    # Bulk Insert
    if valid_rows:
        try:
            # Upsert is safer but user requested strict check.
            # Since we validated NIK uniqueness, Insert is fine.
            # Process in chunks of 500 to be safe
            chunk_size = 500
            for i in range(0, len(valid_rows), chunk_size):
                chunk = valid_rows[i:i + chunk_size]
                supabase_request('POST', 'employees', json_data=chunk, headers_extra=HEADERS_HR)
        except Exception as e:
            # Global Insert Error (rare if validated)
            raise HTTPException(status_code=500, detail=f"Database Insert Failed: {str(e)}")

    return CSVUploadResponse(
        total_rows=len(records),
        valid_rows=len(valid_rows),
        invalid_rows=len(errors),
        errors=errors,
        preview=valid_rows[:5]
    )
