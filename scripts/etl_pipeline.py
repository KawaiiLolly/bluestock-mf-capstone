"""
    etl_pipeline.py
    
    1. Data Ingestion
    2. Data Cleaning
    3. Database Load
    
    Usage:
    # Normal
    python scripts/etl_pipeline.py
    
    # Rebuild the databse from scratch
    python scripts/etl_pipeline.py --fresh-db
"""

import sys
import time
import argparse
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import data_ingestion
import data_cleaning
import db_loader

def print_divider():
    print("=" * 80)

def print_step(number, total, title):
    print(f"\n[{number}/{total}] {title}")
    print("-" * 50)


def run_pipeline(fresh_db):

    total_steps = 3
    pipeline_start = time.time()

    print_divider()
    print("  Bluestock MF — ETL Pipeline")
    print_divider()

    # Data Ingestion
    print_step(1, total_steps, "Data Ingestion")

    step_start = time.time()
    data_ingestion.main()
    step_time = round(time.time() - step_start, 2)

    print(f"\n  Step 1 done in {step_time}s")

    # Data Cleaning
    print_step(2, total_steps, "Data Cleaning")

    step_start = time.time()
    data_cleaning.main()
    step_time = round(time.time() - step_start, 2)

    print(f"\n  Step 2 done in {step_time}s")

    # Databse Load
    print_step(3, total_steps, "Database Load")

    step_start = time.time()

    from sqlalchemy import create_engine

    BASE_DIR = SCRIPTS_DIR.parent
    DB_DIR   = BASE_DIR / "data" / "db"
    DB_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH  = DB_DIR / "bluestock_mf.db"

    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

    # Drop all tables first if --fresh-db flag was used
    if fresh_db and DB_PATH.exists():
        print("  --fresh-db flag detected, dropping existing tables...")
        db_loader.drop_all(engine)

    db_loader.apply_schema(engine)

    # Load dimension tables
    db_loader.load(engine, "clean_fund_master.csv",  "dim_fund",  db_loader.transform_dim_fund)
    db_loader.build_dim_date(engine)

    # Load fact tables
    db_loader.load(engine, "clean_nav_history.csv",           "fact_nav",                  db_loader.transform_fact_nav, chunk=10000)
    db_loader.load(engine, "clean_investor_transactions.csv", "fact_transactions",         db_loader.transform_fact_transactions)
    db_loader.load(engine, "clean_scheme_performance.csv",    "fact_performance",          db_loader.transform_fact_performance)
    db_loader.load(engine, "clean_portfolio_holdings.csv",    "fact_portfolio",            db_loader.transform_fact_portfolio)
    db_loader.load(engine, "clean_aum_by_fund_house.csv",     "fact_aum",                  db_loader.transform_fact_aum)
    db_loader.load(engine, "clean_monthly_sip_inflows.csv",   "fact_sip_industry",         db_loader.transform_fact_sip)
    db_loader.load(engine, "clean_benchmark_indices.csv",     "fact_benchmark_indices",    db_loader.transform_fact_benchmark_indices)
    db_loader.load(engine, "clean_category_inflows.csv",      "fact_category_inflows",     db_loader.transform_fact_category_inflows)
    db_loader.load(engine, "clean_industry_folio_count.csv",  "fact_industry_folio_count", db_loader.transform_fact_industry_folio_count)

    db_loader.verify(engine)

    step_time = round(time.time() - step_start, 2)
    print(f"\n  Step 3 done in {step_time}s")

    # Done
    total_time = round(time.time() - pipeline_start, 2)

    print()
    print_divider()
    print("  All steps completed successfully!")
    print(f"  Total time: {total_time}s")
    print(f"  Database saved at: {DB_PATH}")
    print_divider()

def main():
    parser = argparse.ArgumentParser(description="ETL Pipeline")
    parser.add_argument(
        "--fresh-db",
        action="store_true",
        help="Drop all tables and rebuild the database from scratch"
    )
    args = parser.parse_args()

    run_pipeline(fresh_db=args.fresh_db)


if __name__ == "__main__":
    main()

