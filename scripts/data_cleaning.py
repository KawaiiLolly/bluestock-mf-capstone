"""
data_cleaning.py
================

Cleans all 10 raw CSV datasets and saves them to data/processed/.
Also writes a cleaning report to reports/cleaning_report.txt.

Run:
    python scripts/data_cleaning.py

"""

import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW      = BASE_DIR / "data" / "raw"
PROC     = BASE_DIR / "data" / "processed"
REPORTS  = BASE_DIR / "reports"

PROC.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

log_lines = []
def log(msg):
    print(msg)
    log_lines.append(msg)

def divider(title):
    log("")
    log("=" * 60)
    log(f"  {title}")
    log("=" * 60)

# Clean nav_history.csv
def clean_nav():
    divider("02_nav_history.csv")
    df = pd.read_csv(RAW / "02_nav_history.csv")
    log(f"  Loaded:  {len(df):,} rows")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    bad_dates = df["date"].isna().sum()
    log(f"  Unparseable dates dropped: {bad_dates}")
    df = df.dropna(subset=["date"])
    before = len(df)
    df = df.drop_duplicates(subset=["amfi_code", "date"])
    log(f"  Duplicates removed: {before - len(df)}")
    df = df.sort_values(["amfi_code", "date"]).reset_index(drop=True)
    date_min = df["date"].min()
    date_max = df["date"].max()
    all_bdays = pd.bdate_range(date_min, date_max)

    filled = []
    for code, grp in df.groupby("amfi_code"):
        grp = grp.set_index("date").reindex(all_bdays)
        grp["amfi_code"] = code
        grp["nav"] = grp["nav"].ffill()        
        grp.index.name = "date"
        grp = grp.reset_index()
        filled.append(grp)

    df = pd.concat(filled, ignore_index=True)
    df = df.dropna(subset=["nav"])             
    invalid = (df["nav"] <= 0).sum()
    log(f"  Invalid NAV (<=0) removed: {invalid}")
    df = df[df["nav"] > 0]
    df["daily_return_pct"] = (
        df.groupby("amfi_code")["nav"].pct_change() * 100
    ).round(4)

    df["nav"] = df["nav"].round(4)
    df.to_csv(PROC / "clean_nav_history.csv", index=False)
    log(f"  Saved:   {len(df):,} rows  →  clean_nav.csv")
    return df


# Clean investor_transactions.csv
TX_MAP = {
    "sip": "SIP", "Sip": "SIP", "SIP": "SIP",
    "lumpsum": "Lumpsum", "LUMPSUM": "Lumpsum", "Lumpsum": "Lumpsum",
    "redemption": "Redemption", "REDEMPTION": "Redemption", "Redemption": "Redemption",
    "stp": "STP", "STP": "STP",
    "swp": "SWP", "SWP": "SWP",
    "switch": "Switch", "Switch": "Switch",
}

KYC_MAP = {
    "KYC Verified": "KYC Verified",
    "kyc_verified": "KYC Verified",
    "VERIFIED":     "KYC Verified",
    "Pending":      "Pending",
    "pending":      "Pending",
    "N/A":          "Pending",
}

def clean_transactions():
    divider("08_investor_transactions.csv")
    df = pd.read_csv(RAW / "08_investor_transactions.csv")
    log(f"  Loaded:  {len(df):,} rows")
    before_types = df["transaction_type"].value_counts().to_dict()
    df["transaction_type"] = df["transaction_type"].map(TX_MAP).fillna("Other")
    log(f"  transaction_type before: {before_types}")
    log(f"  transaction_type after:  {df['transaction_type'].value_counts().to_dict()}")
    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"], dayfirst=True, errors="coerce"
    )
    bad = df["transaction_date"].isna().sum()
    log(f"  Unparseable dates dropped: {bad}")
    df = df.dropna(subset=["transaction_date"])
    neg = (df["amount_inr"] <= 0).sum()
    log(f"  Negative/zero amounts removed: {neg}")
    df = df[df["amount_inr"] > 0]
    df["kyc_status"] = df["kyc_status"].map(KYC_MAP).fillna("Pending")
    log(f"  KYC status values: {df['kyc_status'].value_counts().to_dict()}")
    before = len(df)
    df = df.drop_duplicates()
    log(f"  Duplicate rows removed: {before - len(df)}")

    df.to_csv(PROC / "clean_investor_transactions.csv", index=False)
    log(f"  Saved:   {len(df):,} rows  →  clean_transactions.csv")
    return df


