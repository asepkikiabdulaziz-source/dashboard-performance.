# User Role & Scope Resolution Flow

## Overview

Sistem menentukan role dan scope user melalui **Slot Assignment System**. Setiap user memiliki **active assignment** ke sebuah **slot**, dan slot tersebut menentukan:
- **Role**: super_admin, rbm, bm, head, salesman, dll
- **Scope**: NATIONAL, REGION, BRANCH, DEPO
- **Scope ID**: ID spesifik dari scope tersebut (region_code, branch_id, depo_id)

## Flow Diagram

```
User Login (email + password)
    ↓
1. Authenticate via Supabase Auth
    ↓
2. Get User Metadata (fallback: name, role, region)
    ↓
3. Resolve Slot Context (DYNAMIC - Priority)
    ├── Email → NIK (hr.employees)
    ├── NIK → Active Assignment → slot_code (hr.assignments)
    ├── slot_code → Slot Details (master.sales_slots)
    │   ├── role (super_admin, rbm, bm, head, salesman)
    │   ├── scope (NATIONAL, REGION, BRANCH, DEPO)
    │   └── scope_id (region_code, branch_id, depo_id)
    └── scope_id → Region Name (master.ref_regions)
    ↓
4. Merge Results (Slot Context OVERRIDES User Metadata)
    ↓
5. Return User Context with role, region, scope, permissions
```

## Database Tables Involved

### 1. `hr.employees`
- **Purpose**: Master data karyawan
- **Key Fields**: `nik`, `email`, `full_name`
- **Usage**: Resolve email → NIK

### 2. `hr.assignments`
- **Purpose**: Assignment karyawan ke slot
- **Key Fields**: `nik`, `slot_code`, `start_date`, `end_date`
- **Usage**: Resolve NIK → active slot_code (end_date IS NULL atau end_date > today)

### 3. `master.sales_slots`
- **Purpose**: Master slot/posisi
- **Key Fields**: 
  - `slot_code`: Unique identifier
  - `role`: Role di slot ini (super_admin, rbm, bm, head, salesman)
  - `scope`: Coverage level (NATIONAL, REGION, BRANCH, DEPO)
  - `scope_id`: ID dari scope (region_code, branch_id, depo_id)
  - `depo_id`: Physical location (optional untuk manager level)
- **Usage**: Resolve slot_code → role, scope, scope_id

### 4. `master.ref_regions`
- **Purpose**: Master data region
- **Key Fields**: `region_code`, `name`, `grbm_code`
- **Usage**: Resolve scope_id (region_code) → full region name untuk BigQuery compatibility

## Code Flow

### Function: `resolve_user_slot_context(email: str)`

**Location**: `backend/auth.py`

**Steps**:

1. **Resolve NIK from Email**
   ```python
   emp_res = supabase_request('GET', 'employees', 
       params={'email': f"ilike.{email}", 'select': 'nik,full_name'})
   nik = emp_res['data'][0]['nik']
   ```

2. **Resolve Active Assignment**
   ```python
   assign_res = supabase_request('GET', 'assignments',
       params={
           'nik': f"eq.{nik}",
           'or': f"(end_date.is.null,end_date.gt.{today})",
           'select': 'slot_code'
       })
   slot_code = assign_res['data'][0]['slot_code']
   ```

3. **Resolve Slot Details**
   ```python
   slot_res = supabase_request('GET', 'sales_slots',
       params={'slot_code': f"eq.{slot_code}", 'select': '*'})
   slot = slot_res['data'][0]
   ```

4. **Resolve Region Name** (if scope = REGION)
   ```python
   if slot.get('scope') == 'REGION':
       region_res = supabase_request('GET', 'ref_regions',
           params={'region_code': f"eq.{scope_id}", 'select': 'name,grbm_code'})
       region_name = region_res['data'][0]['name']
   ```

5. **Return Context**
   ```python
   return {
       "name": full_name,
       "nik": nik,
       "slot_code": slot_code,
       "role": slot.get('role', 'viewer'),        # ← DARI SLOT
       "region": region_resolved,                  # ← DARI SLOT SCOPE
       "scope": slot.get('scope'),                # ← DARI SLOT
       "scope_id": slot.get('scope_id'),          # ← DARI SLOT
       ...
   }
   ```

## Examples

### Example 1: User A - Super Admin

**Database State**:
```sql
-- hr.employees
email: 'admin@company.com' → nik: 'ADMIN001'

-- hr.assignments
nik: 'ADMIN001' → slot_code: 'SL-ADMIN-001' (end_date IS NULL)

-- master.sales_slots
slot_code: 'SL-ADMIN-001'
role: 'super_admin'
scope: 'NATIONAL'
scope_id: NULL
```

**Result**:
```json
{
  "email": "admin@company.com",
  "role": "super_admin",
  "region": "ALL",
  "scope": "NATIONAL",
  "scope_id": null
}
```

### Example 2: User B - RBM (Regional Business Manager)

