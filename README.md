# Bluestock Capstone I — Mutual Fund Analytics
 
> **Start date:** 01 Jun 2026 &nbsp;|&nbsp; **Final due date:** 12 Jun 2026

---

## Day 1: Data Ingestion Complete

## Deliverables Checklist

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


## Day 2 — Data Cleaning + SQL Database Complete

## Deliverables Checklist

### Day 2
- [x] `data/processed/` has 10 clean CSVs
- [x] `data/db/bluestock_mf.db` exists with 11 tables
- [x] `sql/schema.sql` defines all tables and indexes
- [x] `sql/queries.sql` has 10 working queries
- [x] `sql/data_dictionary.md` documents all columns
- [x] `reports/cleaning_report.txt` generated
---

# Day 3 — Exploratory Data Analysis (EDA)

### What it does

Performs analysis on the cleaned mutual fund dataset and generates visual insights as PNG charts.


### Output

* PNG charts saved in `reports/charts/`
* Visual insights for mutual fund trends, investor behavior, risk, returns, benchmark performance and key findings.

---

## Deliverables Checklist

* [x] EDA completed on cleaned datasets
* [x] Multiple charts generated and saved as PNG
* [x] Key trends and insights identified
* [x] Charts stored in `reports/charts/`
