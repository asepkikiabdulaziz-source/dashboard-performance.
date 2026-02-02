# FAQ: Menambah User Baru

## ❓ Pertanyaan: "Jika nanti saya menambah user baru, apa yang terjadi?"

## ✅ Jawaban Singkat

**Tidak ada yang perlu dilakukan manual!** Sistem akan otomatis:
1. ✅ Query database saat user baru login pertama kali
2. ✅ Cache hasil untuk 15 menit
3. ✅ Login berikutnya sangat cepat (dari cache)

---

## 📋 Flow Detail

### 1. Admin Menambah User Baru

**Via**: `POST /api/admin/employees/`

**Yang Terjadi**:
- ✅ User dibuat di database (`hr.employees`)
- ✅ Auth account dibuat (jika `create_auth_user=True`)
- ✅ **TIDAK ada cache** (karena belum pernah login)

### 2. User Baru Login Pertama Kali

**Flow Otomatis**:
```
User Login
  ↓
Sistem cek cache → MISS (user baru, belum ada)
  ↓
Query database (RPC function atau legacy)
  ↓
Resolve: role, region, scope, dll
  ↓
Cache hasil (15 menit TTL)
  ↓
Return user context
```

**Latency**: 50-100ms (RPC) atau 200-500ms (legacy)

### 3. Login Berikutnya

**Flow Otomatis**:
```
User Login
  ↓
Sistem cek cache → HIT (ada cache)
  ↓
Return dari cache (sangat cepat!)
```

**Latency**: <1ms (dari cache)

---

## 🔄 Skenario Khusus

### Skenario 1: User Baru Tanpa Assignment

**Kasus**: User baru dibuat, tapi belum ada assignment

**Yang Terjadi**:
- ✅ User bisa login
- ✅ Role: `viewer` (default)
- ✅ Scope: `DEPO` (default)
- ✅ Region: `ALL` (no specific region)
- ✅ Cache tetap dibuat (dengan data minimal)

### Skenario 2: User Baru dengan Assignment

**Kasus**: User baru dibuat, langsung ada assignment

**Yang Terjadi**:
- ✅ User bisa login
- ✅ Role, scope, region di-resolve dari assignment
- ✅ Cache dibuat dengan data lengkap

### Skenario 3: Assignment Berubah Setelah User Login

**Kasus**: User sudah login (ada cache), lalu assignment diubah

**Masalah**: Cache masih berisi data lama (15 menit TTL)

**Solusi Otomatis** (sudah diimplementasikan):
- ✅ Cache otomatis di-invalidate saat assignment berubah
- ✅ Login berikutnya akan query database lagi (dapat data terbaru)

**Solusi Manual** (jika perlu):
```bash
POST /api/admin/cache/invalidate/{email}
```

---

## ⚡ Performance

### Login Pertama (User Baru)

| Metric | Value |
|--------|-------|
| Cache Status | MISS |
| Database Queries | 1 (RPC) atau 4-5 (legacy) |
| Latency | 50-100ms (RPC) atau 200-500ms (legacy) |
| Cache Created | ✅ Yes (15 min TTL) |

### Login Berikutnya

| Metric | Value |
|--------|-------|
| Cache Status | HIT |
| Database Queries | 0 |
| Latency | <1ms |
| Cache Used | ✅ Yes |

---

## ✅ Checklist: Menambah User Baru

### Untuk Admin:

1. ✅ **Create User**
   ```
   POST /api/admin/employees/
   {
     "nik": "12345",
     "full_name": "John Doe",
     "email": "john@example.com",
     "create_auth_user": true,
     "password": "secure123"
   }
   ```

2. ✅ **Create Assignment** (jika perlu)
   ```
   POST /api/admin/slots/{slot_code}/assign
   {
     "nik": "12345",
     "reason": "New assignment"
   }
   ```
   **Note**: Cache otomatis di-invalidate saat assignment dibuat/diubah

3. ✅ **User Login**
   - User login → Sistem otomatis resolve & cache
   - Tidak perlu action manual

---

## 🎯 Kesimpulan

### Yang Terjadi Otomatis:

1. ✅ **User baru login** → Cache miss → Query DB → Cache hasil
2. ✅ **Login berikutnya** → Cache hit → Sangat cepat (<1ms)
3. ✅ **Assignment berubah** → Cache auto-invalidate → Query DB lagi
4. ✅ **Cache expire** (15 menit) → Auto refresh dari DB

### Yang Perlu Manual:

1. ⚠️ **Tidak ada!** Semua otomatis
2. ⚠️ **Optional**: Clear all cache jika ada perubahan besar

### Best Practice:

1. ✅ **Tidak perlu invalidate manual** - Sistem sudah handle
2. ✅ **Monitor cache stats** via `/api/admin/cache/stats`
3. ✅ **Set TTL sesuai kebutuhan** (default 15 menit optimal)

---

## 📚 Dokumentasi Lengkap

- **Flow Detail**: `backend/docs/NEW_USER_FLOW.md`
- **Cache System**: `backend/user_context_cache.py`
- **Auth Flow**: `backend/auth.py`
- **Admin Endpoints**: `backend/admin_employees.py`, `backend/admin_slots.py`

---

## 💡 Tips

1. **User baru tanpa assignment?** → Tidak masalah, akan dapat default role/scope
2. **Assignment berubah?** → Cache otomatis di-invalidate
3. **Perlu data terbaru segera?** → Invalidate cache manual atau tunggu 15 menit
4. **Performance concern?** → Cache sudah optimal, tidak perlu khawatir

**Intinya: Semua otomatis, tidak perlu khawatir!** 🚀
