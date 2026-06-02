"""
    data_ingestion.py
"""

import pandas as pd
from pathlib import Path

# PATHS
BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"

REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# LOAD DATASETS
def load_datasets(raw_dir):
    datasets = {}
    csv_files = sorted(raw_dir.glob("*.csv"))
    if not csv_files:
        print("No CSV files found in data/raw/")
        return datasets

    print(f"Found {len(csv_files)} CSV files\n")

    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path, low_memory=False)
            datasets[file_path.name] = df
            print(f"{file_path.name:<50} {df.shape[0]:>10,} rows × {df.shape[1]} cols")

        except Exception as e:
            print(f"ERROR loading {file_path.name}: {e}")
    print(f"\nLoaded {len(datasets)} dataset(s).")

    return datasets

# INSPECT DATASETS
def inspect_datasets(datasets):
    for filename, df in datasets.items():
        print("\n" + "=" * 50)
        print(f"DATASET: {filename}")
        print("=" * 50)
        print(f"\nShape:")
        print(df.shape)
        print("\nDtypes:")
        print(df.dtypes)
        print("\nNull Counts:")
        print(df.isnull().sum())
        print("\nHead:")
        print(df.head())

# FUND MASTER EXPLORATION
def explore_fund_master(datasets):
    if "01_fund_master.csv" not in datasets:
        print("\n01_fund_master.csv not found. Skipping exploration.")
        return

    fm = datasets["01_fund_master.csv"]

    print("\n" + "=" * 50)
    print("FUND MASTER OVERVIEW")
    print("=" * 50)

    print("\nFirst 3 Records:")
    print(fm.head(3))

    columns_to_explore = {
        "Fund Houses": "fund_house",
        "Categories": "category",
        "Sub-Categories": "sub_category",
        "Risk Categories": "risk_category"
    }

    for label, col in columns_to_explore.items():

        if col not in fm.columns:
            print(f"\nColumn '{col}' not found.")
            continue

        unique_values = sorted(
            fm[col].dropna().unique()
        )

        result_df = pd.DataFrame({
            label: unique_values
        })

        print("\n" + "-" * 50)
        print(label)
        print("-" * 50)

        print(f"Total Unique Values: {len(unique_values)}")
        print(result_df)

    print("\n" + "-" * 50)
    print("AMFI SCHEME CODE STRUCTURE")
    print("-" * 50)

    if "amfi_code" in fm.columns:
        print("\nSample AMFI Codes:")
        cols = ["amfi_code"]
        if "scheme_name" in fm.columns:
            cols.append("scheme_name")
        print(fm[cols].head(10))
        print("\nAMFI codes are unique numeric identifiers assigned to mutual fund schemes by AMFI.")
        print(f"\nTotal Unique AMFI Codes: {fm['amfi_code'].nunique():,}"        )

# AMFI VALIDATION

def validate_amfi_codes(datasets):
    if ("01_fund_master.csv" not in datasets or "02_nav_history.csv" not in datasets):        
        print("\n01_fund_master.csv or 02_nav_history.csv not found.")
        return None

    fm = datasets["01_fund_master.csv"]
    nav = datasets["02_nav_history.csv"]

    if ("amfi_code" not in fm.columns or  "amfi_code" not in nav.columns):
        print("\namfi_code column not found.")
        return None

    fm_codes = set(fm["amfi_code"].dropna().astype(int).unique())

    nav_codes = set(nav["amfi_code"].dropna().astype(int).unique())

    missing_in_nav = fm_codes - nav_codes
    extra_in_nav = nav_codes - fm_codes
    matched = fm_codes & nav_codes

    print("\n" + "=" * 50)
    print("AMFI CODE VALIDATION")
    print("=" * 50)

    print(f"01_fund_master total codes       : {len(fm_codes):,}")
    print(f"02_nav_history total codes       : {len(nav_codes):,}")
    print(f"Matched codes                    : {len(matched):,}")
    print(f"Missing in NAV                   : {len(missing_in_nav):,}")
    print(f"Extra in NAV                     : {len(extra_in_nav):,}")

    if missing_in_nav:
        print("\nMissing codes (first 20):")
        print(sorted(missing_in_nav)[:20])
    else:
        print("\nAll fund master AMFI codes exist in nav history.")

    return {
        "fund_master_codes": len(fm_codes),
        "nav_history_codes": len(nav_codes),
        "matched": len(matched),
        "missing": len(missing_in_nav),
        "extra": len(extra_in_nav)
    }
    
