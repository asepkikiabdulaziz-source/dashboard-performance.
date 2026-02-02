# 🗺️ Roadmap: Real Dashboard Implementation
## BigQuery + Supabase + RLS + Redis Cache

**Status**: Planning Phase  
**Last Updated**: 2026-02-02  
**Target Completion**: TBD

---

## 📋 Overview

Implementasi dashboard real dengan arsitektur:
- **Raw Transactions**: BigQuery (`pma.all_prc`)
- **Master Data**: Supabase (source) + BigQuery (copy untuk JOIN)
- **Aggregations**: BigQuery Materialized Views
- **RLS Layer**: Supabase Dashboard Tables dengan Row-Level Security
- **Cache Layer**: Redis (multi-level caching)
- **Update Strategy**: Manual trigger only (no automation)

---

## 🎯 Goals

1. ✅ Dashboard real dengan data transaksi dari BigQuery
2. ✅ Complex RLS berdasarkan role, region, scope, zone
3. ✅ Optimal caching untuk performance
4. ✅ Manual refresh (admin upload → trigger refresh)
5. ✅ Scalable architecture untuk future growth

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  DATA FLOW                                              │
└─────────────────────────────────────────────────────────┘

1. RAW DATA:
   BigQuery (pma.all_prc - Raw Transactions)
   │
   │ Admin Upload (Manual)
   ▼
2. MATERIALIZED VIEWS:
   BigQuery Materialized Views
   ├── dashboard_sales_enriched_mv
   ├── dashboard_kpis_mv
   └── dashboard_leaderboard_mv
   │
   │ Manual Trigger (API)
   ▼
3. RLS LAYER:
   Supabase Dashboard Tables
   ├── dashboard.sales_summary (with RLS)
   ├── dashboard.kpis (with RLS)
   ├── dashboard.leaderboard (with RLS)
   └── dashboard.competition_ranks (with RLS)
   │
   │ Application Query (with user context)
   ▼
4. CACHE LAYER:
   Redis (Multi-level)
   ├── L1: Filtered by user context (TTL: 24h)
   ├── L2: Unfiltered (filter on-demand)
   └── Cache invalidation on manual refresh
   │
   │ API Query
   ▼
5. DASHBOARD:
   FastAPI → Frontend
