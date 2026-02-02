# 🚀 Panduan Memulai: Real Dashboard Implementation

**Status**: Ready to Start  
**Last Updated**: 2026-02-02

---

## 🎯 Tujuan

Membantu Anda memulai implementasi dashboard real dengan langkah-langkah yang jelas dan bisa di-test satu per satu.

---

## 📋 Prerequisites (Cek Dulu)

Sebelum mulai, pastikan:

- [ ] ✅ BigQuery credentials sudah setup (`bigquery-credentials.json` atau ADC)
- [ ] ✅ Supabase connection sudah working
- [ ] ✅ Data di BigQuery sudah ada (`pma.all_prc` dan `pma.FINAL_SCORECARD_RANKED`)
- [ ] ✅ Master data di Supabase sudah ada

---

## 🗺️ Step-by-Step Implementation

### **STEP 0: Exploration & Verification** ⭐ START HERE
**Waktu**: 30 menit  
**Tujuan**: Pastikan data yang ada dan pahami strukturnya

#### Tasks:
1. **Cek BigQuery Tables**
   ```python
   # Run script untuk explore data
   python backend/scripts/utils/explore_scorecard.py
   python backend/scripts/utils/simple_schema.py
   ```

2. **Cek Data yang Ada**
   - Apakah `pma.all_prc` sudah ada data?
   - Apakah `pma.FINAL_SCORECARD_RANKED` sudah ada data?
   - Berapa banyak rows?
   - Apa saja kolom-kolomnya?

3. **Cek Master Data di Supabase**
   - Apakah `master.products` sudah ada?
   - Apakah `hr.employees` sudah ada?
   - Apakah bisa JOIN dengan data BigQuery?

#### Deliverable:
- ✅ Daftar tabel yang tersedia
- ✅ Sample data dari setiap tabel
- ✅ Mapping kolom untuk JOIN

---

### **STEP 1: Simple Test Query** 
**Waktu**: 1 jam  
**Tujuan**: Test query BigQuery langsung dan verify hasilnya

#### Tasks:
1. **Buat script test sederhana**
   ```python
   # backend/scripts/test/test_bq_simple_query.py
   # Query sederhana dari FINAL_SCORECARD_RANKED
   ```

2. **Test Query**
   - Query leaderboard data
   - Query sales summary
   - Verify hasil sesuai ekspektasi

3. **Test dengan User Context**
   - Test RLS filtering (region-based)
   - Verify data yang di-filter sesuai role user

#### Deliverable:
- ✅ Script test query
- ✅ Sample output
- ✅ Verification bahwa data bisa di-query

---

### **STEP 2: Create Simple Materialized View** 
**Waktu**: 2 jam  
**Tujuan**: Test konsep Materialized View dengan data sederhana

#### Tasks:
1. **Buat Materialized View Sederhana**
   ```sql
   -- Test dengan 1 MV dulu: dashboard_leaderboard_mv
   -- Copy dari FINAL_SCORECARD_RANKED (tanpa JOIN dulu)
   ```

2. **Test Refresh MV**
   - Create MV
   - Test refresh
   - Query dari MV
   - Verify hasil sama dengan query langsung

3. **Test Performance**
   - Compare query time: direct vs MV
   - Verify MV lebih cepat

#### Deliverable:
- ✅ SQL untuk create MV
- ✅ Test script untuk refresh
- ✅ Performance comparison

---

### **STEP 3: Create Simple Supabase Table** 
**Waktu**: 2 jam  
**Tujuan**: Test Supabase table dan RLS sederhana

#### Tasks:
1. **Buat Table Sederhana**
   ```sql
   -- dashboard.leaderboard (copy dari FINAL_SCORECARD_RANKED)
   -- Tanpa RLS dulu, test insert/select dulu
   ```

2. **Test Insert Data**
   - Insert sample data dari BigQuery
   - Verify data masuk dengan benar

3. **Test Basic RLS**
   - Enable RLS
   - Create policy sederhana (role-based)
   - Test dengan different user roles

#### Deliverable:
- ✅ SQL migration untuk table
- ✅ SQL migration untuk RLS policy
- ✅ Test script untuk insert & query

---