# CSV SUMMARY REPORT
def generate_summary(datasets):
    rows = []
    for name, df in datasets.items():
        high_null_cols = (
            df.columns[
                df.isnull().mean() > 0.20
            ]
            .tolist()
        )
        rows.append({
            "File": name,
            "Rows": df.shape[0],
            "Columns": df.shape[1],
            "Average Null %":
                round(
                    df.isnull()
                    .mean()
                    .mean() * 50,
                    2
                ),
            "Duplicate Rows":
                int(df.duplicated().sum()),
            "High Null Columns":
                ", ".join(high_null_cols)
                if high_null_cols else "-"
        })
    summary_df = pd.DataFrame(rows)
    output_file = (REPORTS_DIR /"data_quality_summary.csv")
    summary_df.to_csv(output_file,index=False)
    print(f"\nCSV summary saved to reports folder.")

# TXT REPORT
def write_txt_report(datasets, validation):

    report_file = REPORTS_DIR / "data_quality_report.txt"

    with open(report_file, "w", encoding="utf-8") as f:

        f.write("=" * 50 + "\n")
        f.write("BLUESTOCK MF CAPSTONE - DAY 1 DATA INGESTION REPORT\n")
        f.write("=" * 50 + "\n\n")

        f.write(f"TOTAL DATASETS LOADED: {len(datasets)}\n\n")

        f.write("-" * 50 + "\n")
        f.write("DATASET SUMMARY\n")
        f.write("-" * 50 + "\n\n")

        for name, df in datasets.items():

            f.write(f"File: {name}\n")
            f.write(f"Rows: {df.shape[0]:,}\n")
            f.write(f"Columns: {df.shape[1]}\n")
            f.write(f"Average Null %: {df.isnull().mean().mean()*50:.2f}%\n")
            f.write(f"Duplicate Rows: {df.duplicated().sum()}\n\n")

        # Fund Master Exploration
        if "01_fund_master.csv" in datasets:

            fm = datasets["01_fund_master.csv"]

            f.write("-" * 50 + "\n")
            f.write("FUND MASTER EXPLORATION\n")
            f.write("-" * 50 + "\n\n")

            columns = {
                "Unique Fund Houses": "fund_house",
                "Categories": "category",
                "Sub-Categories": "sub_category",
                "Risk Categories": "risk_category"
            }

            for label, col in columns.items():

                if col in fm.columns:

                    values = sorted(fm[col].dropna().unique())

                    f.write(f"{label} ({len(values)})\n")
                    f.write("-" * 50 + "\n")

                    for value in values:
                        f.write(f"{value}\n")

                    f.write("\n")

            # AMFI Codes
            if "amfi_code" in fm.columns:

                f.write("AMFI SCHEME CODE STRUCTURE\n")
                f.write("-" * 50 + "\n")
                f.write(
                    f"Total Unique AMFI Codes: "
                    f"{fm['amfi_code'].nunique():,}\n\n"
                )

        # Validation Results
        if validation:
            f.write("AMFI CODE VALIDATION\n")
            f.write("-" * 50 + "\n")
            f.write(f"  01_fund_master  total codes       : {validation['fund_master_codes']:,}\n")
            f.write(f"  02_nav_history  total codes       : {validation['nav_history_codes']:,}\n")
            f.write(f"  Matched (present in both)         : {validation['matched']:,}\n" )
            f.write(f"  In 01_fund_master, missing in NAV : {validation['missing']:,}\n" )
            f.write(f"  In NAV, missing in 01_fund_master : {validation['extra']:,}\n")
            
            if validation["missing"] > 0:
                f.write(f"\n  Missing codes (first 20): {validation['missing_codes'][:20]}\n")
            else:
                f.write("\n  All 01_fund_master codes are present in 02_nav_history.\n")
            f.write("\n")
        else:
            f.write("[INFO] 01_fund_master.csv or 02_nav_history.csv not loaded — skipping validation.\n")                                       

    print(f"\nTXT report saved to reports folder.")

# MAIN

def main():
    print("=" * 50)
    print("DAY 1 - DATA INGESTION")
    print("=" * 50)
    datasets = load_datasets(RAW_DIR)

    if not datasets:
        return

    inspect_datasets(datasets)
    explore_fund_master(datasets)
    validation = validate_amfi_codes(datasets)
    generate_summary(datasets)
    write_txt_report(datasets, validation)

    print("\nData ingestion completed.")


if __name__ == "__main__":
    main()