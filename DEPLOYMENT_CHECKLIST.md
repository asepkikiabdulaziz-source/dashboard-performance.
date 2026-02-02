# Deployment Checklist - Push ke Git

## ✅ Perubahan yang Akan Di-Deploy

### 1. Production Configuration ✅
- **File**: `backend/config.py` (NEW)
- **Changes**: Environment-based config, validation, production settings

### 2. Security Middleware ✅
- **File**: `backend/middleware/security.py` (NEW)
- **Changes**: Rate limiting, security headers, error handling

### 3. Updated Main App ✅
- **File**: `backend/main.py`
- **Changes**: 
  - Menggunakan Config class
  - Security middleware enabled
  - Production-ready CORS

### 4. Updated Dockerfile ✅
- **File**: `Dockerfile`
- **Changes**: Gunicorn untuk production, multi-worker

### 5. Updated GitHub Actions ✅
- **File**: `.github/workflows/deploy.yml`
- **Changes**: 
  - Production environment variables
  - Secrets dari Cloud Secret Manager
  - Resource limits & scaling

### 6. Bug Fixes ✅
- **File**: `frontend/src/pages/admin/GenericCompetitionMonitor.jsx`
- **Changes**: Region filter bug fixed

### 7. Optimizations ✅
- **Files**: 
  - `backend/user_context_cache.py` (NEW)
  - `backend/zone_resolution_service.py` (NEW)
  - `backend/connection_pool.py` (NEW)
  - `backend/auth.py` (updated)
- **Changes**: Caching, optimized queries, connection pooling

---

## ⚠️ Breaking Changes

### Tidak Ada Breaking Changes!

Semua perubahan **backward compatible**:
- ✅ Config class dengan defaults untuk development
- ✅ Security middleware bisa di-disable via env var
- ✅ Rate limiting bisa di-disable
- ✅ Fallback ke uvicorn jika gunicorn tidak tersedia

---

## 🔍 Pre-Push Checklist

### 1. Test Locally (Optional tapi Recommended)

```bash
# Test config
cd backend
python -c "from config import Config; missing = Config.validate(); print('Missing:', missing) if missing else print('✅ Config OK')"

# Test imports
python -c "from main import app; print('✅ App imports OK')"
```

### 2. Verify No Syntax Errors

```bash
# Backend
python -m py_compile backend/config.py
python -m py_compile backend/middleware/security.py

# Frontend (if changed)
cd frontend
npm run build
```

### 3. Check Git Status

```bash
git status
# Review semua files yang akan di-commit
```

### 4. Review Changes

```bash
# Review perubahan penting
git diff backend/main.py
git diff .github/workflows/deploy.yml
git diff Dockerfile
```

---

## 🚀 Push Instructions

### Step 1: Stage Changes

```bash
# Add semua perubahan
git add .

# Atau add specific files
git add backend/config.py
git add backend/middleware/
git add backend/main.py
git add .github/workflows/deploy.yml
git add Dockerfile
git add frontend/src/pages/admin/GenericCompetitionMonitor.jsx
```

### Step 2: Commit

```bash
git commit -m "feat: Production deployment configuration

- Add production config management (config.py)
- Add security middleware (rate limiting, headers)
- Update Cloud Run deployment with secrets
- Fix region filter bug in competition monitor
- Add scalability optimizations (caching, RPC)
- Update Dockerfile for production (gunicorn)"
```

### Step 3: Push

```bash
# Push ke main branch (akan trigger deployment)
git push origin main
```

---

## 📊 Deployment Process

Setelah push, GitHub Actions akan:

1. ✅ **Checkout code**
2. ✅ **Authenticate with GCP**
3. ✅ **Build Docker image** (dengan gunicorn)
4. ✅ **Push to Artifact Registry**
5. ✅ **Deploy to Cloud Run** dengan:
   - Production environment
   - Secrets dari Secret Manager
   - Resource limits
   - Auto-scaling

**Waktu**: ~5-10 menit

---

## 🔍 Post-Deployment Verification

### 1. Check GitHub Actions

- Go to: `https://github.com/YOUR_REPO/actions`
- Check latest workflow run
- Verify semua steps berhasil

### 2. Check Cloud Run Service

```bash
# Get service URL
gcloud run services describe dashboard-performance \
  --region asia-southeast2 \
  --format "value(status.url)"
```

### 3. Test Health Endpoint

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

### 4. Test API

```bash
# Test login (jika ada test user)
curl -X POST https://your-service-url.run.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'
```

### 5. Check Logs

```bash
gcloud run services logs read dashboard-performance \
  --region asia-southeast2 \
  --limit 50
```

**Look for**:
- ✅ "Configuration Summary" (dari config.py)
- ✅ "Rate limiting enabled" (jika enabled)
- ✅ "Cache initialized"
- ✅ No errors

---

## ⚠️ Important Notes

### 1. Secrets Must Exist in Cloud Secret Manager

Jika secrets belum dibuat, deployment akan **FAIL**!

**Quick check**:
```bash
gcloud secrets list
```

**Required secrets**:
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `BIGQUERY_PROJECT_ID`
- `BIGQUERY_DATASET`
- `BIGQUERY_TABLE`
- `ALLOWED_ORIGINS`
- `SECRET_KEY`

### 2. Service Account Permissions

Cloud Run service account harus punya access ke secrets:
```bash
# Check current service account
gcloud run services describe dashboard-performance \
  --region asia-southeast2 \
  --format "value(spec.template.spec.serviceAccountName)"
```

### 3. First Deployment

Jika ini pertama kali deploy dengan secrets:
- Deployment mungkin **FAIL** pertama kali
- Fix: Grant secret access, lalu re-deploy
- Atau: Set secrets sebagai env vars dulu (temporary)

---

## 🚨 Rollback Plan

Jika ada masalah setelah deploy:

### Option 1: Revert Git Commit

```bash
# Revert last commit
git revert HEAD
git push origin main
```

### Option 2: Rollback Cloud Run Revision

```bash
# List revisions
gcloud run revisions list \
  --service dashboard-performance \
  --region asia-southeast2

# Rollback to previous revision
gcloud run services update-traffic dashboard-performance \
  --to-revisions PREVIOUS_REVISION=100 \
  --region asia-southeast2
```

---

## ✅ Final Checklist

Sebelum push, pastikan:

- [ ] Semua files sudah di-review
- [ ] Config validation passed (optional test)
- [ ] No syntax errors
- [ ] Git status clean
- [ ] Commit message jelas
- [ ] Secrets sudah ada di Cloud Secret Manager (jika pakai secrets)
- [ ] Service account punya access ke secrets
- [ ] Siap untuk monitor deployment

---

## 🎯 Ready to Push!

Jika semua checklist ✅, langsung push:

```bash
git add .
git commit -m "feat: Production deployment configuration"
git push origin main
```

**Monitor deployment di**:
- GitHub Actions: `https://github.com/YOUR_REPO/actions`
- Cloud Run Console: `https://console.cloud.google.com/run`

---

**Status**: ✅ Ready to Deploy!
