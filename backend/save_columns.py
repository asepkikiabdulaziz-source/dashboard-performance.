"""
Save all column names to a text file for review
"""
import pandas as pd

df = pd.read_excel('_master_item.xlsx')

with open('excel_columns.txt', 'w', encoding='utf-8') as f:
    f.write("=== ALL COLUMNS IN _master_item.xlsx ===\n\n")
    f.write(f"Total columns: {len(df.columns)}\n\n")
    
    for i, col in enumerate(df.columns, 1):
        f.write(f"{i:3d}. {col}\n")
    
    f.write(f"\n\n=== SAMPLE DATA (First Row) ===\n\n")
    first = df.iloc[0]
    for col in df.columns:
        value = first[col]
        if pd.notna(value):
            f.write(f"{col:35} = {value}\n")

print("Column list saved to excel_columns.txt")
print(f"Total columns found: {len(df.columns)}")
