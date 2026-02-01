# Schema Concept & Architecture

## 1. Region & GRBM (Hierarchy in Lookup)

**Pertanyaan User**: "Region punya relasi ke GRBM. GRBM ke Company. Kenapa masuk Lookup?"

**Penjelasan Sistem**:
Tabel `ref_lookup` memiliki kolom **`parent_code`**. Kolom ini memfasilitasi relasi hierarki tanpa perlu tabel terpisah.

**Contoh Data (Simulasi):**
| Category  | Code   | Name           | Parent Code (Relasi) |
| :---      | :---   | :---           | :---                 |
| **GRBM**  | `LP-2` | Sulawesi Area  | `ID001` (Link ke Company) |
| **REGION**| `R18`  | Makassar Area  | **`LP-2`** (Link ke GRBM) |

*   **Kesimpulan**: Relasi (Foreign Key logis) tetap ada dan terjaga melalui kolom `parent_code`. Ini adalah pola "Adjacency List" dalam satu tabel.

## 2. Role vs Level (Function vs Grade)

**Pertanyaan User**: "Kenapa Level tidak disatukan di ref_role?"

**Penjelasan Sistem**:
Pemisahan ini memungkinkan fleksibilitas **"Matrix"** (Fungsi vs Senioritas).

### Jika Disatukan (Role includes Level):
Kita harus membuat Role ID unik untuk setiap kombinasi:
1. `SALESMAN_ENTRY`
2. `SALESMAN_SENIOR`
3. `SUPERVISOR_ENTRY`
4. `SUPERVISOR_SENIOR`
*(Jumlah Role meledak)*

### Jika Dipisah (Current Design):
Kita cukup punya 1 Role "Salesman", dan bisa dikombinasikan dengan Level apapun.
*   **Role**: `SALESMAN` (Fungsi: Jualan)
*   **Level**: `1` (Junior) atau `4` (Managerial)

**Keuntungan**:
1.  Master Role tetap bersih (hanya 4-5 item).
2.  Level bisa distandarisasi untuk semua departemen (Level 1 selalu Entry, baik Salesman maupun HR).
3.  Di `sales_slots`, kita bisa lihat data seperti Role `SALESMAN` tapi Level `99` (Special), yang sulit diakomodasi jika hardcoded di Role.
