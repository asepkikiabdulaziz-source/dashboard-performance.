import pandas as pd
import json

df = pd.read_excel('_master_item.xlsx')
target_skus = [304949, 304937, 304947]

subset = df[df['KD_SKU'].isin(target_skus)]

print("=== TARGET SKU DATA (JSON) ===")
# Convert to dict for clean output
data = subset.to_dict(orient='records')
print(json.dumps(data, indent=2))
