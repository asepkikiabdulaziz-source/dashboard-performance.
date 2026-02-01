import pandas as pd

df = pd.read_excel('_master_item.xlsx')
target_skus = [304949, 304937, 304947]

# Filter specifically for these SKUs
subset = df[df['KD_SKU'].isin(target_skus)]

print("=== DATA INVESTIGATION FOR TARGET SKUs ===\n")
cols_to_show = ['KD_SKU', 'NAMA_SKU', 'KD_SKU_PARENT', 'NAMA_SKU_PARENT', 'BOX / CRT', 'BOX / PCS', 'ISI', 'STATUS_PRODUK']
print(subset[cols_to_show].to_string())

print("\n=== COLUMN TYPES ===")
print(subset[['BOX / CRT', 'BOX / PCS', 'ISI']].dtypes)
