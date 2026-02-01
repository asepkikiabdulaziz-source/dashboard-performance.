"""
List ALL columns clearly from _master_item.xlsx
"""
import pandas as pd

df = pd.read_excel('_master_item.xlsx')

print("=== ALL COLUMNS IN EXCEL FILE ===\n")
print(f"Total columns: {len(df.columns)}\n")

for i, col in enumerate(df.columns, 1):
    print(f"{i:3d}. {col}")

print(f"\n\n=== FIRST ROW DATA ===\n")
first = df.iloc[0]
for col in df.columns:
    value = first[col]
    if pd.notna(value):
        print(f"{col:30} = {value}")
