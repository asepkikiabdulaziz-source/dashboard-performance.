# Fix: Login Tidak Bisa Setelah Deploy

## 🔍 Langkah Cepat untuk Debug

### 1. Cek Service URL dan Test Health

```bash
# Dapatkan service URL
gcloud run services describe dashboard-performance \
  --region asia-southeast2 \
  --format="value(status.url)"
```

Salin URL tersebut, lalu test:

```bash
# Ganti YOUR_SERVICE_URL dengan URL dari command di atas
curl https://YOUR_SERVICE_URL.run.app/health
```

**Jika berhasil:** Anda akan melihat JSON dengan `"status": "healthy"`

### 2. Cek Environment Variables

```bash
gcloud run services describe dashboard-performance \
  --region asia-southeast2 \
  --format="yaml(spec.template.spec.containers[0].env)"
```

**Pastikan ada:**
- `SUPABASE_URL` (harus ada nilai)
- `SUPABASE_KEY` (harus ada nilai)
- `ALLOWED_ORIGINS` (harus ada nilai, contoh: `https://your-service-url.run.app`)

### 3. Cek Logs untuk Error

```bash
gcloud run services logs read dashboard-performance \
  --region asia-southeast2 \
  --limit 50
```

**Cari error messages:**
- "Missing Supabase URL/Key" → Environment variables tidak ter-set
- "Auth Login Error" → Masalah dengan Supabase Auth
- CORS errors → `ALLOWED_ORIGINS` tidak benar

---

## 🔧 Perbaikan Cepat

### Fix 1: Update ALLOWED_ORIGINS

Jika Anda melihat CORS error, update `ALLOWED_ORIGINS`:

```bash
# Ganti YOUR_SERVICE_URL dengan URL service Anda
gcloud run services update dashboard-performance \
  --region asia-southeast2 \
  --set-env-vars ALLOWED_ORIGINS=https://YOUR_SERVICE_URL.run.app
```

### Fix 2: Verifikasi GitHub Secrets

Pastikan semua secrets sudah ditambahkan di GitHub:
1. Buka: `https://github.com/asepkikiabdulaziz-source/dashboard-performance/settings/secrets/actions`
2. Pastikan ada:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `ALLOWED_ORIGINS`
   - `BIGQUERY_PROJECT_ID`
   - `BIGQUERY_DATASET`
   - `BIGQUERY_TABLE`
   - `SECRET_KEY`

### Fix 3: Re-deploy dengan Environment Variables

Jika env vars tidak ter-set, trigger re-deploy:

```bash
git commit --allow-empty -m "Trigger redeploy to fix env vars"
git push origin main
```

---

## 🧪 Test Login Endpoint

Test langsung ke API untuk memastikan backend bekerja:

```bash
# Ganti YOUR_SERVICE_URL dan credentials
curl -X POST https://YOUR_SERVICE_URL.run.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email@example.com","password":"your-password"}'
```

**Jika berhasil:** Anda akan melihat JSON dengan `access_token`

**Jika error:**
- `401` → Email/password salah atau user tidak ada
- `500` → Cek logs untuk detail error
- `CORS error` → Update `ALLOWED_ORIGINS`

---

## 📋 Checklist Verifikasi

Setelah memperbaiki, pastikan:

- [ ] Health endpoint return `{"status": "healthy"}`
- [ ] Environment variables ter-set dengan benar
- [ ] `ALLOWED_ORIGINS` mencakup URL frontend
- [ ] Login endpoint bisa diakses (test dengan curl)
- [ ] Browser console tidak ada CORS errors
- [ ] User bisa login dari frontend

---

## 📖 Dokumentasi Lengkap

Lihat `TROUBLESHOOTING_LOGIN.md` untuk panduan lengkap troubleshooting.