**Database State**:
```sql
-- hr.employees
email: 'rbm.jabodebek@company.com' → nik: 'RBM001'

-- hr.assignments
nik: 'RBM001' → slot_code: 'SL-RBM-JBO-001' (end_date IS NULL)

-- master.sales_slots
slot_code: 'SL-RBM-JBO-001'
role: 'rbm'
scope: 'REGION'
scope_id: 'R06'  -- region_code

-- master.ref_regions
region_code: 'R06' → name: 'R06 JABODEBEK', grbm_code: 'GRBM01'
```

**Result**:
```json
{
  "email": "rbm.jabodebek@company.com",
  "role": "rbm",
  "region": "R06 JABODEBEK",
  "scope": "REGION",
  "scope_id": "R06",
  "zona_rbm": "GRBM01"
}
```

### Example 3: User C - Head Nasional

**Database State**:
```sql
-- hr.employees
email: 'head.nasional@company.com' → nik: 'HEAD001'

-- hr.assignments
nik: 'HEAD001' → slot_code: 'SL-HEAD-NAT-001' (end_date IS NULL)

-- master.sales_slots
slot_code: 'SL-HEAD-NAT-001'
role: 'head'
scope: 'NATIONAL'
scope_id: NULL
```

**Result**:
```json
{
  "email": "head.nasional@company.com",
  "role": "head",
  "region": "ALL",
  "scope": "NATIONAL",
  "scope_id": null
}
```

## Scope Types & Region Mapping

| Scope | scope_id Content | Region Resolution | Example |
|-------|------------------|-------------------|---------|
| **NATIONAL** | `NULL` | `region = "ALL"` | Super Admin, Head Nasional |
| **REGION** | `region_code` (e.g., 'R06') | Resolve ke `ref_regions.name` | RBM, Regional Manager |
| **BRANCH** | `branch_id` | Via branch → region | Branch Manager |
| **DEPO** | `depo_id` | Via depo → branch → region | Salesman |

## Priority Resolution

Sistem menggunakan **2-tier resolution**:

1. **Tier 1: Supabase User Metadata** (Fallback)
   - Dari `user_metadata` di Supabase Auth
   - Static, perlu manual update

2. **Tier 2: Slot Assignment** (Priority - Dynamic)
   - Dari `resolve_user_slot_context()`
   - **OVERRIDES** Tier 1 jika ada
   - Dynamic, otomatis dari database

**Code**:
```python
# In verify_token() and authenticate_user()
res = {
    "name": metadata.get("name", "Unknown User"),      # Tier 1
    "region": metadata.get("region", "UNKNOWN"),       # Tier 1
    "role": metadata.get("role", "viewer")             # Tier 1
}

# DYNAMIC RESOLUTION: Prioritize Slot-based attributes
slot_context = resolve_user_slot_context(email)
if slot_context:
    res.update(slot_context)  # ← Tier 2 OVERRIDES Tier 1
```

## How to Set User Role & Scope

### Method 1: Via Slot Assignment (Recommended)

1. **Create Slot** di `master.sales_slots`:
   ```sql
   INSERT INTO master.sales_slots (slot_code, role, scope, scope_id)
   VALUES ('SL-RBM-JBO-001', 'rbm', 'REGION', 'R06');
   ```

2. **Assign Employee** ke slot di `hr.assignments`:
   ```sql
   INSERT INTO hr.assignments (nik, slot_code, start_date)
   VALUES ('RBM001', 'SL-RBM-JBO-001', CURRENT_DATE);
   ```

3. **User login** → Sistem otomatis resolve role & scope dari slot

### Method 2: Via Supabase User Metadata (Fallback)

1. Update `user_metadata` di Supabase Auth:
   ```json
   {
     "name": "User Name",
     "role": "rbm",
     "region": "R06 JABODEBEK"
   }
   ```

2. **Note**: Method ini hanya digunakan jika slot assignment tidak ditemukan

## Troubleshooting

### User tidak punya role/scope?

**Check**:
1. Apakah user ada di `hr.employees` dengan email yang benar?
2. Apakah ada active assignment di `hr.assignments` (end_date IS NULL)?
3. Apakah slot_code ada di `master.sales_slots`?
4. Apakah slot memiliki `role` dan `scope` yang valid?

### User role tidak sesuai?

**Check**:
1. Cek `master.sales_slots.role` untuk slot_code user
2. Pastikan assignment aktif (end_date IS NULL atau > today)
3. Pastikan tidak ada multiple active assignments untuk user yang sama

### Region tidak ter-resolve?

**Check**:
1. Jika scope = REGION, pastikan `scope_id` ada di `master.ref_regions`
2. Jika scope = BRANCH, pastikan branch → region mapping ada
3. Jika scope = DEPO, pastikan depo → branch → region mapping ada

## Summary

**Sistem tahu user A = super admin, user B = RBM, user C = Head dari:**

1. ✅ **Email** → NIK (hr.employees)
2. ✅ **NIK** → slot_code (hr.assignments - active)
3. ✅ **slot_code** → role, scope, scope_id (master.sales_slots)
4. ✅ **scope_id** → region name (master.ref_regions)

**Semua otomatis dari database, tidak perlu hardcode!**
