# 📊 Analisis Tabel yang Digunakan: Leaderboard & Kompetisi

**Date**: 2026-02-02  
**Status**: Current Implementation Analysis

---

## 🎯 Summary

### **Leaderboard**
- **Tabel**: `FINAL_SCORECARD_RANKED` (BigQuery)
- **Source**: Materialized via stored procedure
- **Rows**: 968 records
- **Caching**: In-memory cache (LeaderboardCache)
- **RLS**: Region-based filtering

### **Kompetisi (AMO)**
- **Tabel**: `rank_ass`, `rank_bm`, `rank_rbm` (BigQuery)
- **Source**: Materialized via stored procedure
- **Caching**: In-memory cache (competition_data)
- **RLS**: Complex (role + region + zone-based)

---

## 📋 DETAILED ANALYSIS

### 1. LEADERBOARD (`/api/leaderboard`)

#### **Tabel yang Digunakan**
```
BigQuery: myproject-482315.pma.FINAL_SCORECARD_RANKED
```

#### **Query Behaviour**
```python
# backend/bigquery_service.py - get_leaderboard()

SELECT 
    region,
    kd_dist,
    area,
    kd_sls as salesman_code,
    nm_sls as salesman_name,
    div_sls as division,
    nik,
    Omset_P1, Omset_P2, Omset_P3, Omset_P4,
    target_oms,
    Total_Score_Final,
    Ranking_Regional,
    ROA_P1, ROA_P2, ROA_P3, ROA_P4,
    Total_CB, EC_Akumulasi,
    saldo_point,
    ... (46 columns total)
FROM `myproject-482315.pma.FINAL_SCORECARD_RANKED`
WHERE region = '{user_region}'  -- RLS filtering
  AND div_sls = '{division}'     -- Optional filter
ORDER BY Ranking_Regional ASC, Total_Score_Final DESC
LIMIT {limit}
```

#### **RLS Behaviour**
1. **Regular Users**:
   - Auto-filtered by `user_region` (dari token)
   - Cannot override region
   - Only see data dari region mereka

2. **Admin Users** (user_region = "ALL"):
   - Can override region via query param `?region=R06`
   - Can see all regions jika tidak specify region
   - Full access

#### **Caching Behaviour**
```python
# backend/cache_manager.py - LeaderboardCache

1. Initial Load:
   - Query BigQuery dengan region="ALL" (load semua data)
   - Store di memory: self._all_data
   - Background thread refresh setiap 15 menit

2. User Request:
   - Filter in-memory berdasarkan user_region
   - Return filtered results
   - No BigQuery query per request (sangat cepat)

3. Auto Refresh:
   - Check cutoff_date setiap 15 menit
   - Jika cutoff_date berubah → refresh cache
   - Background thread (non-blocking)
```

#### **API Endpoint**
```
GET /api/leaderboard?limit=100&division=DIV01&region=R06
```

**Flow**:
1. User request → `get_leaderboard()` endpoint
2. RLS check → `get_user_region()` dependency
3. Cache lookup → `cache_manager.get_leaderboard(region, division, limit)`
4. In-memory filter → Return filtered data
5. Response → JSON list of salesman records

---

### 2. KOMPETISI (`/api/dashboard/competition/{competition_id}/{level}`)

#### **Tabel yang Digunakan**
```
BigQuery: 
- myproject-482315.pma.rank_ass   (untuk level='ass')
- myproject-482315.pma.rank_bm   (untuk level='bm')
- myproject-482315.pma.rank_rbm  (untuk level='rbm')
```

**Mapping** (dari `competition_config.py`):
```python
COMPETITIONS = {
    "amo_jan_2026": {
        "tables": {
            "ass": "rank_ass",
            "bm": "rank_bm", 
            "rbm": "rank_rbm"
        }
    }
}
```

