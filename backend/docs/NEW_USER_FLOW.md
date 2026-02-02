# Flow Ketika Menambah User Baru

## 📋 Overview

Dokumen ini menjelaskan apa yang terjadi ketika Anda menambah user baru ke sistem, termasuk bagaimana caching dan optimasi bekerja.

---

## 🔄 Flow Lengkap: User Baru → Login Pertama

### Step 1: Admin Menambah User Baru

**Via API**: `POST /api/admin/employees/`

```python
# backend/admin_employees.py
@router.post("/", response_model=Employee, status_code=201)
async def create_employee(employee: EmployeeCreate, ...):
    # 1. Create Auth User (jika create_auth_user=True)
    # 2. Insert ke hr.employees
    # 3. Return employee data
```

**Yang Terjadi**:
- ✅ User dibuat di Supabase Auth (jika `create_auth_user=True`)
- ✅ Data employee dimasukkan ke `hr.employees`
- ✅ **TIDAK ada cache** untuk user baru (karena belum pernah login)

---

### Step 2: User Baru Login Pertama Kali

**Flow**:
```
User Login
  ↓
authenticate_user(email, password)
  ↓
verify_token() → resolve_user_slot_context(email)
  ↓
1. Cek Cache → MISS (user baru, belum ada cache)
  ↓
2. Query Database (RPC atau Legacy)
  ↓
3. Cache Hasil (TTL: 15 menit)
  ↓
4. Return User Context
```

**Detail di Code** (`backend/auth.py`):

```python
def resolve_user_slot_context(email: str, use_cache: bool = True):
    # 1. Cek cache dulu
    if use_cache:
        cached = get_cached_user_context(email)
        if cached:
            return cached  # ← User baru: TIDAK ada cache, skip
    
    # 2. Query database (RPC atau legacy)
    # User baru: Akan query database
    rpc_res = supabase_request('POST', 'rpc/get_user_context_by_email', ...)
    
    # 3. Cache hasil untuk 15 menit
    if use_cache and result.get('nik'):
        set_cached_user_context(email, result)  # ← Cache untuk login berikutnya
    
    return result
```

---

## ✅ Yang Terjadi Otomatis

### 1. **Cache Miss → Query Database**

User baru **belum ada di cache**, jadi sistem akan:
- ✅ Query database via RPC function (jika tersedia)
- ✅ Atau fallback ke legacy queries (4-5 queries)
- ✅ Resolve semua data: role, region, scope, dll

### 2. **Cache Otomatis Terisi**

Setelah query berhasil:
- ✅ Hasil di-cache untuk **15 menit**
- ✅ Login berikutnya akan **sangat cepat** (dari cache)

### 3. **RPC Function Handle User Baru**

RPC function `hr.get_user_context_by_email()` akan:
- ✅ Query `hr.employees` untuk cari user
- ✅ JOIN dengan `hr.assignments` (jika ada)
- ✅ JOIN dengan `master.sales_slots` (jika ada assignment)
- ✅ JOIN dengan `master.ref_regions` (jika REGION scope)
- ✅ Return JSON lengkap atau `NULL` jika user tidak ditemukan

---

## ⚠️ Skenario Khusus

### Skenario 1: User Baru Tanpa Assignment

**Kasus**: User baru dibuat, tapi belum ada assignment di `hr.assignments`

**Yang Terjadi**:
```json
// RPC function return:
{
  "name": "John Doe",
  "nik": "12345",
  "slot_code": null,      // ← Tidak ada assignment
  "role": "viewer",       // ← Default role
  "scope": "DEPO",        // ← Default scope
  "region": "ALL"         // ← No specific region
}
```

**Cache**: Tetap di-cache, tapi dengan data minimal

---

### Skenario 2: User Baru dengan Assignment Baru

**Kasus**: User baru dibuat, langsung ada assignment