# Clean scheme_performance.csv
def clean_performance():
    divider("07_scheme_performance.csv")
    df = pd.read_csv(RAW / "07_scheme_performance.csv")
    log(f"  Loaded:  {len(df):,} rows")

    return_cols = ['return_1yr_pct','return_3yr_pct','return_5yr_pct','sharpe_ratio','beta',
            'alpha','std_dev_ann_pct','sortino_ratio','max_drawdown_pct']

    for col in return_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            nulls = df[col].isna().sum()
            if nulls:
                log(f"  '{col}' — {nulls} non-numeric values set to NaN")

    df["sharpe_flag"] = df["sharpe_ratio"].apply(
        lambda x: "NEGATIVE" if pd.notna(x) and x < 0 else "OK"
    )
    neg_sharpe = (df["sharpe_flag"] == "NEGATIVE").sum()
    log(f"  Negative Sharpe ratios flagged: {neg_sharpe}")

    if "expense_ratio_pct" in df.columns:
        out_of_range = ~df["expense_ratio_pct"].between(0.1, 2.5)
        log(f"  expense_ratio_pct out of [0.1, 2.5]: {out_of_range.sum()} — set to NaN")
        df.loc[out_of_range, "expense_ratio_pct"] = np.nan
    if "max_drawdown_pct" in df.columns:
        df["max_drawdown_pct"] = df["max_drawdown_pct"].clip(-1.0, 0.0)
    df.to_csv(PROC / "clean_scheme_performance.csv", index=False)
    log(f"  Saved:   {len(df):,} rows  →  clean_performance.csv")
    return df

# Clean fund_master.csv
def clean_fund_master():
    divider("01_fund_master.csv")
    df = pd.read_csv(RAW / "01_fund_master.csv")
    log(f"  Loaded:  {len(df):,} rows")
    df["amfi_code"] = pd.to_numeric(df["amfi_code"], errors="coerce")
    df = df.drop_duplicates(subset=["amfi_code"]).dropna(subset=["amfi_code"])
    df["scheme_name"] = df["scheme_name"].str.strip()
    df["fund_house"]  = df["fund_house"].str.strip()
    df.to_csv(PROC / "clean_fund_master.csv", index=False)
    log(f"  Saved: {len(df):,} rows  →  clean_fund_master.csv")
    return df

# Clean aum_by_fund_house.csv
def clean_aum():
    divider("03_aum_by_fund_house.csv")
    df = pd.read_csv(RAW / "03_aum_by_fund_house.csv")
    log(f"  Loaded:  {len(df):,} rows")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["aum_crore"] = pd.to_numeric(df["aum_crore"], errors="coerce")
    df = df.dropna(subset=["fund_house", "date", "aum_crore"])
    df = df[df["aum_crore"] > 0]
    df = df.drop_duplicates(subset=["fund_house", "date"])
    df = df.sort_values(["fund_house", "date"]).reset_index(drop=True)
    df.to_csv(PROC / "clean_aum_by_fund_house.csv", index=False)
    log(f"  Saved: {len(df):,} rows  →  clean_aum_by_fund_house.csv")
    return df

# Clean portfolio_holdings.csv
def clean_holdings():
    divider("09_portfolio_holdings.csv")
    df = pd.read_csv(RAW / "09_portfolio_holdings.csv")
    log(f"  Loaded:  {len(df):,} rows")
    df["weight_pct"] = pd.to_numeric(df["weight_pct"], errors="coerce")
    df["portfolio_date"]=pd.to_datetime(df["portfolio_date"], errors="coerce")
    df = df.dropna(subset=["amfi_code", "stock_symbol"])
    df = df.drop_duplicates(subset=["amfi_code", "stock_symbol"])
    # Weight must be 0–100
    df = df[df["weight_pct"].between(0, 100)]
    df.to_csv(PROC / "clean_portfolio_holdings.csv", index=False)
    log(f"  Saved: {len(df):,} rows  →  clean_portfolio_holdings.csv")
    return df

