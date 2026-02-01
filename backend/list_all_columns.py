"""
Show all columns in _master_item.xlsx
"""
import pandas as pd

df = pd.read_excel('_master_item.xlsx')

print("=== ALL COLUMNS ===\n")
for i, col in enumerate(df.columns, 1):
    print(f"{i:2d}. {col}")

print(f"\n=== SAMPLE ROW (first product) ===\n")
first_row = df.iloc[0]
for col in df.columns:
    print(f"{col:30} = {first_row[col]}")
