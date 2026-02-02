import pandas as pd

# Read the Excel file
df = pd.read_excel('_master_item.xlsx')

# Standardize column names
df.columns = df.columns.str.upper()

print("=== PARENT SKU HIERARCHY ANALYSIS ===\n")

# Find a parent with multiple children
parent_counts = df.groupby('KD_SKU_PARENT').size().sort_values(ascending=False)
print("Top 5 Parent SKUs with most children:")
print(parent_counts.head())

# Show example of one parent with its children
top_parent = parent_counts.index[0]
print(f"\n=== EXAMPLE: Parent SKU {top_parent} and its children ===")
family = df[df['KD_SKU_PARENT'] == top_parent][['KD_SKU', 'NAMA_SKU', 'KD_SKU_PARENT', 'NAMA_SKU_PARENT']]
print(family.to_string())

# Check if parent SKU itself exists as a product
print(f"\n=== Is parent SKU {top_parent} also a product? ===")
parent_as_product = df[df['KD_SKU'] == top_parent]
if len(parent_as_product) > 0:
    print("YES - Parent is also a product:")
    print(parent_as_product[['KD_SKU', 'NAMA_SKU', 'KD_SKU_PARENT']].to_string())
else:
    print("NO - Parent is just a grouping code, not an actual product")

# Statistics
total = len(df)
self_parent = len(df[df['KD_SKU'] == df['KD_SKU_PARENT']])
has_parent = len(df[df['KD_SKU'] != df['KD_SKU_PARENT']])

print(f"\n=== STATISTICS ===")
print(f"Total products: {total}")
print(f"Root products (self-parent): {self_parent}")
print(f"Child products (has different parent): {has_parent}")
print(f"Percentage of products with parent: {has_parent/total*100:.1f}%")
