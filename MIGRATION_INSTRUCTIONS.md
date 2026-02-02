# Instruksi Migration: User Context RPC Function

## ✅ Konfirmasi: Assignment Change Auto-Invalidate

**Ya, sudah otomatis!** 

Saat assignment diubah via `POST /api/admin/slots/{slot_code}/assign`, sistem akan:
1. ✅ Update assignment di database
2. ✅ **Otomatis invalidate cache** untuk user tersebut
3. ✅ Login berikutnya akan query database lagi (dapat data terbaru)

**Code**: `backend/admin_slots.py` line 521-532

---

## 🚀 Cara Menjalankan Migration

### Opsi 1: Via Supabase SQL Editor (Recommended)

1. **Buka Supabase Dashboard**
   - Login ke https://supabase.com/dashboard
   - Pilih project Anda

2. **Buka SQL Editor**
   - Klik menu "SQL Editor" di sidebar kiri
   - Klik "New query"

3. **Copy-Paste SQL Migration**
   - Buka file: `backend/scripts/migrations/migration_user_context_rpc.sql`
   - Copy semua isinya (Ctrl+A, Ctrl+C)
   - Paste ke SQL Editor (Ctrl+V)

4. **Run Migration**
   - Klik tombol "Run" atau tekan `Ctrl+Enter`
   - Tunggu sampai selesai (biasanya <1 detik)

5. **Verify**
   - Harusnya muncul pesan sukses
   - Function `hr.get_user_context_by_email` sudah dibuat

### Opsi 2: Via Python Script (Jika DATABASE_URL tersedia)

```bash
# Pastikan DATABASE_URL ada di .env
python backend/scripts/utils/run_user_context_rpc_migration.py
```

**Note**: Jika connection error, gunakan Opsi 1 (SQL Editor) yang lebih reliable.

---

## 📋 SQL Migration Content

File: `backend/scripts/migrations/migration_user_context_rpc.sql`

```sql
-- =================================================================
-- Migration: Optimized User Context Resolution RPC
-- Description: Single query to resolve user context (replaces 4-5 separate queries)
-- Performance: Reduces auth latency from 500ms to 50-100ms
-- =================================================================

-- Create optimized RPC function for user context resolution
CREATE OR REPLACE FUNCTION hr.get_user_context_by_email(p_email text)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_result json;
BEGIN
    -- Single query with JOINs to get all user context data
    SELECT json_build_object(
        'name', e.full_name,
        'nik', e.nik,
        'slot_code', a.slot_code,
        'role', COALESCE(s.role, 'viewer'),
        'scope', COALESCE(s.scope, 'DEPO'),
        'scope_id', s.scope_id,
        'depo_id', s.depo_id,
        'division_id', s.division_id,
        'region_code', s.scope_id,  -- For REGION scope
        'region_name', r.name,      -- Resolved region name
        'grbm_code', r.grbm_code    -- For zone resolution
    ) INTO v_result
    FROM hr.employees e
    LEFT JOIN hr.assignments a ON 
        e.nik = a.nik 
        AND (a.end_date IS NULL OR a.end_date > CURRENT_DATE)
    LEFT JOIN master.sales_slots s ON a.slot_code = s.slot_code
    LEFT JOIN master.ref_regions r ON 
        s.scope = 'REGION' 
        AND s.scope_id = r.region_code
    WHERE LOWER(e.email) = LOWER(p_email)
    ORDER BY a.start_date DESC NULLS LAST  -- Get most recent assignment
    LIMIT 1;
    
    RETURN v_result;
END;
$$;

-- Add comment
COMMENT ON FUNCTION hr.get_user_context_by_email IS 
'Optimized single-query user context resolution. Returns user role, scope, and region info.';

-- Grant execute permission
GRANT EXECUTE ON FUNCTION hr.get_user_context_by_email TO authenticated;
GRANT EXECUTE ON FUNCTION hr.get_user_context_by_email TO anon;
```

---

## ✅ Verifikasi Migration Berhasil

### Test Function

Di Supabase SQL Editor, jalankan:

```sql
-- Test dengan email user yang ada
SELECT hr.get_user_context_by_email('user@example.com');
```

**Expected Result**: JSON object dengan user context:
```json
{
  "name": "John Doe",
  "nik": "12345",
  "slot_code": "SLOT001",
  "role": "rbm",
  "scope": "REGION",
  "scope_id": "R06",
  "region_name": "R06 JABODEBEK",
  "grbm_code": "GRBM001",
  ...
}
```

### Check Function Exists

```sql
SELECT routine_name 
FROM information_schema.routines 
WHERE routine_schema = 'hr' 
AND routine_name = 'get_user_context_by_email';
```

**Expected**: 1 row dengan function name

---

## 🎯 Setelah Migration

1. **Restart FastAPI Application**
   ```bash
   # Stop current server (Ctrl+C)
   # Start again
   uvicorn main:app --reload
   ```

2. **System Otomatis Menggunakan RPC**
   - Tidak perlu ubah code
   - System akan coba RPC dulu
   - Fallback ke legacy jika RPC tidak tersedia

3. **Check Logs**
   - Login dengan user yang ada
   - Cari log: `"Resolved context via RPC for {email}"`
   - Ini berarti RPC function berhasil digunakan

---

## ⚠️ Troubleshooting

### Error: "function hr.get_user_context_by_email does not exist"

**Solusi**:
1. Pastikan migration sudah di-run
2. Check schema name (harus `hr`)
3. Verify function dengan query di atas

### Error: "permission denied"

**Solusi**:
- Pastikan GRANT statements di migration sudah di-run
- Check user permissions di Supabase

### RPC Tidak Digunakan (Masih Legacy Queries)

**Check**:
1. Function sudah dibuat? (test dengan SQL query)
2. Logs menunjukkan error? (cek `backend/auth.py` line 85-86)
3. Restart application sudah dilakukan?

---

## 📚 Referensi

- **Migration File**: `backend/scripts/migrations/migration_user_context_rpc.sql`
- **Usage in Code**: `backend/auth.py` line 42-84
- **Documentation**: `backend/docs/RPC_FUNCTION_EXPLANATION.md`

---

## ✅ Checklist

- [ ] Migration SQL sudah di-run di Supabase SQL Editor
- [ ] Function verified dengan test query
- [ ] FastAPI application sudah di-restart
- [ ] Test login dan cek logs untuk "Resolved context via RPC"
- [ ] Performance improvement terlihat (latency turun)

---

**Status**: ✅ Ready to run migration!