### **STEP 4: Simple ETL Script** 
**Waktu**: 3 jam  
**Tujuan**: Test end-to-end flow (BQ → Supabase)

#### Tasks:
1. **Buat ETL Script Sederhana**
   ```python
   # backend/scripts/etl/test_simple_sync.py
   # Sync leaderboard dari BQ MV ke Supabase
   ```

2. **Test ETL Flow**
   - Query dari BQ MV
   - Insert ke Supabase
   - Verify data sync dengan benar

3. **Test Manual Trigger**
   - Create API endpoint sederhana
   - Test trigger dari admin panel
   - Verify refresh bekerja

#### Deliverable:
- ✅ ETL script
- ✅ API endpoint
- ✅ Test end-to-end

---

### **STEP 5: Scale Up (Full Implementation)**
**Waktu**: 2-3 minggu  
**Tujuan**: Implement semua fitur sesuai roadmap

Setelah Step 1-4 berhasil, lanjut ke:
- Phase 1: All Materialized Views
- Phase 2: All Supabase Tables + Complex RLS
- Phase 3: Full ETL Script
- Phase 4: API Endpoints
- Phase 5: Redis Cache
- Phase 6: Dashboard Service
- Phase 7: Frontend Integration

---

## 🎯 Rekomendasi: Mulai dari STEP 0

**Kenapa STEP 0?**
1. ✅ Tidak perlu coding, hanya exploration
2. ✅ Bisa langsung verify data yang ada
3. ✅ Pahami struktur sebelum build
4. ✅ Identifikasi masalah lebih awal

**Action Items untuk STEP 0:**

1. **Run exploration scripts**:
   ```bash
   cd backend
   python scripts/utils/explore_scorecard.py
   python scripts/utils/simple_schema.py
   ```

2. **Cek BigQuery tables**:
   - Buka BigQuery Console
   - Cek `pma.all_prc` (raw transactions)
   - Cek `pma.FINAL_SCORECARD_RANKED` (leaderboard)

3. **Cek Supabase master data**:
   - Buka Supabase Dashboard
   - Cek `master.products`
   - Cek `hr.employees`
   - Cek `master.ref_regions`

4. **Document findings**:
   - List semua tabel yang ada
   - List kolom-kolom penting
   - Identifikasi kolom untuk JOIN

---

## 📝 Checklist: Ready to Start?

Sebelum mulai STEP 1, pastikan:

- [ ] ✅ STEP 0 selesai (exploration)
- [ ] ✅ Data di BigQuery sudah verified
- [ ] ✅ Master data di Supabase sudah verified
- [ ] ✅ Paham struktur data yang ada
- [ ] ✅ Tahu kolom-kolom untuk JOIN

---

## 🆘 Jika Ada Masalah

### Problem: BigQuery connection error
**Solution**: 
- Cek credentials file
- Cek environment variables
- Test dengan `bq` CLI

### Problem: Data tidak ada
**Solution**:
- Upload sample data dulu
- Atau skip ke STEP 2 dengan mock data

### Problem: Supabase connection error
**Solution**:
- Cek `.env` file
- Cek Supabase URL & keys
- Test connection dengan simple query

---

## 🎓 Learning Path

**Beginner** (Baru mulai):
- Start dari STEP 0
- Ikuti step-by-step
- Test setiap step sebelum lanjut

**Intermediate** (Sudah familiar):
- Skip STEP 0 jika sudah paham data
- Mulai dari STEP 1 atau STEP 2
- Bisa parallel beberapa tasks

**Advanced** (Expert):
- Langsung ke STEP 5 (Full Implementation)
- Reference roadmap untuk detail

---

## 📚 Resources

- **Roadmap Detail**: `DASHBOARD_REAL_ROADMAP.md`
- **BigQuery Docs**: https://cloud.google.com/bigquery/docs
- **Supabase RLS**: https://supabase.com/docs/guides/auth/row-level-security
- **Redis Cache**: https://redis.io/docs/

---

## ✅ Next Action

**Sekarang**: Mulai dari **STEP 0 - Exploration**

1. Run exploration scripts
2. Cek data yang ada
3. Document findings
4. Report hasil ke tim

Setelah STEP 0 selesai, kita lanjut ke STEP 1! 🚀
