# 📋 Guide: Mengelola Tables di Masa Depan

## Overview

Aplikasi dirancang untuk **fleksibel** - Anda bisa menambah, menghapus, atau disable tables tanpa harus mengubah banyak code.

## Cara Menghapus/Disable Table

### Opsi 1: Disable Competition (Recommended)

Edit `backend/competition_config.py`:

```python
COMPETITIONS = {
    "amo_jan_2026": {
        "title": "MONITORING KOMPETISI AMO",
        "period": "JANUARI 2026",
        "enabled": False,  # ← Set ke False untuk disable
        "tables": {
            "ass": "rank_ass",
            "bm": "rank_bm",
            "rbm": "rank_rbm"
        }
    }
}
```

**Hasil:**
- Competition tidak muncul di list
- Endpoint competition tidak bisa diakses
- Tidak ada error, hanya tidak tersedia

### Opsi 2: Disable Level Tertentu

```python
COMPETITIONS = {
    "amo_jan_2026": {
        "tables": {
            "ass": "rank_ass",
            "bm": None,  # ← Disable level BM
            "rbm": "rank_rbm"
        }
    }
}
```

**Hasil:**
- Level BM tidak bisa diakses
- Level ASS dan RBM tetap berfungsi
- Return empty array jika diakses

### Opsi 3: Hapus Competition Entry

Hapus entry dari `COMPETITIONS` dictionary:

```python
COMPETITIONS = {
    # "amo_jan_2026": { ... }  ← Hapus ini
}
```

**Hasil:**
- Competition tidak ada sama sekali
- Error "Invalid competition ID" jika diakses

## Cara Menambah Competition Baru

Edit `backend/competition_config.py`:

```python
COMPETITIONS = {
    "amo_jan_2026": { ... },
    
    "new_competition_feb": {
        "title": "Competition Februari",
        "period": "FEBRUARI 2026",
        "description": "Periode Februari 2026",
        "enabled": True,
        "tables": {
            "ass": "rank_ass_feb",  # Table baru
            "bm": "rank_bm_feb",
            "rbm": "rank_rbm_feb"
        }
    }
}
```

**Tidak perlu:**
- ❌ Edit code lain
- ❌ Restart aplikasi (auto-load dari config)
- ❌ Set environment variables baru

## Cara Mengganti Table Name

### Untuk Main Leaderboard Table

**Via Environment Variable:**
```bash
BIGQUERY_TABLE=new_table_name
```

**Atau via GitHub Secrets:**
- Update `BIGQUERY_TABLE` secret dengan table name baru

### Untuk Competition Tables

Edit `backend/competition_config.py`:

```python
COMPETITIONS = {
    "amo_jan_2026": {
        "tables": {
            "ass": "new_rank_ass",  # ← Ganti table name
            "bm": "rank_bm",
            "rbm": "rank_rbm"
        }
    }
}
```

## Error Handling

Aplikasi sudah handle error dengan baik:

### Jika Table Tidak Ada
- **Competition tables:** Return empty array `[]`
- **Main table:** Return empty data dengan warning
- **Tidak crash aplikasi**

### Jika Table Dihapus di BigQuery
1. Aplikasi akan detect error "table not found"
2. Return empty data
3. Log warning untuk admin
4. Aplikasi tetap berjalan

## Best Practices

### 1. Jangan Hapus Table Langsung di BigQuery
**Sebelum hapus:**
1. Disable di config dulu (`enabled: False`)
2. Deploy dan test
3. Setelah yakin tidak ada yang pakai, baru hapus di BigQuery

### 2. Gunakan Versioning untuk Tables
**Contoh:**
```
rank_ass_v1
rank_ass_v2  ← Table baru
```

**Migrate:**
1. Update config ke table baru
2. Deploy
3. Hapus table lama setelah yakin

### 3. Backup Sebelum Hapus
```sql
-- Backup table sebelum hapus
CREATE TABLE `pma.rank_ass_backup_20260202` AS
SELECT * FROM `pma.rank_ass`;
```

## Migration Checklist

Ketika menghapus/mengganti table:

- [ ] Disable di config (`enabled: False`)
- [ ] Deploy dan test
- [ ] Cek logs - pastikan tidak ada error
- [ ] Backup table (jika perlu)
- [ ] Hapus/ganti table di BigQuery
- [ ] Update config dengan table baru (jika replace)
- [ ] Re-enable (`enabled: True`)
- [ ] Deploy dan verify

## Contoh: Menghapus Competition Lama

```python
# 1. Disable dulu
COMPETITIONS = {
    "old_competition": {
        "enabled": False,  # ← Disable
        ...
    }
}

# 2. Deploy dan test

# 3. Setelah yakin, hapus entry
COMPETITIONS = {
    # "old_competition": { ... }  ← Hapus ini
}
```

---

**Kesimpulan:** Aplikasi sudah dirancang untuk handle perubahan tables dengan baik. Cukup edit `competition_config.py` dan deploy!
