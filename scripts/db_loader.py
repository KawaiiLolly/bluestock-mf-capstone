"""
db_loader.py
============

Run:
    python scripts/db_loader.py

    # Rebuild from scratch
    python scripts/db_loader.py --fresh

Output:
    data/db/bluestock_mf.db
"""

import sys
import argparse
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).resolve().parent.parent
PROC     = BASE_DIR / "data" / "processed"
DB_DIR   = BASE_DIR / "data" / "db"
SQL_DIR  = BASE_DIR / "sql"
REPORTS  = BASE_DIR / "reports"

DB_DIR.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

DB_PATH     = DB_DIR / "bluestock_mf.db"
SCHEMA_PATH = SQL_DIR / "schema.sql"

def log(msg):
    print(msg)

# Apply schema.sql
def apply_schema(engine):
    log("\n  Applying schema from schema.sql ...")
    ddl = SCHEMA_PATH.read_text(encoding="utf-8")
    statements = [s.strip() for s in ddl.split(";") if s.strip()]
    with engine.connect() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
        conn.commit()
    log("  Schema applied.")


def drop_all(engine):
    tables = [
        "fact_sip_industry", "fact_aum", "fact_portfolio",
        "fact_performance", "fact_transactions", "fact_nav",
        "dim_date", "dim_fund"
    ]
    with engine.connect() as conn:
        for t in tables:
            conn.execute(text(f"DROP TABLE IF EXISTS {t}"))
        conn.commit()
    log("  All tables dropped.")


# Build dim_date (generated, not from CSV)
def build_dim_date(engine):
    log("\n  Building dim_date ...")
    nav = pd.read_csv(
        PROC / "clean_nav_history.csv"
    )
    nav["date"] = pd.to_datetime(nav["date"])
    dates = pd.date_range(
        nav["date"].min(),
        nav["date"].max()
    )
    rows = []
    for d in dates:
        rows.append({
            "date":       d.strftime("%Y-%m-%d"),
            "year":       d.year,
            "month":      d.month,
            "quarter":    d.quarter,
            "month_name": d.strftime("%B"),
            "is_weekday": 1 if d.weekday() < 5 else 0,
        })

    df = pd.DataFrame(rows)
    df.to_sql("dim_date", engine, if_exists="append", index=False)
    log(f"  dim_date loaded: {len(df):,} rows")
    return df


# Step 3 — Load each table
def load(engine, csv_name, table, transform_fn=None, chunk=5000):
    path = PROC / csv_name
    if not path.exists():
        log(f"  [SKIP] {csv_name} not found.")
        return 0

    df = pd.read_csv(path, low_memory=False)

    if transform_fn:
        df = transform_fn(df)

    df.to_sql(table, engine, if_exists="append", index=False, chunksize=chunk)
    log(f"  {csv_name:<35} → {table:<25}  {len(df):>8,} rows")
    return len(df)


# Per-table transform functions
def transform_dim_fund(df):
    df["amfi_code"] = df["amfi_code"].astype(str)
    aum_df=pd.read_csv(PROC/"clean_aum_by_fund_house.csv")
    aum_df["date"]=pd.to_datetime(aum_df["date"])
    lastest_aum=(aum_df.sort_values("date")
                 .groupby("fund_house", as_index=False)
                 .last()[["fund_house", "aum_crore"]]
                 )
    df=df.merge(lastest_aum, on="fund_house", how="left")
    df=df.rename(columns={
        "risk_category":"risk_grade",
        "expense_ratio_pct":"expense_ratio"
    })
    keep = ["amfi_code","scheme_name","fund_house","category","sub_category",
            "risk_grade","benchmark","launch_date","fund_manager",
            "aum_crore","expense_ratio","exit_load_pct"]
    return df[[c for c in keep if c in df.columns]]

def transform_fact_nav(df):
    df["amfi_code"] = df["amfi_code"].astype(str)
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    keep = ["amfi_code","date","nav","daily_return_pct"]
    return df[[c for c in keep if c in df.columns]]

