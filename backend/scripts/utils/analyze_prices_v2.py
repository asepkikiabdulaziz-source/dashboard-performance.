
import pandas as pd
import os

def analyze_prices():
    file_path = "d:/PROJECT/dashboard-performance/_master_item.xlsx"
    if not os.path.exists(file_path):
        return
    
    df = pd.read_excel(file_path)
    cols = ['ECERAN', 'ECERAN (KSNI)', 'ISI', 'BOX / CRT', 'BOX / PCS']
    print("ANALYSIS OF POTENTIAL NUMERIC COLS:")
    for col in cols:
        if col in df.columns:
            print(f"\nCol: {col}")
            print(f"Dtype: {df[col].dtype}")
            print(f"Unique sample values: {df[col].unique()[:5]}")
            # Try to see if it can be numeric
            try:
                num_vals = pd.to_numeric(df[col], errors='coerce')
                print(f"Valid numeric count: {num_vals.notnull().sum()} / {len(df)}")
            except:
                print("Cannot convert to numeric easily")

if __name__ == "__main__":
    analyze_prices()
