# Panduan Menjalankan Aplikasi Dashboard Performance

Dokumen ini berisi langkah-langkah untuk menyiapkan dan menjalankan aplikasi, serta cara mencoba fitur **Admin Panel** & **Employee Management** yang baru saja ditambahkan.

## 1. Persiapan Database (Supabase)

Sebelum menjalankan aplikasi, Anda perlu memastikan struktur database sudah sesuai.

1.  Login ke [Supabase Dashboard](https://supabase.com/dashboard).
2.  Masuk ke menu **SQL Editor**.
3.  Buka file `backend/schema_migration.sql` di project ini via text editor.
4.  Copy semua isi file tersebut.
5.  Paste ke SQL Editor Supabase dan klik **RUN**.
    *   *Ini akan membuat schema `hr`, `master`, dan tabel `employees`, `ref_role`.*

## 2. Menjalankan Backend (API)

Pastikan terminal berada di folder `backend`.

```bash
# 1. Masuk ke folder backend (jika belum)
cd backend

# 2. Pastikan virtual environment aktif (jika pakai venv)
# Windows:
..\.venv\Scripts\Activate.ps1

# 3. Jalankan server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

*Jika berhasil, Anda akan melihat log:* `Uvicorn running on http://0.0.0.0:8000`

## 3. Menjalankan Frontend (UI)

Buka terminal **baru**, dan arahkan ke folder `frontend`.

```bash
# 1. Masuk ke folder frontend
cd frontend

# 2. Install dependencies (jika belum pernah)
npm install

# 3. Jalankan development server
npm run dev
```

*Aplikasi akan berjalan di:* `http://localhost:5173`

## 4. Cara Mencoba (Skenario Test)

Setelah kedua server berjalan, ikuti langkah ini untuk mencoba fitur baru.

### A. Login sebagai Admin
1.  Buka browser ke [http://localhost:5173](http://localhost:5173).
2.  Login dengan kredensial Admin:
    *   **Email**: `admin@company.com`
    *   **Password**: `admin123`
    *   *(Pastikan user ini sudah ada di `auth.users` Supabase Anda. Jika belum, buat manual via Supabase Dashboard)*.

### B. Masuk ke Admin Panel
1.  Setelah login, klik tombol **"Admin Panel"** di pojok kanan atas navigation bar.
2.  Anda akan melihat halaman dengan dua Tab: **Product Management** dan **Employee Management**.

### C. Mencoba Employee Management
1.  Pilih Tab **Employee Management**.
2.  Klik tombol **"Add Employee"**.
3.  Isi formulir:
    *   **NIK**: `SPV001` (contoh)
    *   **Full Name**: `Budi Supervisor`
    *   **Role**: `Supervisor`
    *   **Email**: `budi@company.com`
4.  Fitur Auto-User:
    *   Centang toggle **"Grant System Access"**.
    *   Isi **Initial Password**: `password123`.
5.  Klik **Create**.

**Verifikasi:**
*   **Di Tabel**: Data "Budi Supervisor" muncul. Kolom "System Access" berwarna **Ungu (Enabled)**.
*   **Di Supabase**: Cek menu **Authentication**, user `budi@company.com` seharusnya sudah terbentuk. Cek tabel `hr.employees`, kolom `auth_user_id` sudah terisi.

### D. Mencoba User Baru
1.  Logout dari akun Admin.
2.  Login dengan akun baru:
    *   User: `budi@company.com`
    *   Pass: `password123`
3.  Anda berhasil masuk! (Namun menu Admin Panel tidak akan muncul karena role-nya Supervisor).
