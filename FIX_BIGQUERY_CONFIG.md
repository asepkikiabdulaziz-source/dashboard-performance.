# 🔧 Fix: BigQuery Configuration Error

## 🐛 Error yang Terjadi

```
Table "None" must be qualified with a dataset (e.g. dataset.table).
```

**Penyebab:** Environment variables `BIGQUERY_DATASET` atau `BIGQUERY_TABLE` tidak ter-set atau empty.

## ✅ Solusi

### 1. Set Environment Variables di Cloud Run

```bash
gcloud run services update dashboard-performance \
  --region asia-southeast2 \
  --update-env-vars BIGQUERY_PROJECT_ID=myproject-482315 \
  --update-env-vars BIGQUERY_DATASET=pma \
  --update-env-vars BIGQUERY_TABLE=FINAL_SCORECARD_RANKED
```

**Ganti dengan nilai yang benar:**
- `BIGQUERY_PROJECT_ID` - Project ID GCP Anda
- `BIGQUERY_DATASET` - Nama dataset di BigQuery
- `BIGQUERY_TABLE` - Nama table di BigQuery

### 2. Atau Set via GitHub Secrets

1. Buka: https://github.com/asepkikiabdulaziz-source/dashboard-performance/settings/secrets/actions
2. Tambahkan/Update secrets:
   - `BIGQUERY_PROJECT_ID`
   - `BIGQUERY_DATASET`
   - `BIGQUERY_TABLE`
3. Trigger re-deploy

### 3. Default Values (jika tidak di-set)

Aplikasi akan menggunakan default values:
- `BIGQUERY_PROJECT_ID`: `myproject-482315`
- `BIGQUERY_DATASET`: `pma`
- `BIGQUERY_TABLE`: `FINAL_SCORECARD_RANKED`

**Tapi lebih baik set secara eksplisit untuk menghindari error.**

## 🔍 Verifikasi

Setelah update, cek logs:

```bash
gcloud run services logs read dashboard-performance \
  --region asia-southeast2 \
  --limit 50 | grep -i "bigquery"
```

**Expected log:**
```
BigQuery configured: `myproject-482315.pma.FINAL_SCORECARD_RANKED`
```

## 📝 Perbaikan yang Diterapkan

1. **Validasi yang lebih baik** - Akan error dengan message jelas jika config tidak lengkap
2. **Default values** - Menggunakan default jika env vars tidak ter-set
3. **Error handling** - Cache manager tidak akan crash jika BigQuery error
4. **Logging yang lebih informatif** - Menampilkan config yang digunakan

## ⚠️ Catatan

- Pastikan semua 3 env vars ter-set (PROJECT_ID, DATASET, TABLE)
- Jika salah satu empty, akan menggunakan default values
- Jika semua empty, akan error dengan message jelas

---

**Status:** ✅ Fixed - Aplikasi akan menggunakan default values jika env vars tidak ter-set, dan error handling lebih baik
