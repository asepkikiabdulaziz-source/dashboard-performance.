import pandas as pd

# Read the Excel file
df = pd.read_excel('_master_item.xlsx')

print("=== ANALYZING PARENT SKU USAGE ===\n")
print(f"Total products: {len(df)}")

# Check column names
print(f"\nColumns in file: {list(df.columns)}")

# Look for parent SKU related columns
parent_cols = [col for col in df.columns if 'parent' in col.lower() or 'induk' in col.lower()]
print(f"\nParent-related columns: {parent_cols}")

# Show sample data with parent SKU
if 'PARENT_SKU_CODE' in df.columns or 'parent_sku_code' in df.columns:
    parent_col = 'PARENT_SKU_CODE' if 'PARENT_SKU_CODE' in df.columns else 'parent_sku_code'
    sku_col = 'SKU_CODE' if 'SKU_CODE' in df.columns else 'sku_code'
    
    print(f"\n=== SAMPLE DATA (first 10 rows) ===")
    print(df[[sku_col, parent_col, 'PRODUCT_NAME' if 'PRODUCT_NAME' in df.columns else 'product_name']].head(10).to_string())
    
    # Check how many products have different parent SKU
    different_parent = df[df[sku_col] != df[parent_col]]
    print(f"\n=== PARENT SKU ANALYSIS ===")
    print(f"Products with DIFFERENT parent SKU: {len(different_parent)}")
    print(f"Products with SAME parent SKU (self-reference): {len(df[df[sku_col] == df[parent_col]])}")
    
    if len(different_parent) > 0:
        print(f"\n=== EXAMPLES OF PARENT-CHILD RELATIONSHIPS ===")
        print(different_parent[[sku_col, parent_col, 'PRODUCT_NAME' if 'PRODUCT_NAME' in df.columns else 'product_name']].head(10).to_string())
else:
    print("\nNo parent SKU column found!")
    print("\nShowing first 5 rows of all data:")
    print(df.head().to_string())