# Clean montly_sip_inflows.csv
def clean_sip_industry():
    divider("04_monthly_sip_inflows.csv")
    df = pd.read_csv(RAW / "04_monthly_sip_inflows.csv")
    log(f"  Loaded:  {len(df):,} rows")
    df["month"] = pd.to_datetime(df["month"], errors="coerce")
    for col in ["sip_inflow_crore", "active_sip_accounts_crore", "new_sip_accounts_lakh", "sip_aum_lakh_crore", "yoy_growth_pct"]:
        if col in df.columns:
            df[col]=pd.to_numeric(df[col], errors="coerce")
    df = df.dropna()
    df = df.drop_duplicates(subset=["month"])
    df = df.sort_values("month").reset_index(drop=True)
    df.to_csv(PROC / "clean_monthly_sip_inflows.csv", index=False)
    log(f"  Saved: {len(df):,} rows  →  clean_monthly_sip_inflows.csv")
    return df

# Clean category_inflows.csv
def clean_category_inflows():
    divider("05_category_inflows.csv")
    df = pd.read_csv(RAW / "05_category_inflows.csv")
    log(f"  Loaded:  {len(df):,} rows")
    df["month"] = pd.to_datetime(df["month"])
    df["net_inflow_crore"] = pd.to_numeric(df["net_inflow_crore"], errors="coerce" )
    df = df.drop_duplicates()
    df.to_csv(PROC / "clean_category_inflows.csv",index=False)
    log(f"  Saved: {len(df):,} rows  →  clean_category_inflows.csv")
    return df

# Clean industry_folio_count.csv
def clean_folio_count():
    divider("06_industry_folio_count.csv")
    df = pd.read_csv(RAW / "06_industry_folio_count.csv")
    log(f"  Loaded:  {len(df):,} rows")
    df["month"] = pd.to_datetime(df["month"])
    df = df.drop_duplicates()
    df.to_csv(PROC / "clean_industry_folio_count.csv",index=False)
    log(f"  Saved: {len(df):,} rows  →  clean_industry_folio_count.csv")
    
    return df

# Clean benchmark_indices.csv
def clean_benchmarks():
    divider("10_benchmark_indices.csv")
    df = pd.read_csv(RAW / "10_benchmark_indices.csv")
    log(f"  Loaded:  {len(df):,} rows")
    df["date"] = pd.to_datetime(df["date"])
    df["close_value"] = pd.to_numeric(df["close_value"], errors="coerce")
    df = df.drop_duplicates()
    df.to_csv(PROC / "clean_benchmark_indicies.csv", index=False)
    log(f"  Saved: {len(df):,} rows  →  clean_benchmark_indices.csv")
    return df

# Writing final report on cleaning
def write_report():
    report_path = REPORTS / "cleaning_report.txt"
    header = [
        "=" * 60,
        "  Bluestock MF Capstone — Cleaning Report",
        "  Day 2",
        "=" * 60,
    ]
    report_path.write_text("\n".join(header + log_lines), encoding="utf-8")
    print(f"\n  Report saved → {report_path}")

# Main
def main():
    log("=" * 60)
    log("  Bluestock MF — Data Cleaning (Day 2)")
    log("=" * 60)

    clean_nav()
    clean_transactions()
    clean_performance()
    clean_fund_master()
    clean_aum()
    clean_holdings()
    clean_sip_industry()
    clean_category_inflows()
    clean_folio_count()
    clean_benchmarks()


    write_report()

    log("")
    log("All 10 datasets cleaned → data/processed/")
    log("=" * 60)


if __name__ == "__main__":
    main()
