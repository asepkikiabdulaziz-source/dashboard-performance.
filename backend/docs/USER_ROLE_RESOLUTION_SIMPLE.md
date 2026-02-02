# Cara Sistem Mengetahui Role & Scope User

## Jawaban Singkat

Sistem **TIDAK hardcode** role user. Sistem membaca dari **database** melalui **Slot Assignment System**.

## Flow Sederhana

```
User Login
    ↓
Email → Cari di hr.employees → Dapat NIK
    ↓
NIK → Cari di hr.assignments → Dapat slot_code (yang aktif)
    ↓
slot_code → Cari di master.sales_slots → Dapat:
    - role (super_admin, rbm, bm, head, salesman)
    - scope (NATIONAL, REGION, BRANCH, DEPO)
    - scope_id (ID dari scope tersebut)
    ↓
scope_id → Jika REGION, cari di master.ref_regions → Dapat nama region
    ↓
Hasil: User punya role, region, scope
```

## Contoh Konkret

### User A = Super Admin

**Database**:
- `hr.employees`: email='admin@company.com' → nik='ADMIN001'
- `hr.assignments`: nik='ADMIN001' → slot_code='SL-ADMIN-001' (aktif)
- `master.sales_slots`: slot_code='SL-ADMIN-001' → role='super_admin', scope='NATIONAL'

**Hasil**: role='super_admin', region='ALL', scope='NATIONAL'

### User B = RBM, Scope Region

**Database**:
- `hr.employees`: email='rbm@company.com' → nik='RBM001'
- `hr.assignments`: nik='RBM001' → slot_code='SL-RBM-JBO-001' (aktif)
- `master.sales_slots`: slot_code='SL-RBM-JBO-001' → role='rbm', scope='REGION', scope_id='R06'
- `master.ref_regions`: region_code='R06' → name='R06 JABODEBEK'

**Hasil**: role='rbm', region='R06 JABODEBEK', scope='REGION', scope_id='R06'

### User C = Head, Scope Nasional

**Database**:
- `hr.employees`: email='head@company.com' → nik='HEAD001'
- `hr.assignments`: nik='HEAD001' → slot_code='SL-HEAD-NAT-001' (aktif)
- `master.sales_slots`: slot_code='SL-HEAD-NAT-001' → role='head', scope='NATIONAL'

**Hasil**: role='head', region='ALL', scope='NATIONAL'

## Tabel Database yang Terlibat

| Tabel | Fungsi | Field Penting |
|-------|--------|---------------|
| `hr.employees` | Master karyawan | email, nik, full_name |
| `hr.assignments` | Assignment karyawan ke slot | nik, slot_code, start_date, end_date |
| `master.sales_slots` | Master slot/posisi | slot_code, **role**, **scope**, **scope_id** |
| `master.ref_regions` | Master region | region_code, name |

## Kunci Penting

1. **Role & Scope ada di `master.sales_slots`**, bukan di user metadata
2. **Assignment aktif** = `end_date IS NULL` atau `end_date > today`
3. **Sistem otomatis resolve** setiap kali user login
4. **Untuk ubah role/scope**: Ubah assignment atau ubah slot definition

## Cara Set User Role

### Step 1: Buat Slot (jika belum ada)
```sql
INSERT INTO master.sales_slots (slot_code, role, scope, scope_id)
VALUES ('SL-RBM-JBO-001', 'rbm', 'REGION', 'R06');
```

### Step 2: Assign User ke Slot
```sql
INSERT INTO hr.assignments (nik, slot_code, start_date)
VALUES ('RBM001', 'SL-RBM-JBO-001', CURRENT_DATE);
```

### Step 3: User Login
Sistem otomatis resolve role='rbm', scope='REGION', region='R06 JABODEBEK'

## Kesimpulan

**Sistem tahu role & scope dari database, bukan hardcode!**

- ✅ User A = super admin → Karena slot assignment-nya ke slot dengan role='super_admin', scope='NATIONAL'
- ✅ User B = RBM → Karena slot assignment-nya ke slot dengan role='rbm', scope='REGION', scope_id='R06'
- ✅ User C = Head → Karena slot assignment-nya ke slot dengan role='head', scope='NATIONAL'

**Semua bisa diubah dengan mengubah assignment atau slot definition di database!**
