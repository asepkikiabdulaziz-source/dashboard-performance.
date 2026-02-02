# Debug: 401 Unauthorized pada Login

## 🔍 Analisis Log

Dari log yang Anda berikan:
- **Status**: 401 Unauthorized
- **Endpoint**: POST `/api/auth/login`
- **Latency**: 4.475s (cukup lama, mungkin ada network issue)
- **Response Size**: 363 bytes (kemungkinan error message)

## ✅ Langkah Debug

### 1. Cek Application Logs (Detail Error)

```bash
# Cek logs aplikasi untuk melihat error detail
gcloud run services logs read dashboard-performance \
  --region asia-southeast2 \
  --limit 100 \
  --format="value(textPayload)"
```

**Cari:**
- `"Auth Login Error"` - Akan menunjukkan status code dan error message dari Supabase
- `"Missing Supabase URL/Key"` - Environment variables tidak ter-set
- `"Login attempt for email"` - Email yang dicoba login

### 2. Verifikasi Environment Variables

```bash
# Cek apakah SUPABASE_URL dan SUPABASE_KEY ter-set
gcloud run services describe dashboard-performance \
  --region asia-southeast2 \
  --format="value(spec.template.spec.containers[0].env)" | grep -E "SUPABASE"
```

**Pastikan:**
- `SUPABASE_URL` ada dan benar (format: `https://xxxxx.supabase.co`)
- `SUPABASE_KEY` ada dan benar (anon key, bukan service role key)

### 3. Test Login Langsung ke Supabase

Test langsung ke Supabase untuk memastikan user dan credentials benar:

```bash
# Set variables (ganti dengan nilai yang benar)
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-anon-key"

# Test login
curl -X POST "$SUPABASE_URL/auth/v1/token?grant_type=password" \
  -H "apikey: $SUPABASE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email@example.com","password":"your-password"}'
```

**Jika berhasil:** Anda akan melihat JSON dengan `access_token`

**Jika error:**
- `400 Bad Request` → Email/password format salah
- `401 Unauthorized` → Email/password salah atau user tidak ada
- `500 Internal Server Error` → Masalah di Supabase

### 4. Verifikasi User di Supabase

Pastikan user sudah dibuat di Supabase Auth:

1. Buka Supabase Dashboard: https://supabase.com/dashboard
2. Pilih project Anda
3. Buka **Authentication** → **Users**
4. Cek apakah email yang digunakan untuk login ada di list

**Jika user tidak ada:**
- Buat user baru via Supabase Dashboard, atau
- Buat user via API (lihat di bawah)

### 5. Test dengan Script Python

Gunakan script test yang sudah dibuat:

```bash
# Set environment variables dulu
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-anon-key"

# Test login
cd backend
python scripts/test_login.py your-email@example.com your-password
```

---

## 🔧 Solusi Berdasarkan Error

### Error: "Invalid login credentials"

**Penyebab:** Email atau password salah

**Solusi:**
1. Verifikasi email dan password benar
2. Cek apakah user sudah dibuat di Supabase Auth
3. Jika lupa password, reset via Supabase Dashboard

### Error: "User not found"

**Penyebab:** User belum dibuat di Supabase Auth

**Solusi:**
1. Buat user via Supabase Dashboard:
   - Authentication → Users → Add User
   - Masukkan email dan password
   - Auto Confirm: ON (untuk testing)

2. Atau buat user via API:
```bash
curl -X POST "$SUPABASE_URL/auth/v1/admin/users" \
  -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "email_confirm": true
  }'
```

### Error: "Missing Supabase URL/Key"

**Penyebab:** Environment variables tidak ter-set di Cloud Run

**Solusi:**
1. Pastikan GitHub Secrets sudah ditambahkan:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`

2. Trigger re-deploy:
```bash
git commit --allow-empty -m "Trigger redeploy to fix env vars"
git push origin main
```

3. Atau update langsung via gcloud:
```bash
gcloud run services update dashboard-performance \
  --region asia-southeast2 \
  --set-env-vars SUPABASE_URL=https://your-project.supabase.co \
  --set-env-vars SUPABASE_KEY=your-anon-key
```

### Error: Timeout atau Connection Error

**Penyebab:** Supabase tidak bisa diakses dari Cloud Run

**Solusi:**
1. Verifikasi `SUPABASE_URL` benar
2. Cek apakah Supabase project masih aktif
3. Test koneksi dari Cloud Run:
```bash
# SSH ke Cloud Run instance (jika memungkinkan)
# Atau test dari local dengan environment variables yang sama
```

---

## 🧪 Test Endpoint Langsung

Test login endpoint langsung dari command line:

```bash
# Dapatkan service URL
SERVICE_URL=$(gcloud run services describe dashboard-performance \
  --region asia-southeast2 \
  --format="value(status.url)")

# Test login
curl -X POST "$SERVICE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email@example.com","password":"your-password"}' \
  -v
```

**Flag `-v` akan menampilkan detail request/response**

---

## 📋 Checklist Debugging

- [ ] Cek application logs untuk error detail
- [ ] Verifikasi `SUPABASE_URL` dan `SUPABASE_KEY` ter-set
- [ ] Test login langsung ke Supabase (bypass backend)
- [ ] Verifikasi user ada di Supabase Auth
- [ ] Test login endpoint dari command line
- [ ] Cek apakah ada network/firewall issue

---

## 🔍 Common Issues

### Issue 1: User Tidak Ada di Supabase

**Gejala:** 401 dengan message "Invalid login credentials"

**Solusi:** Buat user di Supabase Dashboard atau via API

### Issue 2: Wrong Supabase Key

**Gejala:** 401 atau 403 dari Supabase

**Solusi:** Pastikan menggunakan **anon key** (bukan service role key) untuk login endpoint

### Issue 3: Email Not Confirmed

**Gejala:** 401 dengan message tentang email confirmation

**Solusi:** 
- Di Supabase Dashboard, set user sebagai "Auto Confirm"
- Atau kirim confirmation email dan klik link

### Issue 4: Supabase Project Paused/Inactive

**Gejala:** Timeout atau connection error

**Solusi:** Cek Supabase Dashboard, pastikan project masih aktif

---

## 📞 Next Steps

Jika masih tidak bisa:

1. **Cek Logs Detail:**
```bash
gcloud run services logs read dashboard-performance \
  --region asia-southeast2 \
  --limit 200 \
  | grep -i "auth\|login\|supabase"
```

2. **Test Supabase Connection:**
```bash
curl -X GET "$SUPABASE_URL/rest/v1/" \
  -H "apikey: $SUPABASE_KEY"
```

3. **Verifikasi User:**
- Buka Supabase Dashboard
- Cek Authentication → Users
- Pastikan user ada dan status aktif