```

---

## 🚀 Implementation Phases

### Phase 1: BigQuery Materialized Views ✅
**Status**: Planning  
**Estimated Time**: 2-3 days

#### Tasks:
- [ ] Create BigQuery Materialized Views
  - [ ] `dashboard_sales_enriched_mv` (sales + product + employee JOIN)
  - [ ] `dashboard_kpis_mv` (aggregated KPIs by region/date)
  - [ ] `dashboard_leaderboard_mv` (from FINAL_SCORECARD_RANKED)
- [ ] Create migration script: `create_dashboard_materialized_views.sql`
- [ ] Test materialized views dengan sample queries
- [ ] Document materialized view schemas

#### Deliverables:
- ✅ SQL migration file
- ✅ Documentation of MV schemas
- ✅ Test queries

---

### Phase 2: Supabase Dashboard Tables + RLS ✅
**Status**: Planning  
**Estimated Time**: 3-4 days

#### Tasks:
- [ ] Create Supabase dashboard schema
  - [ ] `dashboard.sales_summary` table
  - [ ] `dashboard.kpis` table
  - [ ] `dashboard.leaderboard` table
  - [ ] `dashboard.competition_ranks` table
  - [ ] `dashboard.metadata` table (untuk sync status)
- [ ] Create RLS Policies
  - [ ] Policy untuk `super_admin` (see all)
  - [ ] Policy untuk `rbm` (see own region + zona_rbm)
  - [ ] Policy untuk `bm` (see own branch + zona_bm)
  - [ ] Policy untuk `salesman` (see own data)
  - [ ] Policy untuk `head` (see national)
- [ ] Create migration script: `create_dashboard_tables_rls.sql`
- [ ] Test RLS policies dengan different user roles

#### Deliverables:
- ✅ SQL migration file
- ✅ RLS policy documentation
- ✅ Test cases untuk RLS

---

### Phase 3: ETL Script (BQ → Supabase) ✅
**Status**: Planning  
**Estimated Time**: 2-3 days

#### Tasks:
- [ ] Create unified ETL script: `backend/scripts/etl/refresh_dashboard.py`
  - [ ] Function: `refresh_bq_materialized_views()`
  - [ ] Function: `sync_to_supabase()` (all tables)
  - [ ] Function: `invalidate_cache()`
  - [ ] Main function: `refresh_all()` (unified trigger)
- [ ] Error handling & logging
- [ ] Batch processing untuk large datasets
- [ ] Progress tracking
- [ ] Test dengan sample data

#### Deliverables:
- ✅ ETL script
- ✅ Error handling
- ✅ Logging & monitoring

---

### Phase 4: API Endpoints ✅
**Status**: Planning  
**Estimated Time**: 1-2 days

#### Tasks:
- [ ] Create API endpoint: `POST /api/admin/dashboard/refresh`
  - [ ] Manual trigger untuk refresh
  - [ ] Background task support (optional)
  - [ ] Response dengan status & timing
- [ ] Create API endpoint: `GET /api/admin/dashboard/refresh-status`
  - [ ] Last sync timestamp
  - [ ] Sync status
- [ ] Add RBAC permission: `system.admin`
- [ ] Add to admin routes

#### Deliverables:
- ✅ API endpoints
- ✅ RBAC integration
- ✅ API documentation

---

### Phase 5: Redis Cache Integration ✅
**Status**: Planning  
**Estimated Time**: 2-3 days

#### Tasks:
- [ ] Setup Redis connection
  - [ ] Local development (Docker)
  - [ ] Production (Cloud Redis / Redis Cloud)
- [ ] Create cache service: `backend/cache/dashboard_cache.py`
  - [ ] Multi-level caching (L1: filtered, L2: unfiltered)
  - [ ] Cache key generation dengan user context
  - [ ] TTL management (24 hours)
  - [ ] Cache invalidation
- [ ] Integrate dengan dashboard service
- [ ] Test cache hit/miss scenarios

#### Deliverables:
- ✅ Cache service
- ✅ Redis configuration
- ✅ Cache strategy documentation

---

### Phase 6: Dashboard Service Layer ✅
**Status**: Planning  
**Estimated Time**: 3-4 days

#### Tasks:
- [ ] Create dashboard service: `backend/services/dashboard_service.py`
  - [ ] `get_sales_summary()` dengan RLS + cache
  - [ ] `get_kpis()` dengan RLS + cache
  - [ ] `get_leaderboard()` dengan RLS + cache
  - [ ] `get_competition_ranks()` dengan RLS + cache
- [ ] User context resolution untuk RLS
- [ ] Cache integration
- [ ] Error handling & fallbacks
- [ ] Unit tests

#### Deliverables:
- ✅ Dashboard service
- ✅ Unit tests
- ✅ Service documentation

---

### Phase 7: Frontend Integration ✅
**Status**: Planning  
**Estimated Time**: 2-3 days

#### Tasks:
- [ ] Create admin page: `DashboardRefresh.jsx`
  - [ ] Manual refresh button
  - [ ] Last refresh status
  - [ ] Refresh progress (if async)
- [ ] Update dashboard pages untuk query dari new service
- [ ] Add loading states
- [ ] Add error handling
- [ ] Test dengan different user roles

#### Deliverables:
- ✅ Admin refresh page
- ✅ Updated dashboard pages
- ✅ Frontend tests

---

### Phase 8: Master Data Sync (Optional) ✅
**Status**: Planning  
**Estimated Time**: 2-3 days

#### Tasks:
- [ ] Create ETL untuk sync master data Supabase → BigQuery
  - [ ] `master.products` → `pma.master_products`
  - [ ] `master.ref_regions` → `pma.master_regions`
  - [ ] `hr.employees` → `pma.master_employees`
  - [ ] `master.ref_distributors` → `pma.master_distributors`
- [ ] Manual trigger endpoint
- [ ] Test JOIN queries dengan master data

#### Deliverables:
- ✅ Master data sync script
- ✅ API endpoint
- ✅ Test queries

---

## 📝 Technical Specifications

### BigQuery Materialized Views

#### `dashboard_sales_enriched_mv`
```sql
SELECT 
    DATE(t.tgl) as date,
    t.pma as region_code,
    t.kd_brg as product_code,
    t.kode_salesman as nik,
    SUM(t.value) as revenue,
    SUM(t.qty) as qty,
    COUNT(DISTINCT t.no_faktur) as transaction_count
FROM `pma.all_prc` t
LEFT JOIN `pma.master_products` p ON t.kd_brg = p.product_code
LEFT JOIN `pma.master_employees` e ON t.kode_salesman = e.nik
WHERE t.tgl >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
GROUP BY date, region_code, product_code, nik
```

#### `dashboard_kpis_mv`
```sql
SELECT 
    DATE(t.tgl) as date,
    t.pma as region_code,
    SUM(t.value) as total_revenue,
    SUM(t.qty) as total_qty,
    COUNT(DISTINCT t.no_faktur) as transaction_count,
    COUNT(DISTINCT t.kode_outlet) as outlet_count,
    COUNT(DISTINCT t.kode_salesman) as salesman_count
