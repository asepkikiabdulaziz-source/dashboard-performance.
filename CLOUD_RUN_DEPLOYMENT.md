# Cloud Run Deployment Guide

## 🎯 Overview

Guide untuk deploy aplikasi Dashboard Performance ke Google Cloud Run dengan optimasi production.

---

## ✅ Current Setup

Anda sudah punya:
- ✅ GitHub Actions workflow (`.github/workflows/deploy.yml`)
- ✅ Dockerfile (multi-stage build)
- ✅ Cloud Run deployment (partial)

---

## 🔧 Updates untuk Production

### 1. GitHub Actions Workflow

**File**: `.github/workflows/deploy.yml`

**Updates**:
- ✅ Production environment variables
- ✅ Secrets management via Cloud Secret Manager
- ✅ Resource limits (memory, CPU)
- ✅ Auto-scaling configuration
- ✅ Security settings

### 2. Dockerfile

**File**: `Dockerfile`

**Updates**:
- ✅ Gunicorn untuk production (better performance)
- ✅ Multi-stage build (optimized)
- ✅ Production-ready command

### 3. Cloud Run Configuration

**Environment Variables** (via Secret Manager):
- `ENVIRONMENT=production`
- `LOG_LEVEL=INFO`
- `RATE_LIMIT_ENABLED=true`
- `CACHE_ENABLED=true`

**Secrets** (harus di-set di Cloud Secret Manager):
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `BIGQUERY_PROJECT_ID`
- `BIGQUERY_DATASET`
- `BIGQUERY_TABLE`
- `ALLOWED_ORIGINS`
- `SECRET_KEY`

---

## 🚀 Setup Cloud Secret Manager

### Step 1: Create Secrets

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Create secrets
echo -n "https://your-project.supabase.co" | \
  gcloud secrets create SUPABASE_URL --data-file=-

echo -n "your-anon-key" | \
  gcloud secrets create SUPABASE_KEY --data-file=-

echo -n "your-service-role-key" | \
  gcloud secrets create SUPABASE_SERVICE_ROLE_KEY --data-file=-

echo -n "your-project-id" | \
  gcloud secrets create BIGQUERY_PROJECT_ID --data-file=-

echo -n "your-dataset" | \
  gcloud secrets create BIGQUERY_DATASET --data-file=-

echo -n "your-table" | \
  gcloud secrets create BIGQUERY_TABLE --data-file=-

echo -n "https://dashboard.example.com,https://app.example.com" | \
  gcloud secrets create ALLOWED_ORIGINS --data-file=-

# Generate secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))" | \
  gcloud secrets create SECRET_KEY --data-file=-
```

### Step 2: Grant Access to Cloud Run

```bash
# Get Cloud Run service account
SERVICE_ACCOUNT=$(gcloud run services describe dashboard-performance \
  --region asia-southeast2 \
  --format 'value(spec.template.spec.serviceAccountName)')

# If no service account, use default
if [ -z "$SERVICE_ACCOUNT" ]; then
  SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
fi

# Grant secret accessor role
gcloud secrets add-iam-policy-binding SUPABASE_URL \
  --member "serviceAccount:${SERVICE_ACCOUNT}" \
  --role "roles/secretmanager.secretAccessor"

# Repeat for all secrets
for secret in SUPABASE_KEY SUPABASE_SERVICE_ROLE_KEY BIGQUERY_PROJECT_ID BIGQUERY_DATASET BIGQUERY_TABLE ALLOWED_ORIGINS SECRET_KEY; do
  gcloud secrets add-iam-policy-binding $secret \
    --member "serviceAccount:${SERVICE_ACCOUNT}" \
    --role "roles/secretmanager.secretAccessor"
done
```

---

## 📝 GitHub Secrets

**Required GitHub Secrets** (di repository settings):
- `GCP_PROJECT_ID` - Your GCP project ID
- `GCP_SA_KEY` - Service account JSON key with Cloud Run Admin & Secret Manager access

**Create Service Account**:
```bash
# Create service account
gcloud iam service-accounts create github-actions \
  --display-name "GitHub Actions Deployer"

# Grant permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member "serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role "roles/run.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member "serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role "roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member "serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role "roles/iam.serviceAccountUser"

# Create and download key
gcloud iam service-accounts keys create key.json \
  --iam-account github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Copy key.json content to GitHub Secret: GCP_SA_KEY
```

---

## 🔄 Deployment Flow

### Automatic (via GitHub)

1. **Push to main branch**
   ```bash
   git push origin main
   ```

2. **GitHub Actions triggers**:
   - Builds Docker image
   - Pushes to Artifact Registry
   - Deploys to Cloud Run
   - Sets environment variables & secrets

3. **Cloud Run automatically**:
   - Starts new revision
   - Routes traffic to new revision
   - Scales based on traffic

### Manual Deployment

```bash
# Build and push
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/dashboard-performance

