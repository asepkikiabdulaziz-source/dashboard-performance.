# Panduan Manajemen User Supabase

Karena kita menggunakan User Metadata untuk menyimpan `role` dan `region`, cara termudah untuk mengubahnya adalah melalui **SQL Editor** di Supabase Dashboard.

## Cara Mengubah Role & Region User

1.  Login ke [Supabase Dashboard](https://supabase.com/dashboard).
2.  Pilih Project Anda.
3.  Di menu kiri, klik icon **SQL Editor** (icon `>_` atau terminal).
4.  Klik **"New Query"**.
5.  Copy-Paste script di bawah ini, sesuaikan isinya, lalu klik **Run** (Ctrl+Enter).

### Script SQL Update User

```sql
-- Ganti email target dan data baru di bawah ini
UPDATE auth.users
SET raw_user_meta_data = jsonb_build_object(
  'name', 'Nama Baru User',
  'role', 'viewer',            -- Opsi: 'admin', 'viewer'
  'region', 'R02 RIAU DARATAN' -- Opsi: 'ALL' atau Kode Region
)
WHERE email = 'user-a@company.com';
```

---

## Verifikasi
Setelah menjalankannya, user tersebut harus **Logout dan Login ulang** di aplikasi dashboard agar perubahan hak akses terasa (karena data region tersimpan di Token sesi).

## Daftar Role yang Tersedia
-   **admin**: Bisa melihat semua data (`region: 'ALL'`) dan switch region.
-   **viewer**: Hanya bisa melihat data sesuai `region` yang ditugaskan.

---

## Studi Kasus: User Sudah Ada tapi Tidak Bisa Akses

Jika user `asep_kiki@pinusmerahabadi.co.id` sudah ada tapi belum punya hak akses (Metadata kosong), jalankan script ini:

```sql
UPDATE auth.users
SET raw_user_meta_data = jsonb_build_object(
  'name', 'Pak Asep Kiki',
  'role', 'admin',             -- Ganti 'viewer' jika bukan admin
  'region', 'ALL'              -- Ganti kode region (misal 'R05') jika bukan admin
)
WHERE email = 'asep_kiki@pinusmerahabadi.co.id';
```
