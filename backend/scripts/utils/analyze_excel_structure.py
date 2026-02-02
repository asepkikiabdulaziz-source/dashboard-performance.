"""
Analyze _master_item.xlsx column structure before import
"""
import pandas as pd

# Read Excel file
df = pd.read_excel('_master_item.xlsx')

print("=== EXCEL FILE ANALYSIS ===\n")
print(f"Total rows: {len(df)}")
print(f"\n=== ALL COLUMNS ({len(df.columns)}) ===")

for i, col in enumerate(df.columns, 1):
    print(f"{i:2d}. {col}")

print("\n=== SAMPLE DATA (first 3 rows) ===")
print(df.head(3).to_string())

print("\n=== COLUMN MAPPING TO master.products ===")
mapping = {
    'KD_SKU': 'sku_code',
    'NAMA_SKU': 'product_name',
    'SHORT_NAME': 'short_name',
    'KD_SKU_PARENT': 'parent_sku_code',
    'NAMA_SKU_PARENT': 'parent_sku_name',
    'PRINCIPAL_ID': 'principal_id',
    'BRAND_ID': 'brand_id',
    'CATEGORY_ID': 'category_id',
    'VARIANT': 'variant',
    'PRICE_SEGMENT': 'price_segment',
    'UOM_SMALL': 'uom_small',
    'ISI_PCS_PER_SMALL': 'isi_pcs_per_small',
    'UOM_MEDIUM': 'uom_medium',
    'ISI_PCS_PER_MEDIUM': 'isi_pcs_per_medium',
    'UOM_LARGE': 'uom_large',
    'ISI_PCS_PER_LARGE': 'isi_pcs_per_large',
    'STATUS_PRODUK': 'is_active',
}

print("\nExpected column mapping:")
for excel_col, db_col in mapping.items():
    exists = "✓" if excel_col in df.columns else "✗"
    print(f"{exists} {excel_col:25} -> {db_col}")

# Check for STATUS_PRODUK values
if 'STATUS_PRODUK' in df.columns:
    print(f"\n=== STATUS_PRODUK values ===")
    print(df['STATUS_PRODUK'].value_counts())