# Deploy
gcloud run deploy dashboard-performance \
  --image gcr.io/YOUR_PROJECT_ID/dashboard-performance \
  --region asia-southeast2 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars ENVIRONMENT=production
```

---

## 🔍 Verify Deployment

### 1. Check Service Status

```bash
gcloud run services describe dashboard-performance \
  --region asia-southeast2 \
  --format "value(status.url)"
```

### 2. Test Health Endpoint

```bash
curl https://your-service-url.run.app/health
```

**Expected**:
```json
{
  "status": "healthy",
  "cache": {...},
  "services": {
    "api": "operational",
    "auth": "operational"
  }
}
```

### 3. Check Logs

```bash
gcloud run services logs read dashboard-performance \
  --region asia-southeast2 \
  --limit 50
```

---

## 🔒 Security Checklist

- [ ] Secrets stored in Cloud Secret Manager (not in code)
- [ ] `ENVIRONMENT=production` set
- [ ] `ALLOWED_ORIGINS` configured for production domains
- [ ] `SECRET_KEY` changed from default
- [ ] Rate limiting enabled
- [ ] Security headers enabled
- [ ] API docs disabled (automatic in production)
- [ ] Debug endpoints disabled (automatic in production)

---

## 📊 Monitoring

### Cloud Run Metrics

**View in Console**:
- Request count
- Latency (p50, p95, p99)
- Error rate
- Instance count
- Memory usage
- CPU usage

**Set up Alerts**:
```bash
# High error rate
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-threshold-value=0.05 \
  --condition-threshold-duration=300s
```

### Application Logs

```bash
# View logs
gcloud run services logs read dashboard-performance \
  --region asia-southeast2

# Follow logs
gcloud run services logs tail dashboard-performance \
  --region asia-southeast2
```

---

## 🚨 Troubleshooting

### Service Won't Start

1. **Check logs**:
   ```bash
   gcloud run services logs read dashboard-performance --region asia-southeast2
   ```

2. **Check secrets**:
   ```bash
   gcloud secrets list
   gcloud secrets versions access latest --secret=SUPABASE_URL
   ```

3. **Test locally**:
   ```bash
   docker build -t test-image .
   docker run -p 8080:8080 --env-file .env test-image
   ```

### High Latency

1. **Increase resources**:
   ```bash
   gcloud run services update dashboard-performance \
     --memory 2Gi \
     --cpu 2 \
     --region asia-southeast2
   ```

2. **Enable min instances** (reduce cold starts):
   ```bash
   gcloud run services update dashboard-performance \
     --min-instances 1 \
     --region asia-southeast2
   ```

### Memory Issues

1. **Increase memory**:
   ```bash
   gcloud run services update dashboard-performance \
     --memory 2Gi \
     --region asia-southeast2
   ```

2. **Enable Redis** (distributed caching):
   - Use Cloud Memorystore or Redis Cloud
   - Set `REDIS_URL` secret

---

## 🔄 Update Workflow

### Add Environment-Specific Deployments

**Update `.github/workflows/deploy.yml`**:

```yaml
on:
  push:
    branches:
      - main      # Production
      - staging   # Staging environment

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      # ... existing steps ...
      
      - name: Deploy to Cloud Run
        run: |
          if [ "${{ github.ref }}" == "refs/heads/main" ]; then
            ENV="production"
            MIN_INSTANCES=1
          else
            ENV="staging"
            MIN_INSTANCES=0
          fi
          
          gcloud run deploy ${{ env.SERVICE_NAME }} \
            --set-env-vars ENVIRONMENT=$ENV \
            --min-instances $MIN_INSTANCES
```

---

## 📈 Performance Optimization

### Current Settings

- **Memory**: 1Gi (sufficient for most cases)
- **CPU**: 1 (can scale to 2-4 for high traffic)
- **Min Instances**: 0 (reduces cost, but has cold starts)
- **Max Instances**: 10 (auto-scales based on traffic)

### Recommended for High Traffic

```bash
gcloud run services update dashboard-performance \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 2 \
  --max-instances 20 \
  --region asia-southeast2
```

---

## ✅ Next Steps

1. **Set up Cloud Secret Manager** (see above)
2. **Update GitHub Secrets** (GCP_PROJECT_ID, GCP_SA_KEY)
3. **Push to main branch** (triggers deployment)
4. **Verify deployment** (check health endpoint)
5. **Monitor performance** (Cloud Run metrics)

---

## 📚 Resources

- **Cloud Run Docs**: https://cloud.google.com/run/docs
- **Secret Manager**: https://cloud.google.com/secret-manager/docs
- **GitHub Actions**: https://docs.github.com/en/actions
- **Production Guide**: `PRODUCTION_DEPLOYMENT_GUIDE.md`

---

**Status**: ✅ Ready untuk update deployment ke production!
