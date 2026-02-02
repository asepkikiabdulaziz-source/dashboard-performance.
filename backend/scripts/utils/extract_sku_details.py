import pandas as pd

df = pd.read_excel('_master_item.xlsx')
skus = [304949, 304937, 304947]
subset = df[df['KD_SKU'].isin(skus)]

print("=== DETAILED DATA FOR SKUs ===")
for _, row in subset.iterrows():
    print(f"SKU: {row['KD_SKU']}")
    print(f"  Name: {row['NAMA_SKU']}")
    print(f"  Parent SKU Code: {row['KD_SKU_PARENT']}")
    print(f"  Parent SKU Name: {row['NAMA_SKU_PARENT']}")
    print(f"  BOX/CRT (Large): {row['BOX / CRT']}")
    print(f"  BOX/PCS (Medium): {row['BOX / PCS']}")
    print(f"  ISI (Small): {row['ISI']}")
    print(f"  UOM 2 (Medium Name): {row.get('UOM 2', 'N/A')}")
    print(f"  UOM 3 (Large Name): {row.get('UOM 3', 'N/A')}")
    print("-" * 30)
