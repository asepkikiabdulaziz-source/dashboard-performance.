# 🔧 Fix Login - Langkah Cepat

## Masalah
Login gagal karena `SUPABASE_URL` dan `SUPABASE_KEY` tidak ter-set di Cloud Run.

## Solusi: 2 Cara

### Cara 1: Set di GitHub Secrets (RECOMMENDED)

1. Buka: https://github.com/asepkikiabdulaziz-source/dashboard-performance/settings/secrets/actions

2. Pastikan secrets ini ada:
   - ✅ `SUPABASE_URL` - URL Supabase Anda
   - ✅ `SUPABASE_KEY` - Anon key dari Supabase

3. Jika belum ada, tambahkan sekarang.

4. Trigger re-deploy:
```bash
git commit --allow-empty -m "Fix: Re-deploy with Supabase secrets"
git push origin main
```

### Cara 2: Set Langsung di Cloud Run (INSTANT)

Jika punya akses gcloud:

```bash
gcloud run services update dashboard-performance \
  --region asia-southeast2 \
  --update-env-vars SUPABASE_URL="https://your-project.supabase.co" \
  --update-env-vars SUPABASE_KEY="your-anon-key"
```

**Ganti dengan nilai yang benar dari Supabase Dashboard.**

## Cara Dapatkan Supabase Credentials

1. Buka: https://supabase.com/dashboard
2. Pilih project Anda
3. Settings → API
4. Copy:
   - **Project URL** → untuk `SUPABASE_URL`
   - **anon public** key → untuk `SUPABASE_KEY`

## Verifikasi

Setelah update, cek logs:
```bash
gcloud run services logs read dashboard-performance \
  --region asia-southeast2 \
  --limit 20 | grep -i "supabase\|login"
```

**Expected:** Tidak ada error "Missing Supabase URL/Key"

---

**Setelah ini, login seharusnya berfungsi!** ✅
