# 📝 Cara Tambah Secrets di GitHub

## Langkah Detail

### 1. Buka Halaman Secrets

**URL Langsung:**
```
https://github.com/asepkikiabdulaziz-source/dashboard-performance/settings/secrets/actions
```

**Atau via UI:**
1. Buka repository: https://github.com/asepkikiabdulaziz-source/dashboard-performance
2. Klik tab **Settings** (di bagian atas)
3. Di sidebar kiri, klik **Secrets and variables** → **Actions**

### 2. Klik "New repository secret"

Tombol ada di **kanan atas** halaman secrets.

### 3. Isi Form

**Untuk SUPABASE_URL:**
- **Name:** `SUPABASE_URL`
- **Secret:** URL Supabase Anda (contoh: `https://abcdefghijklmnop.supabase.co`)
- Klik **"Add secret"**

**Untuk SUPABASE_KEY:**
- Klik **"New repository secret"** lagi
- **Name:** `SUPABASE_KEY`
- **Secret:** Anon public key dari Supabase (panjang, mulai dengan `eyJ...`)
- Klik **"Add secret"**

### 4. Verifikasi

Setelah ditambahkan, kedua secrets akan muncul di daftar:
- ✅ `SUPABASE_URL`
- ✅ `SUPABASE_KEY`

## Cara Dapatkan Nilai dari Supabase

1. **Buka Supabase Dashboard:**
   - https://supabase.com/dashboard
   - Login jika perlu

2. **Pilih Project Anda**
   - Klik project yang digunakan untuk aplikasi ini

3. **Buka Settings → API:**
   - Di sidebar kiri, klik **Settings** (ikon gear)
   - Klik **API** di submenu

4. **Copy Values:**
   - **Project URL** → Copy untuk `SUPABASE_URL`
     - Format: `https://xxxxx.supabase.co`
   - **anon public** key → Copy untuk `SUPABASE_KEY`
     - Panjang, mulai dengan `eyJ...`
     - ⚠️ JANGAN pakai **service_role** key!

## Checklist

Setelah selesai, pastikan secrets ini ada:
- [ ] `GCP_PROJECT_ID`
- [ ] `GCP_SA_KEY`
- [ ] `SUPABASE_URL` ← **WAJIB untuk login**
- [ ] `SUPABASE_KEY` ← **WAJIB untuk login**
- [ ] `SUPABASE_SERVICE_ROLE_KEY`
- [ ] `BIGQUERY_PROJECT_ID`
- [ ] `BIGQUERY_DATASET`
- [ ] `BIGQUERY_TABLE`
- [ ] `ALLOWED_ORIGINS`
- [ ] `SECRET_KEY`

## Setelah Ditambahkan

1. Tunggu beberapa detik
2. Deployment berikutnya akan otomatis menggunakan secrets baru
3. Atau trigger manual re-deploy jika perlu

---

**Catatan:** Secrets hanya bisa dilihat saat ditambahkan, tidak bisa dilihat lagi setelahnya (untuk keamanan).
