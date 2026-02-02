# Production Deployment Guide

## 🎯 Overview

Complete guide untuk deploy aplikasi Dashboard Performance ke production environment.

---

## ✅ Pre-Deployment Checklist

### 1. Configuration Validation

**Required Environment Variables**:
```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# BigQuery
BIGQUERY_PROJECT_ID=your-project-id
BIGQUERY_DATASET=your-dataset
BIGQUERY_TABLE=your-table

# Production Settings
ENVIRONMENT=production
ALLOWED_ORIGINS=https://dashboard.example.com,https://app.example.com
SECRET_KEY=your-secure-random-key-here
LOG_LEVEL=INFO
```

**Optional (for scale)**:
```bash
# Redis (for distributed caching)
REDIS_URL=redis://your-redis-host:6379

# Connection pool
DB_MAX_CONNECTIONS=20
DB_POOL_TIMEOUT=30

# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

### 2. Database Migration

**Run RPC Migration**:
```sql
-- In Supabase SQL Editor
-- File: backend/scripts/migrations/migration_user_context_rpc.sql
```

### 3. Security Checklist

- [ ] `SECRET_KEY` diubah dari default
- [ ] `ALLOWED_ORIGINS` di-set untuk production domains
- [ ] `ENVIRONMENT=production` di-set
- [ ] Debug endpoints disabled (otomatis jika `ENVIRONMENT=production`)
- [ ] API docs disabled di production (otomatis)
- [ ] Rate limiting enabled
- [ ] Security headers enabled

---

## 🚀 Deployment Steps

### Step 1: Prepare Environment

**Create `.env` file**:
```bash
cp .env.example .env
# Edit .env dengan production values
```

**Validate configuration**:
```bash
cd backend
python -c "from config import Config; missing = Config.validate(); print('Missing:', missing) if missing else print('✅ All config valid')"
```

### Step 2: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 3: Run Deployment Script

**Linux/macOS**:
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh production
```

**Windows**:
```powershell
.\scripts\deploy.ps1 production
```

### Step 4: Build Frontend

```bash
cd frontend
npm install
npm run build
```

Frontend build akan di-copy ke `backend/dist` atau `frontend/dist`.

### Step 5: Start Application

**Development**:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Production (Recommended)**:
```bash
# Using Gunicorn (recommended for production)
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Using PM2**:
```bash
npm install -g pm2
pm2 start "gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000" --name dashboard-api
pm2 save
pm2 startup
```

**Using systemd** (Linux):
```bash
# Create /etc/systemd/system/dashboard-api.service
# See systemd service file below
sudo systemctl enable dashboard-api
sudo systemctl start dashboard-api
```

---

## 🔒 Security Configuration

### Rate Limiting

Default: **60 requests/minute, 1000 requests/hour** per IP

**Customize**:
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=5000
```

### CORS

**Production**:
```bash
ALLOWED_ORIGINS=https://dashboard.example.com,https://app.example.com
```

**Development** (default):
- `http://localhost:5173`
- `http://localhost:3000`

### Security Headers

Automatically added:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Strict-Transport-Security` (HTTPS only)

---

## 📊 Health Checks

### Basic Health Check

```bash
curl http://localhost:8000/health
```

**Response**:
```json
{
  "status": "healthy",
  "cache": {
    "data_count": 10000,
    "cutoff_date": "2024-01-01",
    "last_refresh": "2024-01-01T12:00:00"
  },
  "services": {
    "api": "operational",
    "auth": "operational"
  }
}
```

### Cache Statistics

```bash
curl -H "Authorization: Bearer <admin-token>" \
  http://localhost:8000/api/admin/cache/stats
```

---

## 🐳 Docker Deployment (Optional)

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Build frontend (if not pre-built)
# COPY ../frontend/dist ./dist

# Expose port
EXPOSE 8000

# Run application
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

---

## 🔄 Deployment Platforms

### Google Cloud Run

```bash
# Build and deploy
gcloud run deploy dashboard-api \
  --source ./backend \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated
```

### AWS Elastic Beanstalk

```bash
# Create .ebextensions/config.yml
# Deploy using EB CLI
eb init
eb create production-env
eb deploy
```

### Heroku

```bash
# Create Procfile
echo "web: gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:\$PORT" > Procfile

# Deploy
git push heroku main
```

---

## 📝 Systemd Service File

**File**: `/etc/systemd/system/dashboard-api.service`

```ini
[Unit]
Description=Dashboard Performance API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/dashboard-performance/backend
Environment="PATH=/opt/dashboard-performance/backend/venv/bin"
EnvironmentFile=/opt/dashboard-performance/backend/.env
ExecStart=/opt/dashboard-performance/backend/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable dashboard-api
sudo systemctl start dashboard-api
sudo systemctl status dashboard-api
```

---

## 🔍 Monitoring & Logging

### Log Files

- **Application logs**: `logs/app.log`
- **Error logs**: `logs/error.log`
- **Log rotation**: 10MB per file, 5 backups

### View Logs

```bash
# Real-time logs
tail -f logs/app.log

# Error logs only
tail -f logs/error.log

# Systemd logs
sudo journalctl -u dashboard-api -f
```

### Performance Monitoring

**Cache Statistics**:
```bash
GET /api/admin/cache/stats
```

**Health Check**:
```bash
GET /health
```

---

## 🚨 Troubleshooting

### Application Won't Start

1. **Check configuration**:
   ```bash
   python -c "from config import Config; print(Config.validate())"
   ```

2. **Check logs**:
   ```bash
   tail -f logs/error.log
   ```

3. **Test import**:
   ```bash
   python -c "from main import app; print('OK')"
   ```

### High Memory Usage

1. **Reduce workers**:
   ```bash
   gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker
   ```

2. **Enable Redis** (distributed caching):
   ```bash
   REDIS_URL=redis://your-redis-host:6379
   ```

### Rate Limiting Issues

1. **Increase limits**:
   ```bash
   RATE_LIMIT_PER_MINUTE=100
   RATE_LIMIT_PER_HOUR=5000
   ```

2. **Disable for specific IPs** (modify middleware)

---

## ✅ Post-Deployment Verification

1. **Health Check**:
   ```bash
   curl http://your-domain.com/health
   ```

2. **API Test**:
   ```bash
   curl -X POST http://your-domain.com/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"test"}'
   ```

3. **Cache Test**:
   ```bash
   curl -H "Authorization: Bearer <token>" \
     http://your-domain.com/api/admin/cache/stats
   ```

4. **Performance Test**:
   - Monitor response times
   - Check cache hit rates
   - Verify rate limiting

---

## 📚 Additional Resources

- **Configuration**: `backend/config.py`
- **Security Middleware**: `backend/middleware/security.py`
- **Deployment Scripts**: `backend/scripts/deploy.sh` / `deploy.ps1`
- **Scalability Guide**: `backend/docs/SCALABILITY_OPTIMIZATIONS.md`

---

## 🎯 Next Steps After Deployment

1. **Set up monitoring** (Sentry, DataDog, etc.)
2. **Configure backups** (database, logs)
3. **Set up alerts** (errors, performance)
4. **Load testing** (verify capacity)
5. **Documentation** (API docs, runbooks)

---

**Status**: ✅ Ready for Production Deployment!
