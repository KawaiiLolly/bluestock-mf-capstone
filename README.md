# Bluestock Capstone I — Mutual Fund Analytics
 
> **Start date:** 01 Jun 2026 &nbsp;|&nbsp; **Final due date:** 12 Jun 2026

---

## Day 1: Data Ingestion Complete

---

## Day 1 Deliverables Checklist

- [x] `scripts/data_ingestion.py` runs without errors
- [x] `scripts/live_nav_fetch.py` runs without errors
- [x] `requirements.txt` committed to repo
- [x] `data/raw/` contains all 10 CSVs + 6 live NAV files
- [x] `reports/data_quality_summary.txt` generated

---

## Scheduled ETL (auto-fetch NAV at 20:00 weekdays)

** OS cron job (Linux/macOS only)**
```bash
python scripts/setup_cron.py --install   # add cron entry
python scripts/setup_cron.py --show      # verify
python scripts/setup_cron.py --remove    # uninstall
```
Cron entry: `TZ=Asia/Kolkata 0 20 * * 1-5 python scripts/live_nav_fetch.py`

---


## Day 2 — Data Cleaning + SQL Database

### What it does
Cleans all 10 raw datasets, designs a 7-table SQLite star schema,
loads all data into the database, and runs 10 analytics queries.

### Steps

**Step 1 — Run data cleaning**
```bash
python scripts/data_cleaning.py
```

What happens inside:
- `02_nav_history.csv` → parse dates, remove duplicates, ffill holidays, validate NAV > 0, compute daily return %
- `08_investor_transactions.csv` → standardise transaction types (sip→SIP), fix date format (DD/MM/YYYY), remove negative amounts, normalise KYC status
- `07_scheme_performance.csv` → coerce to numeric, flag negative Sharpe, clamp expense_ratio to [0.1, 2.5]
- All other 7 CSVs → type coercion, null drops, duplicate removal

Output: 10 clean CSVs in `data/processed/` + `reports/cleaning_report.txt`

**Step 2 — Load into SQLite**
```bash
python scripts/db_loader.py --fresh
```

What happens inside:
- Reads `sql/schema.sql` and creates 8 tables
- Loads `dim_fund` (40 rows) and generates `dim_date` (1,500+ rows)
- Loads all 6 fact tables in FK-safe order
- Prints row count verification table

Output: `data/db/bluestock_mf.db`

**Step 3 — Run 10 SQL queries**
```bash
python scripts/run_queries.py
```

Runs all queries from `sql/queries.sql`, prints results to console, saves each result as a CSV to `reports/query_results/`.

---

## Database Schema (Star Schema)

Check data_dictionary.md for detailed information.

---

## Deliverables Checklist

### Day 2
- [x] `data/processed/` has 10 clean CSVs
- [x] `data/db/bluestock_mf.db` exists with 11 tables
- [x] `sql/schema.sql` defines all tables and indexes
- [x] `sql/queries.sql` has 10 working queries
- [x] `sql/data_dictionary.md` documents all columns
- [x] `reports/cleaning_report.txt` generated
---
