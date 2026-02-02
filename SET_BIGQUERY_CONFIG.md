# 🔧 Set BigQuery Config - Fix Error 500

## Masalah
Error 500 pada `/api/dashboard/kpis` karena BigQuery config MISSING.

## Solusi Cepat

### Opsi 1: Set di GitHub Secrets (RECOMMENDED)

1. Buka: https://github.com/asepkikiabdulaziz-source/dashboard-performance/settings/secrets/actions

2. Tambahkan secrets:
   - **Name:** `BIGQUERY_PROJECT_ID`
     - **Value:** `myproject-482315` (atau project ID Anda)
   
   - **Name:** `BIGQUERY_DATASET`
     - **Value:** `pma` (atau dataset name Anda)
   
   - **Name:** `BIGQUERY_TABLE`
     - **Value:** `FINAL_SCORECARD_RANKED` (atau table name Anda)

3. Trigger re-deploy:
```bash
git commit --allow-empty -m "Re-deploy with BigQuery config"
git push origin main
```

### Opsi 2: Set Langsung di Cloud Run

```bash
gcloud run services update dashboard-performance \
  --region asia-southeast2 \
  --update-env-vars BIGQUERY_PROJECT_ID="myproject-482315" \
  --update-env-vars BIGQUERY_DATASET="pma" \
  --update-env-vars BIGQUERY_TABLE="FINAL_SCORECARD_RANKED"
```

## Verifikasi

Setelah set, cek lagi:
```
https://dashboard-performance-739177218520.asia-southeast2.run.app/api/debug/config-check
```

**Expected:**
```json
{
  "BIGQUERY_PROJECT_ID": "✅ SET",
  "BIGQUERY_DATASET": "✅ SET",
  "BIGQUERY_TABLE": "✅ SET"
}
```

## Setelah Fix

- Error 500 pada `/api/dashboard/kpis` akan hilang
- Dashboard akan bisa load data dari BigQuery
- Aplikasi akan berfungsi penuh

---

**Catatan:** Aplikasi sekarang sudah handle missing BigQuery config dengan lebih baik (return empty data instead of crash), tapi lebih baik set config untuk fungsi penuh.
