# 🔍 Cek Login Issue - Langkah Debugging

## Step 1: Cek Apakah Secrets Ter-Set di Cloud Run

Buka browser dan akses:
```
https://dashboard-performance-739177218520.asia-southeast2.run.app/api/debug/config-check
```

**Expected Response:**
```json
{
  "status": "ok",
  "config": {
    "SUPABASE_URL": "✅ SET",
    "SUPABASE_KEY": "✅ SET",
    ...
  }
}
```

**Jika ada "❌ MISSING":**
- Secrets belum ter-deploy ke Cloud Run
- Perlu re-deploy setelah set secrets

## Step 2: Cek Logs untuk Error Detail

Buka Cloud Console:
```
https://console.cloud.google.com/run/detail/asia-southeast2/dashboard-performance/logs
```

**Cari:**
- "Missing Supabase URL/Key" → Secrets tidak ter-set
- "Auth Login Error" → Error dari Supabase (cek detail)
- "Login attempt for email" → Request sampai ke backend

## Step 3: Test Login Endpoint Langsung

```bash
curl -X POST https://dashboard-performance-739177218520.asia-southeast2.run.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email@example.com","password":"your-password"}'
```

**Jika error 500:**
- Server configuration error
- Cek apakah SUPABASE_URL dan SUPABASE_KEY ter-set

**Jika error 401:**
- Email/password salah atau user tidak ada
- Cek di Supabase Dashboard → Authentication → Users

## Step 4: Verifikasi User di Supabase

1. Buka: https://supabase.com/dashboard
2. Pilih project Anda
3. Authentication → Users
4. Pastikan email yang digunakan untuk login ada di list
5. Pastikan status user aktif

## Solusi Cepat

### Jika Secrets Belum Ter-Set di Cloud Run:

**Opsi 1: Re-deploy (setelah set secrets di GitHub)**
```bash
git commit --allow-empty -m "Re-deploy with secrets"
git push origin main
```

**Opsi 2: Set Langsung di Cloud Run**
```bash
gcloud run services update dashboard-performance \
  --region asia-southeast2 \
  --update-env-vars SUPABASE_URL="https://your-project.supabase.co" \
  --update-env-vars SUPABASE_KEY="your-anon-key"
```

---

**Cek endpoint `/api/debug/config-check` dulu untuk melihat masalah sebenarnya!**
