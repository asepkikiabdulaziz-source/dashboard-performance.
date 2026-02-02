# Setup Database Connection untuk Migration

## Masalah

Connection string dari `.env` mungkin menggunakan format Direct connection, bukan Pooler connection.

## Solusi

### 1. Dapatkan Connection String yang Benar

**Di Supabase Dashboard:**
1. Buka project Anda
2. Settings > Database
3. Scroll ke "Connection string"
4. Pilih tab **"Pooler mode"** (BUKAN Direct connection)
5. Copy connection string

**Format yang benar:**
```
postgresql://postgres.xxx:password@aws-X-region.pooler.supabase.com:6543/postgres
```

**Format yang SALAH (Direct connection):**
```
postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
```

### 2. Update .env File

Tambahkan atau update di `.env`:

```bash
# Pooler connection (RECOMMENDED untuk migrations)
DATABASE_URL=postgresql://postgres.mcbrliwcekwhujsiyklk:Ak3403090115@aws-1-ap-south-1.pooler.supabase.com:6543/postgres
```

**Atau gunakan variabel terpisah:**

```bash
SUPABASE_DB_HOST=aws-1-ap-south-1.pooler.supabase.com
SUPABASE_DB_PORT=6543
SUPABASE_DB_USER=postgres.mcbrliwcekwhujsiyklk
SUPABASE_DB_PASSWORD=Ak3403090115
SUPABASE_DB_NAME=postgres
```

### 3. Test Connection

```bash
python backend/scripts/utils/test_db_connection.py
```

**Expected output:**
```
[OK] Connection successful!
     PostgreSQL version: PostgreSQL 15.x
     Current schema: public
     HR schema exists: Yes
```

### 4. Run Migration

Setelah connection test berhasil:

```bash
python backend/scripts/utils/run_user_context_rpc_migration.py
```

## Troubleshooting

### Error: "could not translate host name"

**Penyebab**: Hostname tidak valid atau menggunakan Direct connection

**Solusi**: 
- Gunakan Pooler connection string dari Supabase Dashboard
- Format: `aws-X-region.pooler.supabase.com` (bukan `db.xxx.supabase.co`)

### Error: "connection timeout"

**Penyebab**: Firewall atau network issue

**Solusi**:
- Check firewall settings
- Try dari network yang berbeda
- Verify Supabase project is active

### Error: "authentication failed"

**Penyebab**: Username atau password salah

**Solusi**:
- Verify connection string dari Supabase Dashboard
- Check username format: `postgres.xxx` (bukan hanya `postgres`)
- Reset password di Supabase jika perlu

## Perbedaan Direct vs Pooler

| Mode | Hostname Format | Port | Use Case |
|------|----------------|------|----------|
| **Direct** | `db.xxx.supabase.co` | 5432 | Development, single connection |
| **Pooler** | `aws-X-region.pooler.supabase.com` | 6543 | Production, multiple connections, migrations |

**Untuk migrations, gunakan Pooler mode!**
