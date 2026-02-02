# 📋 Configuration Guide - No Hardcode Policy

## 🎯 Prinsip

**TIDAK ADA HARDCODE** - Semua konfigurasi harus melalui environment variables atau GitHub Secrets/Variables.

## 📍 Lokasi Konfigurasi

### 1. GitHub Repository Settings

#### Secrets (Sensitive Data)
Buka: `https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions`

**Required Secrets:**
- `GCP_PROJECT_ID` - GCP Project ID (contoh: `myproject-482315`)
- `GCP_SA_KEY` - Service Account JSON key untuk deployment
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase anon key
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `BIGQUERY_PROJECT_ID` - BigQuery project ID
- `BIGQUERY_DATASET` - BigQuery dataset name
- `BIGQUERY_TABLE` - BigQuery table name
- `ALLOWED_ORIGINS` - CORS allowed origins (comma-separated)
- `SECRET_KEY` - Application secret key

#### Variables (Non-Sensitive Configuration)
Buka: `https://github.com/YOUR_USERNAME/YOUR_REPO/settings/variables/actions`

**Optional Variables (with defaults):**
- `GCP_SERVICE_NAME` - Cloud Run service name (default: `dashboard-performance`)
- `GCP_REGION` - GCP region (default: `asia-southeast2`)
- `GCP_ARTIFACT_REPOSITORY` - Artifact Registry repository (default: `dashboard-repo`)
- `CLOUD_RUN_MEMORY` - Memory allocation (default: `1Gi`)
- `CLOUD_RUN_CPU` - CPU allocation (default: `1`)
- `CLOUD_RUN_MIN_INSTANCES` - Min instances (default: `0`)
- `CLOUD_RUN_MAX_INSTANCES` - Max instances (default: `10`)
- `CLOUD_RUN_TIMEOUT` - Request timeout in seconds (default: `300`)

### 2. Cloud Run Environment Variables

Set via GitHub Actions workflow atau langsung via gcloud:
```bash
gcloud run services update SERVICE_NAME \
  --region REGION \
  --update-env-vars KEY=value
```

## 🔧 File Konfigurasi

### `backend/config.py`
- Application configuration (Supabase, BigQuery, CORS, etc.)
- **NO HARDCODED VALUES** - semua dari environment variables

### `backend/deployment_config.py`
- Deployment-specific configuration (GCP settings, Cloud Run resources)
- **NO HARDCODED VALUES** - semua dari environment variables

### `.github/workflows/deploy.yml`
- GitHub Actions workflow
- Menggunakan `${{ secrets.* }}` dan `${{ vars.* }}`
- **NO HARDCODED VALUES**

## ✅ Checklist Konfigurasi

### Pre-Deployment

- [ ] `GCP_PROJECT_ID` di-set di GitHub Secrets
- [ ] `GCP_SA_KEY` di-set di GitHub Secrets
- [ ] Semua Supabase secrets di-set
- [ ] Semua BigQuery secrets di-set
- [ ] `ALLOWED_ORIGINS` di-set dengan URL production
- [ ] `SECRET_KEY` di-generate dan di-set

### Optional Configuration

- [ ] `GCP_SERVICE_NAME` di-set (jika berbeda dari default)
- [ ] `GCP_REGION` di-set (jika berbeda dari default)
- [ ] Cloud Run resource limits di-adjust sesuai kebutuhan

## 🚫 Yang TIDAK BOLEH

❌ **JANGAN hardcode:**
- Project IDs
- Service names
- Region names
- Credentials
- URLs
- Resource limits

✅ **HARUS menggunakan:**
- Environment variables
- GitHub Secrets
- GitHub Variables
- Configuration files dengan env var loading

## 📝 Contoh Setup

### 1. Set GitHub Secrets

```bash
# Via GitHub UI atau GitHub CLI
gh secret set GCP_PROJECT_ID --body "myproject-482315"
gh secret set SUPABASE_URL --body "https://xxxxx.supabase.co"
# ... dst
```

### 2. Set GitHub Variables (Optional)

```bash
gh variable set GCP_SERVICE_NAME --body "dashboard-performance"
gh variable set GCP_REGION --body "asia-southeast2"
# ... dst
```

### 3. Verify Configuration

Workflow akan validate configuration sebelum deploy:
- Jika `GCP_PROJECT_ID` tidak di-set, deployment akan fail dengan error jelas

## 🔍 Verifikasi

### Cek GitHub Secrets
```bash
gh secret list
```

### Cek GitHub Variables
```bash
gh variable list
```

### Cek Cloud Run Env Vars
```bash
gcloud run services describe SERVICE_NAME \
  --region REGION \
  --format="yaml(spec.template.spec.containers[0].env)"
```

## 📚 Dokumentasi Terkait

- `backend/config.py` - Application configuration
- `backend/deployment_config.py` - Deployment configuration
- `.github/workflows/deploy.yml` - Deployment workflow

---

**Status:** ✅ No hardcode policy implemented