def transform_fact_transactions(df):
    df["amfi_code"] = df["amfi_code"].astype(str)
    df["transaction_date"] = pd.to_datetime(df["transaction_date"],errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.rename(columns={
        "transaction_date": "date",
        "transaction_type": "type",
        "amount_inr": "amount"
    })
    keep = [
        "investor_id", "amfi_code", "date", "type", "amount", "state",
        "city", "city_tier","age_group", "gender", "annual_income_lakh",
        "payment_mode","kyc_status"]
    return df[[c for c in keep if c in df.columns]]

def transform_fact_performance(df):
    df["amfi_code"] = df["amfi_code"].astype(str)
    df = df.rename(columns={
        "return_1yr_pct": "return_1yr",
        "return_3yr_pct": "return_3yr",
        "return_5yr_pct": "return_5yr",
        "sharpe_ratio": "sharpe",
        "std_dev_ann_pct": "std_deviation",
        "max_drawdown_pct": "max_drawdown",
        "expense_ratio_pct": "expense_ratio"
    })
    df["as_of_date"] = "2024-03-31"
    keep = ["amfi_code","as_of_date","return_1yr",  "return_3yr", "return_5yr",
        "sharpe", "alpha",  "beta",  "max_drawdown", 
        "std_deviation", "expense_ratio", "sharpe_flag"  ]
    return df[[c for c in keep if c in df.columns]]

def transform_fact_portfolio(df):
    df["amfi_code"] = df["amfi_code"].astype(str)
    df = df.rename(columns={"portfolio_date": "date"})
    keep = ["amfi_code","stock_symbol","weight_pct","sector","date","isin"]
    return df[[c for c in keep if c in df.columns]]

def transform_fact_aum(df):
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    keep = ["fund_house","date","aum_crore","num_schemes"]
    return df[[c for c in keep if c in df.columns]]

def transform_fact_sip(df):
    df["month"] = pd.to_datetime(df["month"], errors="coerce").dt.strftime("%Y-%m-%d")
    df=df.rename(columns={"active_sip_accounts_crore":"sip_accounts_crore"})
    keep = ["month","sip_inflow_crore","sip_accounts_crore"]
    return df[[c for c in keep if c in df.columns]]

def transform_fact_benchmark_indices(df):
    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    keep = ["date","index_name","close_value"]
    return df[[c for c in keep if c in df.columns]]

def transform_fact_category_inflows(df):
    df["month"] = pd.to_datetime( df["month"],errors="coerce" ).dt.strftime("%Y-%m-%d")
    keep = ["month", "category", "net_inflow_crore"]
    return df[[c for c in keep if c in df.columns]]

def transform_fact_industry_folio_count(df):
    df["month"] = pd.to_datetime(df["month"], errors="coerce" ).dt.strftime("%Y-%m-%d")
    keep = [ "month", "total_folios_crore", "equity_folios_crore",
        "debt_folios_crore",  "hybrid_folios_crore", "others_folios_crore" ]
    return df[[c for c in keep if c in df.columns]]

# Verify row counts
def verify(engine):
    tables = ["dim_fund",
    "dim_date",
    "fact_nav",
    "fact_transactions",
    "fact_performance",
    "fact_portfolio",
    "fact_aum",
    "fact_sip_industry",
    "fact_benchmark_indices",
    "fact_category_inflows",
    "fact_industry_folio_count"]
    log("\n" + "-" * 50)
    log("  Database verification")
    log("-" * 50)
    total = 0
    with engine.connect() as conn:
        for t in tables:
            n = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            log(f"  {t:<28}  {n:>8,} rows")
            total += n
    log("-" * 50)
    log(f"  {'TOTAL':<28}  {total:>8,} rows")



# Main
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fresh", action="store_true",
                        help="Drop all tables before loading.")
    args = parser.parse_args()

    log("=" * 50)
    log("  Bluestock MF — DB Loader (Day 2)")
    log(f"  DB: {DB_PATH}")
    log("=" * 50)

    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

    if args.fresh and DB_PATH.exists():
        drop_all(engine)

    apply_schema(engine)

    log("\n  Loading dimension tables ...")
    load(engine, "clean_fund_master.csv", "dim_fund",   transform_dim_fund)
    build_dim_date(engine)

    log("\n  Loading fact tables ...")
    load(engine, "clean_nav_history.csv",            "fact_nav",          transform_fact_nav,          chunk=10000)
    load(engine, "clean_investor_transactions.csv",   "fact_transactions", transform_fact_transactions)
    load(engine, "clean_scheme_performance.csv",    "fact_performance",  transform_fact_performance)
    load(engine, "clean_portfolio_holdings.csv",       "fact_portfolio",    transform_fact_portfolio)
    load(engine, "clean_aum_by_fund_house.csv",            "fact_aum",          transform_fact_aum)
    load(engine, "clean_monthly_sip_inflows.csv",   "fact_sip_industry", transform_fact_sip)
    load(engine, "clean_benchmark_indicies.csv","fact_benchmark_indices",transform_fact_benchmark_indices)
    load(engine, "clean_category_inflows.csv", "fact_category_inflows", transform_fact_category_inflows)
    load(engine, "clean_industry_folio_count.csv", "fact_industry_folio_count", transform_fact_industry_folio_count)
   
    verify(engine)
    log("\n" + "=" * 50)
    log(f"  Database ready → {DB_PATH}")
    log("=" * 50)


if __name__ == "__main__":
    main()
