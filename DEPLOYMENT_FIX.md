# Fix Deployment Error - Secret Manager API

## 🔧 Masalah yang Terjadi

Deployment gagal karena Secret Manager API belum diaktifkan di GCP project Anda.

## ✅ Solusi yang Diterapkan

Workflow sudah diubah untuk menggunakan **GitHub Secrets** langsung sebagai environment variables, sehingga tidak memerlukan Secret Manager API.

## 📝 Setup GitHub Secrets

Anda perlu menambahkan secrets berikut di GitHub Repository Settings:

1. Buka: `https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions`
2. Klik **"New repository secret"**
3. Tambahkan secrets berikut:

### Required Secrets:

- `GCP_PROJECT_ID` - ID project GCP Anda (contoh: `myproject-482315`)
- `GCP_SA_KEY` - Service Account JSON key untuk deployment
- `SUPABASE_URL` - URL Supabase project Anda
- `SUPABASE_KEY` - Supabase anon key
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `BIGQUERY_PROJECT_ID` - BigQuery project ID
- `BIGQUERY_DATASET` - BigQuery dataset name
- `BIGQUERY_TABLE` - BigQuery table name
- `ALLOWED_ORIGINS` - Allowed CORS origins (contoh: `https://yourdomain.com,https://app.yourdomain.com`)
- `SECRET_KEY` - Secret key untuk aplikasi (generate dengan: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)

## 🚀 Deploy Ulang

Setelah semua secrets ditambahkan, push ulang ke branch `main`:

```bash
git add .github/workflows/deploy.yml
git commit -m "Fix: Use GitHub Secrets instead of Secret Manager"
git push origin main
```

## 🔄 Opsi: Mengaktifkan Secret Manager API (Opsional)

Jika Anda ingin menggunakan Secret Manager di masa depan (lebih aman untuk production):

### Step 1: Enable Secret Manager API

1. Buka: https://console.developers.google.com/apis/api/secretmanager.googleapis.com/overview?project=739177218520
2. Klik **"Enable"**
3. Tunggu beberapa menit hingga API aktif

### Step 2: Create Secrets di Secret Manager

```bash
# Set project
gcloud config set project 739177218520

# Create secrets
echo -n "YOUR_SUPABASE_URL" | \
  gcloud secrets create SUPABASE_URL --data-file=-

echo -n "YOUR_SUPABASE_KEY" | \
  gcloud secrets create SUPABASE_KEY --data-file=-

echo -n "YOUR_SERVICE_ROLE_KEY" | \
  gcloud secrets create SUPABASE_SERVICE_ROLE_KEY --data-file=-

echo -n "YOUR_BIGQUERY_PROJECT_ID" | \
  gcloud secrets create BIGQUERY_PROJECT_ID --data-file=-

echo -n "YOUR_BIGQUERY_DATASET" | \
  gcloud secrets create BIGQUERY_DATASET --data-file=-

echo -n "YOUR_BIGQUERY_TABLE" | \
  gcloud secrets create BIGQUERY_TABLE --data-file=-

echo -n "YOUR_ALLOWED_ORIGINS" | \
  gcloud secrets create ALLOWED_ORIGINS --data-file=-

# Generate secret key
python -c "import secrets; print(secrets.token_urlsafe(32))" | \
  gcloud secrets create SECRET_KEY --data-file=-
```

### Step 3: Grant Access ke Cloud Run Service Account

```bash
# Get project number
PROJECT_NUMBER=$(gcloud projects describe 739177218520 --format="value(projectNumber)")

# Grant access
gcloud secrets add-iam-policy-binding SUPABASE_URL \
  --member "serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role "roles/secretmanager.secretAccessor"

# Repeat for all secrets
for secret in SUPABASE_KEY SUPABASE_SERVICE_ROLE_KEY BIGQUERY_PROJECT_ID BIGQUERY_DATASET BIGQUERY_TABLE ALLOWED_ORIGINS SECRET_KEY; do
  gcloud secrets add-iam-policy-binding $secret \
    --member "serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role "roles/secretmanager.secretAccessor"
done
```

### Step 4: Update Workflow (jika ingin kembali ke Secret Manager)

Ubah kembali `.github/workflows/deploy.yml` untuk menggunakan `--set-secrets` seperti sebelumnya.

## ✅ Verifikasi

Setelah deploy berhasil, cek status:

```bash
gcloud run services describe dashboard-performance \
  --region asia-southeast2 \
  --format "value(status.url)"
```

Test health endpoint:
```bash
curl https://YOUR-SERVICE-URL.run.app/health
```
