"""
Import ALL products from _master_item.xlsx to master.products
WITH CORRECT COLUMN MAPPING (verified from actual Excel file)
"""
import pandas as pd
import numpy as np
from supabase_client import supabase_request

# Read Excel file
df = pd.read_excel('_master_item.xlsx')

print("=== IMPORTING PRODUCTS FROM EXCEL ===\n")
print(f"Total products in Excel: {len(df)}")

# CORRECT Column mapping based on actual Excel structure
# Columns: NO, KD_SKU, NAMA_SKU, KD_SKU_PARENT, NAMA_SKU_PARENT, CATEGORY, MARK,
#          BOX / CRT, BOX / PCS, ISI, HARGA JUAL, HARGA BELI, HARGA POKOK, HARGA PROMO, HARGA DISKON, PRINCIPAL,
#          BRAND, ECERAN, DIVISI, LAUNCHING, NPL, BUSDEV, TYPE, MIX DIVISI, FLAVOUR,
#          DIVISI (6 & 7), DIVISI (SD), PRINC 2, ECERAN (KSNI), STATUS_PRODUK

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
        
        # Get parent SKU
        parent_sku_code = str(row['KD_SKU_PARENT']).strip() if pd.notna(row['KD_SKU_PARENT']) else sku_code
        
        # Parse UOM data from BOX/CRT and BOX/PCS columns
        # BOX / CRT might be like "20" meaning 20 boxes per carton
        # BOX / PCS might be like "12" meaning 12 pieces per box
        # ISI might be total pieces
        
        box_crt = row.get('BOX / CRT', None)
        box_pcs = row.get('BOX / PCS', None)
        isi = row.get('ISI', None)
        
        # Try to parse UOM values
        uom_medium = None
        isi_pcs_per_medium = None
        uom_large = None
        isi_pcs_per_large = None
        
        if pd.notna(box_pcs) and box_pcs != 0:
            uom_medium = 'BOX'
            isi_pcs_per_medium = int(box_pcs) if isinstance(box_pcs, (int, float)) else None
        
        if pd.notna(box_crt) and box_crt != 0:
            uom_large = 'KRT'
            # If we have box_pcs and box_crt, multiply them
            if isi_pcs_per_medium and isinstance(box_crt, (int, float)):
                isi_pcs_per_large = int(isi_pcs_per_medium * box_crt)
            else:
                isi_pcs_per_large = int(box_crt) if isinstance(box_crt, (int, float)) else None
        
        product = {
            'company_id': 'ID001',
            'sku_code': sku_code,
            'product_name': str(row['NAMA_SKU']).strip() if pd.notna(row['NAMA_SKU']) else None,
            'short_name': str(row.get('MARK', '')).strip() if pd.notna(row.get('MARK')) else None,
            'parent_sku_code': parent_sku_code,
            'parent_sku_name': str(row['NAMA_SKU_PARENT']).strip() if pd.notna(row['NAMA_SKU_PARENT']) else None,
            'principal_id': str(row.get('PRINC 2', '')).strip() if pd.notna(row.get('PRINC 2')) else None,
            'brand_id': str(row.get('BRAND', '')).strip() if pd.notna(row.get('BRAND')) else None,
            'category_id': str(row.get('CATEGORY', '')).strip() if pd.notna(row.get('CATEGORY')) else None,
            'variant': str(row.get('FLAVOUR', '')).strip() if pd.notna(row.get('FLAVOUR')) else None,
            'price_segment': str(row.get('ECERAN (KSNI)', '')).strip() if pd.notna(row.get('ECERAN (KSNI)')) else None,
            'uom_small': 'PCS',  # Default small UOM
            'uom_medium': uom_medium,
            'isi_pcs_per_medium': isi_pcs_per_medium,
            'uom_large': uom_large,
            'isi_pcs_per_large': isi_pcs_per_large,
            'is_active': is_active,
            'is_npl': True if row.get('NPL', '') == 'NPL' else False,
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
print(f"\n=== SAMPLE PRODUCTS (first 5) ===")
for p in products[:5]:
    print(f"\nSKU: {p['sku_code']}")
    print(f"  Name: {p['product_name']}")
    print(f"  Short: {p['short_name']}")
    print(f"  Parent: {p['parent_sku_code']} ({p['parent_sku_name']})")
    print(f"  Category: {p['category_id']}, Brand: {p['brand_id']}, Principal: {p['principal_id']}")
    print(f"  UOM: S:{p['uom_small']} M:{p['uom_medium']}({p['isi_pcs_per_medium']}) L:{p['uom_large']}({p['isi_pcs_per_large']})")
    print(f"  Active: {p['is_active']}, NPL: {p['is_npl']}")

# Count active vs inactive
active_count = sum(1 for p in products if p['is_active'])
inactive_count = len(products) - active_count
npl_count = sum(1 for p in products if p['is_npl'])

print(f"\n=== STATISTICS ===")
print(f"Active products: {active_count}")
print(f"Inactive products: {inactive_count}")
print(f"NPL products: {npl_count}")

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
            if hasattr(e, 'response') and e.response is not None:
                print(f"Error Details: {e.response.text}")
            # Optionally stop on first error to investigate
            # break
    
    print(f"\n=== IMPORT COMPLETE ===")
    print(f"Successfully imported: {success_count}")
    print(f"Errors: {error_count}")
else:
    print("\nImport cancelled.")