#### **Query Behaviour**
```python
# backend/bigquery_service.py - get_competition_ranks()

# 1. Determine table berdasarkan level
table_name = config["tables"][level]  # "rank_ass", "rank_bm", or "rank_rbm"
full_table_id = f"`{project_id}.{dataset}.{table_name}`"

# 2. Complex RLS Filtering
WHERE clauses berdasarkan:
- User role (super_admin, rbm, bm, salesman)
- Level (ass, bm, rbm)
- Region
- Zona_RBM
- Zona_BM
- Scope & Scope_ID

# 3. Query
SELECT * FROM {table_name}
WHERE {complex_rls_filters}
ORDER BY {rank_col} ASC
LIMIT {limit}
```

#### **RLS Behaviour (Complex)**

**Level: RBM**
```python
if role == 'rbm':
    if zona_rbm:
        WHERE ZONA_RBM = '{zona_rbm}'
    elif region != "ALL":
        WHERE REGION = '{region}'
```

**Level: BM**
```python
if role == 'bm':
    if zona_bm:
        WHERE ZONA_BM = '{zona_bm}'
    elif zona_rbm:
        WHERE ZONA_RBM = '{zona_rbm}'
    elif region != "ALL":
        WHERE REGION = '{region}'
```

**Level: ASS**
```python
if role == 'bm' and scope_id:
    WHERE (ZONA_BM = '{scope_id}' OR CABANG = '{scope_id}')
elif region != "ALL":
    WHERE REGION = '{region}'
```

**Admin**:
- Can see all jika tidak specify filter
- Can filter by region, zona_bm, zona_rbm via query params

#### **Caching Behaviour**
```python
# backend/cache_manager.py - get_competition_ranks_cached()

1. Initial Load:
   - Query BigQuery dengan region="ALL" untuk setiap level
   - Store di memory: self._competition_data["{comp_id}_{level}"]
   - Background thread refresh setiap 15 menit

2. User Request:
   - Get dari cache: self._competition_data.get(f"{comp_id}_{level}")
   - Apply in-memory RLS filtering
   - Return filtered results

3. Filter Logic (in-memory):
   - Same complex RLS logic as BigQuery query
   - Filter Python list berdasarkan user context
```

#### **API Endpoint**
```
GET /api/dashboard/competition/amo_jan_2026/ass?region=R06&zona_bm=DP EAST
```

**Flow**:
1. User request → `get_competition_ranks_v2()` endpoint
2. Extract user context → role, region, scope, zona_rbm, zona_bm
3. Cache lookup → `cache_manager.get_competition_ranks_cached()`
4. In-memory RLS filter → Apply complex filtering
5. Response → JSON list of competition ranks

---

## 🔄 Data Flow Comparison

### **Current Implementation (BigQuery Direct)**

```
┌─────────────────────────────────────────────────┐
│  USER REQUEST                                   │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  FastAPI Endpoint                               │
│  - RLS Check (get_user_region)                  │
│  - Extract filters                              │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  Cache Manager (In-Memory)                      │
│  - Check cache (self._all_data)                 │
│  - Filter in-memory                             │
│  - Return results                               │
└─────────────────────────────────────────────────┘
         │
         ▼ (if cache miss or refresh needed)
┌─────────────────────────────────────────────────┐
│  BigQuery Service                               │
│  - Query FINAL_SCORECARD_RANKED                 │
│  - Apply RLS filters                            │
│  - Return DataFrame                             │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  Cache Update                                   │
│  - Store in memory                              │
│  - Background refresh                           │
└─────────────────────────────────────────────────┘
```

### **Proposed Implementation (Supabase + RLS)**

```
┌─────────────────────────────────────────────────┐
│  USER REQUEST                                   │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  FastAPI Endpoint                               │
│  - Set user context headers                     │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  Supabase Query (with RLS)                      │
│  - RLS policies auto-apply                      │
│  - Filtered results                             │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  Redis Cache (Optional)                         │
│  - Cache filtered results                       │
│  - TTL: 24 hours                                │
└─────────────────────────────────────────────────┘
```

---

## 📊 Table Structure

