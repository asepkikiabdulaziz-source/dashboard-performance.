"""
Import ALL products from _master_item.xlsx to master.products
Includes inactive products to maintain parent-child relationships
"""
import pandas as pd
import numpy as np
from supabase_client import supabase_request

# Read Excel file
df = pd.read_excel('_master_item.xlsx')

print("=== IMPORTING PRODUCTS FROM EXCEL ===\n")
print(f"Total products in Excel: {len(df)}")

# Column mapping based on analysis
COLUMN_MAP = {
    'KD_SKU': 'sku_code',
    'NAMA_SKU': 'product_name',
    'MARK': 'short_name',  # MARK is the short name
    'KD_SKU_PARENT': 'parent_sku_code',
    'NAMA_SKU_PARENT': 'parent_sku_name',
    'PRINC 2': 'principal_id',  # PRINC 2 is the principal
    'BRAND': 'brand_id',
    'CATEGORY': 'category_id',
    'FLAVOUR': 'variant',
    'ECERAN': 'price_segment',  # ECERAN is price segment
    'UOM 1': 'uom_small',
    'ISI 1': 'isi_pcs_per_small',
    'UOM 2': 'uom_medium',
    'ISI 2': 'isi_pcs_per_medium',
    'UOM 3': 'uom_large',
    'ISI 3': 'isi_pcs_per_large',
    'STATUS_PRODUK': 'is_active',
}

# Check which columns exist
print("\n=== COLUMN MAPPING ===")
for excel_col, db_col in COLUMN_MAP.items():
    exists = "✓" if excel_col in df.columns else "✗"
    print(f"{exists} {excel_col:20} -> {db_col}")

# Prepare data for import
products = []
skipped = 0

for idx, row in df.iterrows():
    try:
        # Map STATUS_PRODUK to is_active
        status = row.get('STATUS_PRODUK', 0)
        is_active = True if status == 'Active' else False
        
        # Check if SKU is valid
        sku_code = str(row['KD_SKU']).strip()
        if not sku_code or sku_code == 'nan':
            skipped += 1
            continue
        
        product = {
            'company_id': 'ID001',
            'sku_code': sku_code,
            'product_name': str(row['NAMA_SKU']).strip() if pd.notna(row['NAMA_SKU']) else None,
            'short_name': str(row.get('MARK', '')).strip() if pd.notna(row.get('MARK')) else None,
            'parent_sku_code': str(row['KD_SKU_PARENT']).strip() if pd.notna(row['KD_SKU_PARENT']) else sku_code,
            'parent_sku_name': str(row['NAMA_SKU_PARENT']).strip() if pd.notna(row['NAMA_SKU_PARENT']) else None,
            'principal_id': str(row.get('PRINC 2', '')).strip() if pd.notna(row.get('PRINC 2')) else None,
            'brand_id': str(row.get('BRAND', '')).strip() if pd.notna(row.get('BRAND')) else None,
            'category_id': str(row.get('CATEGORY', '')).strip() if pd.notna(row.get('CATEGORY')) else None,
            'variant': str(row.get('FLAVOUR', '')).strip() if pd.notna(row.get('FLAVOUR')) else None,
            'price_segment': str(row.get('ECERAN', '')).strip() if pd.notna(row.get('ECERAN')) else None,
            'uom_small': str(row.get('UOM 1', '')).strip() if pd.notna(row.get('UOM 1')) else None,
            'isi_pcs_per_small': int(row.get('ISI 1', 0)) if pd.notna(row.get('ISI 1')) and row.get('ISI 1', 0) > 0 else None,
            'uom_medium': str(row.get('UOM 2', '')).strip() if pd.notna(row.get('UOM 2')) else None,
            'isi_pcs_per_medium': int(row.get('ISI 2', 0)) if pd.notna(row.get('ISI 2')) and row.get('ISI 2', 0) > 0 else None,
            'uom_large': str(row.get('UOM 3', '')).strip() if pd.notna(row.get('UOM 3')) else None,
            'isi_pcs_per_large': int(row.get('ISI 3', 0)) if pd.notna(row.get('ISI 3')) and row.get('ISI 3', 0) > 0 else None,
            'is_active': is_active,
            'is_npl': False,  # Default to false, can be updated later
        }
        
        # Clean empty strings to None
        for key, value in product.items():
            if isinstance(value, str) and (value == '' or value == 'nan'):
                product[key] = None
        
        products.append(product)
        
    except Exception as e:
        print(f"Error processing row {idx}: {e}")
        skipped += 1

print(f"\nProducts prepared: {len(products)}")
print(f"Skipped: {skipped}")

# Show sample
print(f"\n=== SAMPLE PRODUCTS (first 3) ===")
for p in products[:3]:
    print(f"\nSKU: {p['sku_code']}")
    print(f"  Name: {p['product_name']}")
    print(f"  Short: {p['short_name']}")
    print(f"  Parent: {p['parent_sku_code']} ({p['parent_sku_name']})")
    print(f"  Category: {p['category_id']}, Brand: {p['brand_id']}, Principal: {p['principal_id']}")
    print(f"  Active: {p['is_active']}")

# Count active vs inactive
active_count = sum(1 for p in products if p['is_active'])
inactive_count = len(products) - active_count
print(f"\n=== STATISTICS ===")
print(f"Active products: {active_count}")
print(f"Inactive products: {inactive_count}")

confirm = input(f"\nProceed to import {len(products)} products? This will DELETE existing products first. (yes/no): ")

if confirm.lower() == 'yes':
    print("\n=== CLEARING EXISTING PRODUCTS ===")
    try:
        # Delete all existing products
        supabase_request('DELETE', 'products', params={'company_id': 'eq.ID001'}, headers_extra={'Accept-Profile': 'master', 'Content-Profile': 'master', 'Prefer': 'return=minimal'})
        print("Existing products cleared.")
    except Exception as e:
        print(f"Error clearing products: {e}")
    
    print("\n=== IMPORTING PRODUCTS ===")
    success_count = 0
    error_count = 0
    
    # Import in batches of 100
    batch_size = 100
    for i in range(0, len(products), batch_size):
        batch = products[i:i+batch_size]
        try:
            supabase_request(
                'POST',
                'products',
                json_data=batch,
                headers_extra={'Accept-Profile': 'master', 'Content-Profile': 'master', 'Prefer': 'return=minimal'}
            )
            success_count += len(batch)
            print(f"Imported {success_count}/{len(products)} products...")
        except Exception as e:
            error_count += len(batch)
            print(f"Error importing batch {i//batch_size + 1}: {e}")
    
    print(f"\n=== IMPORT COMPLETE ===")
    print(f"Successfully imported: {success_count}")
    print(f"Errors: {error_count}")
else:
    print("\nImport cancelled.")
