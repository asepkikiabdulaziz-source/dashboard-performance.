# 📊 BigQuery Tables Configuration

## Overview

Aplikasi menggunakan **multiple tables** dari BigQuery, bukan hanya satu table.

## Tables yang Digunakan

### 1. Main Leaderboard Table
**Config:** `BIGQUERY_TABLE` environment variable
**Default:** `FINAL_SCORECARD_RANKED`
**Digunakan untuk:**
- Leaderboard utama
- KPIs dashboard
- Sales trends
- Region comparison

### 2. Competition Tables
**Config:** `backend/competition_config.py`
**Tables:**
- `rank_ass` - Ranking untuk level ASS
- `rank_bm` - Ranking untuk level BM
- `rank_rbm` - Ranking untuk level RBM

**Semua competition tables menggunakan dataset yang sama** (`BIGQUERY_DATASET`)

### 3. Metadata Table
**Table:** `cut_off`
**Digunakan untuk:**
- Cutoff date
- Ideal target metadata

**Juga menggunakan dataset yang sama**

## Konfigurasi

### Environment Variables (Required)

```bash
BIGQUERY_PROJECT_ID=myproject-482315
BIGQUERY_DATASET=pma
BIGQUERY_TABLE=FINAL_SCORECARD_RANKED  # Main leaderboard table
```

### Competition Tables Configuration

File: `backend/competition_config.py`

```python
COMPETITIONS = {
    "amo_jan_2026": {
        "tables": {
            "ass": "rank_ass",    # Table untuk level ASS
            "bm": "rank_bm",      # Table untuk level BM
            "rbm": "rank_rbm"     # Table untuk level RBM
        }
    }
}
```

**Semua tables harus ada di dataset yang sama** (`BIGQUERY_DATASET`)

## Struktur BigQuery

```
myproject-482315.pma
├── FINAL_SCORECARD_RANKED  (main leaderboard)
├── rank_ass                (competition ASS)
├── rank_bm                 (competition BM)
├── rank_rbm                (competition RBM)
└── cut_off                 (metadata)
```

## Menambah Competition Baru

Edit `backend/competition_config.py`:

```python
COMPETITIONS = {
    "amo_jan_2026": {
        "title": "MONITORING KOMPETISI AMO",
        "period": "JANUARI 2026",
        "tables": {
            "ass": "rank_ass",
            "bm": "rank_bm",
            "rbm": "rank_rbm"
        }
    },
    "new_competition": {
        "title": "New Competition",
        "period": "FEBRUARI 2026",
        "tables": {
            "ass": "new_rank_ass",    # Table baru
            "bm": "new_rank_bm",
            "rbm": "new_rank_rbm"
        }
    }
}
```

## Verifikasi Tables

Pastikan semua tables ada di BigQuery:

```sql
-- Cek semua tables di dataset
SELECT table_name 
FROM `myproject-482315.pma.INFORMATION_SCHEMA.TABLES`
WHERE table_type = 'BASE TABLE'
ORDER BY table_name;
```

**Expected tables:**
- `FINAL_SCORECARD_RANKED`
- `rank_ass`
- `rank_bm`
- `rank_rbm`
- `cut_off`

---

**Catatan:** Hanya `BIGQUERY_TABLE` yang perlu di-set via environment variable. Competition tables dikonfigurasi di code dan menggunakan dataset yang sama.
