# Troubleshooting: Login Tidak Bisa Setelah Deploy

## 🔍 Masalah yang Mungkin Terjadi

Setelah deploy ke Cloud Run, login tidak berfungsi. Berikut adalah langkah-langkah untuk mendiagnosis dan memperbaiki masalah.

---

## ✅ Checklist Diagnostik

### 1. Cek Environment Variables di Cloud Run

Pastikan semua environment variables sudah ter-set dengan benar:

```bash
# Cek environment variables
gcloud run services describe dashboard-performance \
  --region asia-southeast2 \
  --format="value(spec.template.spec.containers[0].env)"
```

**Required Variables:**
- ✅ `SUPABASE_URL` - URL Supabase project Anda
- ✅ `SUPABASE_KEY` - Supabase anon key
- ✅ `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- ✅ `ALLOWED_ORIGINS` - URL frontend (contoh: `https://your-service-url.run.app`)
- ✅ `ENVIRONMENT=production`
- ✅ `BIGQUERY_PROJECT_ID`
- ✅ `BIGQUERY_DATASET`
- ✅ `BIGQUERY_TABLE`

### 2. Cek Logs Cloud Run

```bash
# Cek logs terbaru
gcloud run services logs read dashboard-performance \
  --region asia-southeast2 \
  --limit 50
```

**Cari:**
- ❌ "Missing Supabase URL/Key" → Environment variables tidak ter-set
- ❌ "Auth Login Error" → Masalah dengan Supabase Auth
- ❌ CORS errors → `ALLOWED_ORIGINS` tidak benar

### 3. Test Health Endpoint

```bash
# Dapatkan service URL
SERVICE_URL=$(gcloud run services describe dashboard-performance \
  --region asia-southeast2 \
  --format="value(status.url)")

# Test health endpoint
curl $SERVICE_URL/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "cache": {...},
  "services": {
    "api": "operational",
    "auth": "operational"
  }
}
```

### 4. Test Login Endpoint Langsung

```bash
# Test login endpoint
curl -X POST $SERVICE_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email@example.com","password":"your-password"}'
```

**Jika Error:**
- `401 Unauthorized` → Email/password salah atau user tidak ada di Supabase
- `500 Internal Server Error` → Cek logs untuk detail error
- `CORS error` → `ALLOWED_ORIGINS` tidak mencakup origin yang digunakan

---

## 🔧 Solusi Umum

### Masalah 1: Environment Variables Tidak Ter-Set

**Gejala:**
- Logs menunjukkan "Missing Supabase URL/Key"
- Login endpoint return 500 error

**Solusi:**
1. Pastikan semua GitHub Secrets sudah ditambahkan
2. Re-deploy untuk memastikan env vars ter-set:

```bash
# Trigger re-deploy
git commit --allow-empty -m "Trigger redeploy"
git push origin main
```

### Masalah 2: CORS Error

**Gejala:**
- Browser console menunjukkan CORS error
- Request blocked oleh browser

**Solusi:**
1. Pastikan `ALLOWED_ORIGINS` mencakup URL frontend:

```bash
# Update ALLOWED_ORIGINS
gcloud run services update dashboard-performance \
  --region asia-southeast2 \
  --set-env-vars ALLOWED_ORIGINS=https://your-service-url.run.app
```

**Format:** `ALLOWED_ORIGINS=https://url1.com,https://url2.com` (comma-separated, no spaces)

### Masalah 3: Supabase Auth Error

**Gejala:**
- Logs menunjukkan "Auth Login Error: 400" atau "401"
- Login endpoint return 401

**Solusi:**
1. Verifikasi `SUPABASE_URL` dan `SUPABASE_KEY` benar
2. Pastikan user sudah dibuat di Supabase Auth
3. Test langsung ke Supabase:

```bash
# Test Supabase Auth langsung
curl -X POST "$SUPABASE_URL/auth/v1/token?grant_type=password" \
  -H "apikey: $SUPABASE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

### Masalah 4: Frontend Tidak Bisa Connect ke Backend

**Gejala:**
- Network error di browser console
- Request timeout

**Solusi:**
1. Pastikan frontend dan backend di-deploy di domain yang sama (sudah benar jika menggunakan Dockerfile yang ada)
2. Jika frontend di-deploy terpisah, set `VITE_API_URL`:

```bash
# Di build time, set environment variable
export VITE_API_URL=https://your-backend-url.run.app/api
npm run build
```

---

## 🧪 Testing Steps

### Step 1: Test Backend Health

```bash
SERVICE_URL=$(gcloud run services describe dashboard-performance \
  --region asia-southeast2 \
  --format="value(status.url)")

curl $SERVICE_URL/health
```

### Step 2: Test Login API

```bash
curl -X POST $SERVICE_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

### Step 3: Test dari Browser

1. Buka browser console (F12)
2. Buka Network tab
3. Coba login
4. Cek request ke `/api/auth/login`
5. Lihat response dan error messages

---

## 📝 Debug Commands

### Cek Semua Environment Variables

```bash
gcloud run services describe dashboard-performance \
  --region asia-southeast2 \
  --format="yaml(spec.template.spec.containers[0].env)"
```

### Cek Logs Real-time

```bash
gcloud run services logs tail dashboard-performance \
  --region asia-southeast2
```

### Test Supabase Connection

```bash
# Set variables
export SUPABASE_URL="your-supabase-url"
export SUPABASE_KEY="your-supabase-key"

# Test connection
curl -X GET "$SUPABASE_URL/rest/v1/" \
  -H "apikey: $SUPABASE_KEY"
```

---

## 🚨 Common Errors & Solutions

### Error: "Missing Supabase URL/Key"
**Solution:** Pastikan `SUPABASE_URL` dan `SUPABASE_KEY` ter-set di Cloud Run

### Error: "CORS policy: No 'Access-Control-Allow-Origin' header"
**Solution:** Update `ALLOWED_ORIGINS` dengan URL frontend yang benar

### Error: "401 Unauthorized" dari Supabase
**Solution:** 
- Verifikasi email/password benar
- Pastikan user sudah dibuat di Supabase Auth
- Cek `SUPABASE_KEY` adalah anon key (bukan service role key)

### Error: "500 Internal Server Error"
**Solution:**
- Cek logs untuk detail error
- Pastikan semua required env vars ter-set
- Verifikasi BigQuery credentials (jika digunakan)

---

## ✅ Verification Checklist

Setelah memperbaiki, verifikasi:

- [ ] Health endpoint return `{"status": "healthy"}`
- [ ] Login endpoint bisa diakses (test dengan curl)
- [ ] Browser console tidak ada CORS errors
- [ ] Network tab menunjukkan request berhasil (200 OK)
- [ ] User bisa login dari frontend
- [ ] Token tersimpan di localStorage
- [ ] User bisa akses dashboard setelah login

---

## 📞 Need More Help?

Jika masalah masih terjadi:

1. **Cek Logs:** `gcloud run services logs read dashboard-performance --region asia-southeast2 --limit 100`
2. **Cek Environment Variables:** Pastikan semua ter-set dengan benar
3. **Test Endpoints:** Gunakan curl untuk test langsung tanpa frontend
4. **Browser Console:** Cek error messages di browser console
