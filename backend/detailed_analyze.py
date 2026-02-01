
import pandas as pd
import os

def detailed_excel_analysis():
    file_path = "d:/PROJECT/dashboard-performance/_master_item.xlsx"
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    df = pd.read_excel(file_path)
    print("FULL COLUMN LIST:")
    print(df.columns.tolist())
    print("\nSAMPLE DATA (1 row):")
    print(df.iloc[0].to_dict())
    print(f"\nROW COUNT: {len(df)}")
    
    # Check for empty/null values in key columns
    print("\nNULL COUNTS:")
    print(df.isnull().sum())

if __name__ == "__main__":
    detailed_excel_analysis()