### **FINAL_SCORECARD_RANKED**
- **Columns**: 46 columns
- **Key Columns**:
  - Identity: `region`, `nik`, `kd_sls`, `nm_sls`, `div_sls`
  - Revenue: `Omset_P1` to `Omset_P4`, `target_oms`
  - Scoring: `Total_Score_Final`, `Ranking_Regional`
  - ROA: `ROA_P1` to `ROA_P4`
  - Points: `pts_Omset_P1` to `pts_Omset_P4`, `pts_ROA_P1` to `pts_ROA_P3`
  - Customer: `Total_CB`, `EC_Akumulasi`
  - Balance: `saldo_point`

### **rank_ass, rank_bm, rank_rbm**
- **Common Columns**:
  - `REGION`, `NIK_ASS`, `NAMA_ASS`, `rank_ASS` (or `rank_zona`)
  - `OMSET`, `TARGET`, `total_Point`
  - `point_oms`, `point_ROA`, `ach_oms`, `ach_ROA`
  - `CABANG`, `ZONA_BM`, `ZONA_RBM`
  - `REWARD`, `CB`, `act_roa`

**Differences**:
- `rank_ass`: Uses `rank_ASS` column, `NAMA_ASS` for name
- `rank_bm`: Uses `rank_zona` column, `CABANG` for name
- `rank_rbm`: Uses `rank_zona` column, `ZONA_RBM` for name

---

## 🔍 Key Behaviours

### **1. Caching Strategy**
- ✅ **In-memory cache** (Python dict/list)
- ✅ **Background refresh** (every 15 min or on cutoff_date change)
- ✅ **Load all data** (region="ALL") then filter in-memory
- ✅ **Fast response** (no BigQuery query per request)

### **2. RLS Implementation**
- ✅ **Application-layer RLS** (Python filtering)
- ✅ **Complex logic** (role + region + zone + scope)
- ✅ **User context** dari token (role, region, scope_id, zona_rbm, zona_bm)

### **3. Data Freshness**
- ✅ **Auto-refresh** on cutoff_date change
- ✅ **Background thread** (non-blocking)
- ✅ **Fallback** to BigQuery jika cache miss

### **4. Performance**
- ✅ **Fast**: In-memory filtering (microseconds)
- ✅ **Scalable**: Cache all data once, filter on-demand
- ✅ **Efficient**: No repeated BigQuery queries

---

## ⚠️ Current Limitations

1. **In-Memory Cache**:
   - Limited by server RAM
   - Not shared across multiple instances
   - Lost on server restart

2. **Application-Layer RLS**:
   - RLS logic di Python code (bukan database)
   - Complex logic scattered across files
   - Harder to maintain

3. **No Supabase Integration**:
   - All queries langsung ke BigQuery
   - Tidak ada RLS di database level
   - Tidak bisa leverage Supabase features

---

## ✅ Benefits of Moving to Supabase

1. **Database-Level RLS**:
   - RLS policies di Supabase (bukan Python)
   - More secure (enforced at DB level)
   - Easier to maintain

2. **Redis Cache**:
   - Shared cache across instances
   - Persistent (survives server restart)
   - Better for distributed systems

3. **Simplified Code**:
   - Less complex filtering logic
   - Supabase handles RLS automatically
   - Cleaner codebase

---

## 🎯 Recommendation

**Keep current implementation** untuk:
- ✅ Performance (sudah optimal dengan in-memory cache)
- ✅ Simplicity (tidak perlu sync ke Supabase)

**Move to Supabase** untuk:
- ✅ Better RLS (database-level)
- ✅ Scalability (Redis cache, multiple instances)
- ✅ Maintainability (less complex code)

**Hybrid Approach** (Recommended):
- ✅ Sync to Supabase (for RLS)
- ✅ Keep Redis cache (for performance)
- ✅ Use Supabase RLS (for security)
- ✅ Fallback to current cache (if needed)

---

**Next Step**: Implement Supabase sync dengan RLS policies yang match current behaviour!