FROM `pma.all_prc` t
WHERE t.tgl >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
GROUP BY date, region_code
```

### Supabase RLS Policies

#### Policy Pattern
```sql
CREATE POLICY "dashboard_sales_rls" ON dashboard.sales_summary
FOR SELECT
USING (
    -- Super Admin: See all
    (current_setting('app.user_role', true) = 'super_admin')
    OR
    -- RBM: See own region
    (
        current_setting('app.user_role', true) = 'rbm'
        AND region_code = current_setting('app.user_region_code', true)
    )
    OR
    -- BM: See own branch
    (
        current_setting('app.user_role', true) = 'bm'
        AND region_code = current_setting('app.user_region_code', true)
    )
    OR
    -- Salesman: See own data
    (
        current_setting('app.user_role', true) = 'salesman'
        AND nik = current_setting('app.user_nik', true)
    )
);
```

### Cache Strategy

#### Cache Keys
```
L1 (Filtered): sales:{role}:{region_code}:{nik}:{start_date}:{end_date}
L2 (Unfiltered): sales_unfiltered:{start_date}:{end_date}
```

#### TTL
- L1 Cache: 24 hours
- L2 Cache: 24 hours
- Invalidation: On manual refresh

---

## 🔄 Update Flow

### Manual Refresh Process

1. **Admin Upload Data**
   - Admin upload raw transaction data ke BigQuery (`pma.all_prc`)
   - Via BigQuery Console, Cloud Storage, atau API

2. **Trigger Refresh**
   - Admin click "Refresh Dashboard" button di admin panel
   - API call: `POST /api/admin/dashboard/refresh`

3. **ETL Process**
   - Step 1: Refresh BigQuery Materialized Views
   - Step 2: Sync to Supabase Dashboard Tables
   - Step 3: Invalidate Redis Cache

4. **Completion**
   - Status updated di `dashboard.metadata`
   - Frontend shows last refresh timestamp

---

## 📦 Dependencies

### New Dependencies
- `redis` (Python): Redis client
- `google-cloud-bigquery`: BigQuery client (already installed)

### Infrastructure
- Redis instance (local dev: Docker, production: Cloud Redis)
- BigQuery project & dataset
- Supabase project

---

## 🧪 Testing Strategy

### Unit Tests
- ETL script functions
- Dashboard service methods
- Cache service methods
- RLS policy logic

### Integration Tests
- ETL end-to-end (BQ → Supabase)
- API endpoints dengan different user roles
- Cache hit/miss scenarios
- RLS enforcement

### Manual Testing
- Admin upload → refresh → verify data
- Different user roles → verify RLS
- Cache invalidation → verify refresh

---

## 📚 Documentation

### Required Documentation
- [ ] Architecture diagram
- [ ] ETL process documentation
- [ ] RLS policy documentation
- [ ] Cache strategy documentation
- [ ] API documentation
- [ ] Admin guide (how to refresh)

---

## 🚨 Risks & Mitigations

### Risk 1: BigQuery Cost
**Mitigation**: 
- Use Materialized Views (pre-computed)
- Manual refresh only (no frequent queries)
- Partition & cluster tables

### Risk 2: Supabase Storage Limit
**Mitigation**:
- Only store last 90 days
- Archive old data
- Monitor storage usage

### Risk 3: Redis Availability
**Mitigation**:
- Fallback to direct Supabase query
- Cache is optional (performance optimization)
- Monitor Redis health

### Risk 4: RLS Complexity
**Mitigation**:
- Comprehensive testing dengan all roles
- Clear documentation
- Fallback to application-layer filtering

---

## ✅ Success Criteria

1. ✅ Dashboard shows real transaction data from BigQuery
2. ✅ RLS works correctly untuk all user roles
3. ✅ Cache improves response time significantly
4. ✅ Manual refresh process works smoothly
5. ✅ System handles large datasets efficiently
6. ✅ Error handling & logging comprehensive

---

## 📅 Timeline Estimate

**Total Estimated Time**: 18-25 days

- Phase 1: 2-3 days
- Phase 2: 3-4 days
- Phase 3: 2-3 days
- Phase 4: 1-2 days
- Phase 5: 2-3 days
- Phase 6: 3-4 days
- Phase 7: 2-3 days
- Phase 8: 2-3 days (optional)

**Recommended Approach**: Implement in phases, test each phase before moving to next.

---

## 🔗 Related Documents

- `SCALABILITY_IMPLEMENTATION_COMPLETE.md`: Previous scalability optimizations
- `backend/docs/RPC_FUNCTION_EXPLANATION.md`: User context resolution
- `backend/docs/USER_ROLE_RESOLUTION.md`: RLS logic

---

## 📝 Notes

- All updates are manual trigger only (no scheduled jobs)
- Cache TTL: 24 hours (aligned with update frequency)
- RLS policies use Supabase's native RLS (not application-layer)
- Master data sync is optional (can JOIN directly from Supabase if needed)

---

**Next Steps**: 
1. Review & approve roadmap
2. Start Phase 1: BigQuery Materialized Views
3. Create migration scripts
4. Test with sample data
