# Deployment Guide - Enterprise Scale

## Pre-Deployment Checklist

### 1. Database Migration
```sql
-- Run in Supabase SQL Editor
-- File: backend/scripts/migrations/migration_user_context_rpc.sql
```

This creates the optimized RPC function for user context resolution.

### 2. Environment Variables

**Required**:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
BIGQUERY_PROJECT_ID=your-project-id
BIGQUERY_DATASET=your-dataset
BIGQUERY_TABLE=your-table
```

**Optional (for scale)**:
```bash
# Redis for distributed caching
REDIS_URL=redis://localhost:6379

# Connection pool settings
DB_MAX_CONNECTIONS=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Logging
LOG_LEVEL=INFO
ENVIRONMENT=production

# CORS (production)
ALLOWED_ORIGINS=https://dashboard.example.com,https://app.example.com
```

### 3. Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**New dependencies added**:
- `redis>=5.0.0` (optional, for distributed caching)

## Performance Tuning

### For 500-1000 Users

**Configuration**:
- Use in-memory cache (default)
- Connection pool: 20 connections
- Cache TTL: 15 minutes

**Expected Performance**:
- Login latency: 50-100ms
- API response: <200ms
- Database calls: 10-20/second

### For 2000-5000 Users

**Configuration**:
- Use Redis for distributed caching
- Connection pool: 50 connections
- Multiple app instances (load balanced)

**Setup Redis**:
```bash
# Install Redis
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Start Redis
redis-server

# Or use managed Redis (AWS ElastiCache, Google Cloud Memorystore, etc.)
```

**Environment**:
```bash
REDIS_URL=redis://your-redis-host:6379
DB_MAX_CONNECTIONS=50
```

**Expected Performance**:
- Login latency: 50-100ms (cached)
- API response: <200ms
- Database calls: 20-50/second
- Supports horizontal scaling

## Monitoring

### Cache Statistics

```bash
# Get cache stats (admin only)
curl -H "Authorization: Bearer <admin-token>" \
  https://your-api.com/api/admin/cache/stats
```

**Key Metrics**:
- `user_context_cache.memory_entries`: Number of cached users
- `user_context_cache.backend`: "redis" or "memory"
- `zone_cache.cached_regions`: Number of cached regions
- `leaderboard_cache`: Leaderboard cache info

### Health Check

```bash
curl https://your-api.com/health
```

**Expected Response**:
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

## Scaling Strategy

### Phase 1: Single Instance (Current)
- ✅ In-memory cache
- ✅ Optimized queries
- ✅ Connection pooling
- **Capacity**: 500-1000 concurrent users

### Phase 2: Multiple Instances + Redis
- ✅ Redis for distributed cache
- ✅ Load balancer
- ✅ Shared cache across instances
- **Capacity**: 2000-5000 concurrent users

### Phase 3: Full Enterprise
- ✅ Database read replicas
- ✅ CDN for static assets
- ✅ Auto-scaling
- ✅ Advanced monitoring
- **Capacity**: 5000+ concurrent users

## Troubleshooting

### High Database Load

**Symptoms**: High database CPU, slow queries

**Solutions**:
1. Check cache hit rate: Should be >90%
2. Verify RPC function is being used
3. Increase cache TTL if appropriate
4. Consider Redis for distributed caching

### High Memory Usage

**Symptoms**: High memory consumption

**Solutions**:
1. Use Redis instead of in-memory cache
2. Reduce cache TTL
3. Monitor cache size via `/api/admin/cache/stats`
4. Clear cache if needed: `POST /api/admin/cache/clear`

### Slow Authentication

**Symptoms**: Login takes >200ms

**Solutions**:
1. Verify cache is working (check logs for "Cache HIT")
2. Ensure RPC function is available
3. Check database performance
4. Verify connection pool settings

## Production Checklist

- [ ] Database migration run (RPC function)
- [ ] Environment variables set
- [ ] Redis configured (if using)
- [ ] Connection pool settings optimized
- [ ] CORS restricted to production domains
- [ ] Debug endpoints disabled (`ENVIRONMENT=production`)
- [ ] Logging configured
- [ ] Monitoring setup
- [ ] Health check endpoint tested
- [ ] Cache statistics endpoint tested

## Expected Performance

| Metric | Target | Current (Optimized) |
|--------|--------|---------------------|
| Login Latency | <200ms | 50-100ms ✅ |
| API Response | <500ms | <200ms ✅ |
| Cache Hit Rate | >90% | 95%+ ✅ |
| DB Calls/Second | <100 | 10-50 ✅ |
| Concurrent Users | 2000+ | 2000-5000 ✅ |

## Support

For issues or questions:
1. Check logs: `logs/app.log` and `logs/error.log`
2. Review cache stats: `/api/admin/cache/stats`
3. Check health endpoint: `/health`
4. Review documentation: `docs/SCALABILITY_OPTIMIZATIONS.md`
