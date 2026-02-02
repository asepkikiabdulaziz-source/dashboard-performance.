# ✅ Supabase Config Sudah SET - Cek Masalah Lain

## Status
- ✅ SUPABASE_URL: SET
- ✅ SUPABASE_KEY: SET  
- ✅ SUPABASE_SERVICE_ROLE_KEY: SET
- ❌ BigQuery config masih MISSING (tidak mempengaruhi login)

## Masalah Login Bisa Jadi:

### 1. User Tidak Ada di Supabase
**Cek:**
1. Buka: https://supabase.com/dashboard
2. Pilih project Anda
3. Authentication → Users
4. Pastikan email yang digunakan untuk login ada di list

**Jika tidak ada:**
- Buat user baru via Supabase Dashboard
- Atau pastikan user sudah dibuat sebelumnya

### 2. Password Salah
- Verifikasi password yang digunakan benar
- Atau reset password via Supabase Dashboard

### 3. Email Belum Dikonfirmasi
**Cek di Supabase:**
- Authentication → Users
- Lihat kolom "Email Confirmed"
- Jika "No", user perlu konfirmasi email dulu

**Solusi:**
- Di Supabase Dashboard, set user sebagai "Auto Confirm"
- Atau kirim confirmation email

### 4. Error dari Supabase Auth
**Cek logs untuk detail error:**
```
https://console.cloud.google.com/run/detail/asia-southeast2/dashboard-performance/logs
```

Cari log dengan:
- "Auth Login Error"
- "Login attempt for email"
- Error message dari Supabase

## Test Login Langsung

Coba test dengan curl untuk melihat error detail:

```bash
curl -X POST https://dashboard-performance-739177218520.asia-southeast2.run.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email@example.com","password":"your-password"}' \
  -v
```

**Flag `-v` akan menampilkan detail request/response**

## Set BigQuery Config (Opsional, untuk aplikasi lengkap)

Tambahkan di GitHub Secrets:
- `BIGQUERY_PROJECT_ID`
- `BIGQUERY_DATASET`
- `BIGQUERY_TABLE`

Atau set langsung:
```bash
gcloud run services update dashboard-performance \
  --region asia-southeast2 \
  --update-env-vars BIGQUERY_PROJECT_ID="myproject-482315" \
  --update-env-vars BIGQUERY_DATASET="pma" \
  --update-env-vars BIGQUERY_TABLE="FINAL_SCORECARD_RANKED"
```

---

**Langkah selanjutnya: Cek apakah user ada di Supabase dan cek logs untuk error detail!**
