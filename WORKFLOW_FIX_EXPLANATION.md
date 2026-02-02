# 🔧 Perbaikan Workflow: Environment Variables Tidak Terhapus

## 🐛 Masalah yang Terjadi

Anda mengatakan semua environment variables sudah di-set di awal (baik di GitHub Secrets maupun gcloud), tapi tiba-tiba dianggap tidak ada.

**Penyebab:** Workflow sebelumnya memiliki step yang **menghapus environment variables** sebelum deploy:

```yaml
- name: Remove old secrets (if service exists)
  run: |
    gcloud run services update ... \
      --clear-secrets \
      --remove-env-vars SUPABASE_URL,SUPABASE_KEY,...
```

Step ini menghapus semua env vars, lalu di step berikutnya di-set ulang. **Masalahnya:**
- Jika GitHub Secrets kosong atau tidak ter-baca, env vars akan ter-set sebagai **empty string**
- Atau jika ada masalah timing, env vars terhapus tapi tidak ter-set ulang

## ✅ Solusi yang Diterapkan

### 1. **Hapus Step "Remove old secrets"**
   - Step yang menghapus env vars sudah dihapus
   - Env vars yang sudah ada tidak akan terhapus lagi

### 2. **Gunakan `--update-env-vars`**
   - Hanya update env vars yang di-specify
   - Preserve env vars yang sudah ada dan tidak di-update
   - Lebih aman daripada `--set-env-vars` yang replace semua

### 3. **Workflow Baru**
   ```yaml
   - name: Deploy to Cloud Run
     run: |
       gcloud run deploy ... \
         --update-env-vars ENVIRONMENT=production,...,SUPABASE_URL=${{ secrets.SUPABASE_URL }},...
   ```

## ⚠️ Catatan Penting

**Jika GitHub Secret kosong:**
- Env var akan di-set ke **empty string** (bukan dihapus)
- Ini akan menyebabkan error seperti "Missing Supabase URL/Key"

**Solusi:**
1. Pastikan semua secrets di-set di GitHub repository settings
2. Atau set env vars secara manual via gcloud (akan tetap ada setelah deploy)

## 🔍 Verifikasi

Setelah deploy berikutnya, cek env vars:

```bash
gcloud run services describe dashboard-performance \
  --region asia-southeast2 \
  --format="yaml(spec.template.spec.containers[0].env)"
```

**Expected:** Semua env vars yang sudah di-set sebelumnya masih ada.

## 📝 Best Practice

1. **Set secrets di GitHub** (recommended untuk automation)
2. **Atau set via gcloud** (akan tetap ada, tidak terhapus oleh workflow)
3. **Jangan set di kedua tempat** (bisa konflik)

## 🚀 Setelah Fix

1. Commit dan push perubahan workflow
2. Deployment berikutnya tidak akan menghapus env vars yang sudah ada
3. Jika ada env vars yang hilang, set ulang via gcloud atau GitHub Secrets

---

**Status:** ✅ Fixed - Env vars tidak akan terhapus lagi oleh workflow