**Yang Terjadi**:
```json
// RPC function return:
{
  "name": "John Doe",
  "nik": "12345",
  "slot_code": "SLOT001",
  "role": "RBM",
  "scope": "REGION",
  "scope_id": "R06",
  "region_name": "R06 JABODEBEK",
  "grbm_code": "GRBM001"
}
```

**Cache**: Di-cache dengan data lengkap

---

### Skenario 3: Assignment Berubah Setelah User Login

**Kasus**: User sudah login (ada cache), lalu assignment diubah

**Masalah**: Cache masih berisi data lama (15 menit TTL)

**Solusi**: Invalidate cache manual

```bash
# Via API
POST /api/admin/cache/invalidate/{email}

# Atau via code
from user_context_cache import invalidate_user_context
invalidate_user_context("user@example.com")
```

**Best Practice**: Invalidate cache setelah update assignment

---

## 🔧 Rekomendasi: Auto-Invalidate Cache

### Opsi 1: Invalidate Setelah Create/Update Assignment

**File**: `backend/admin_employees.py` atau assignment endpoint

```python
# Setelah create/update assignment
from user_context_cache import invalidate_user_context

# Invalidate cache untuk user tersebut
invalidate_user_context(employee.email)
```

### Opsi 2: Database Trigger (Advanced)

Buat trigger di database untuk auto-invalidate:

```sql
-- Trigger untuk invalidate cache saat assignment berubah
CREATE OR REPLACE FUNCTION hr.invalidate_user_cache_on_assignment_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Call API untuk invalidate cache
    -- (requires HTTP extension atau background job)
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

**Note**: Opsi ini lebih kompleks, perlu HTTP extension atau background job

---

## 📊 Performance Impact

### Login Pertama (User Baru)

| Metric | Value |
|--------|-------|
| **Cache Status** | MISS |
| **Database Queries** | 1 (RPC) atau 4-5 (legacy) |
| **Latency** | 50-100ms (RPC) atau 200-500ms (legacy) |
| **Cache Created** | Yes (15 min TTL) |

### Login Berikutnya (Setelah Cache)

| Metric | Value |
|--------|-------|
| **Cache Status** | HIT |
| **Database Queries** | 0 |
| **Latency** | <1ms (dari cache) |
| **Cache Used** | Yes |

---

## ✅ Checklist: Menambah User Baru

### Untuk Admin:

1. ✅ **Create User** via `POST /api/admin/employees/`
   - Pastikan email unik
   - Set `create_auth_user=True` jika perlu auth account
   - Isi data lengkap (NIK, name, dll)

2. ✅ **Create Assignment** (jika perlu)
   - Assign slot_code ke user
   - Set start_date dan end_date

3. ✅ **User Login Pertama**
   - User login → cache otomatis terisi
   - Tidak perlu action manual

4. ✅ **Jika Assignment Berubah**
   - Invalidate cache: `POST /api/admin/cache/invalidate/{email}`
   - Atau tunggu 15 menit (cache expire otomatis)

---

## 🎯 Kesimpulan

### Yang Terjadi Otomatis:

1. ✅ **User baru login** → Cache miss → Query database → Cache hasil
2. ✅ **Login berikutnya** → Cache hit → Sangat cepat (<1ms)
3. ✅ **Cache expire** (15 menit) → Auto refresh dari database

### Yang Perlu Manual:

1. ⚠️ **Invalidate cache** jika assignment berubah (sebelum 15 menit)
2. ⚠️ **Clear all cache** jika ada perubahan besar (optional)

### Best Practice:

1. ✅ **Auto-invalidate** cache setelah update assignment (recommended)
2. ✅ **Monitor cache stats** via `/api/admin/cache/stats`
3. ✅ **Set TTL sesuai kebutuhan** (default 15 menit sudah optimal)

---

## 📚 Referensi

- Cache implementation: `backend/user_context_cache.py`
- Auth flow: `backend/auth.py`
- Admin endpoints: `backend/admin_employees.py`
- Cache management: `backend/admin_cache.py`
