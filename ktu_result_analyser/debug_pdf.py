from utils.pdf_processor import process_pdf
import os

pdf_path = r"c:\Users\anish\Documents\ktu\ktu_result_analyser\uploads\result_BMC (58).pdf"

if not os.path.exists(pdf_path):
    print(f"File not found: {pdf_path}")
else:
    print("Processing PDF...")
    df, stats = process_pdf(pdf_path)
    
    if df is not None:
        print("--- DataFrame Head ---")
        print(df.head())
        print("\n--- Departments Found ---")
        print(df['Dept'].unique())
        print("\n--- Stats ---")
        print(stats['dept_stats'])
    else:
        print("No data extracted.")
