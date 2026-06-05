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

- [x] `data/processed/` has 10 clean CSVs
- [x] `data/db/bluestock_mf.db` exists with 11 tables
- [x] `sql/schema.sql` defines all tables and indexes
- [x] `sql/queries.sql` has 10 working queries
- [x] `sql/data_dictionary.md` documents all columns
- [x] `reports/cleaning_report.txt` generated
---

# Day 3 — Exploratory Data Analysis (EDA)

## Deliverables Checklist

* [x] EDA completed on cleaned datasets
* [x] Multiple charts generated and saved as PNG
* [x] Key trends and insights identified
* [x] Charts stored in `reports/charts/`

# Day 4 - Fund Performance Analystics

### What it does
Computes all key risk/return metrices for all 40 schemes using actual NAV history.

### Open the notebook
```bash
jupyter notebook notebooks/04_performance_analystics.ipynb
```
### Deliverables Metrics computed

| Task | Formula | Output File |
|---|---|---|
| Daily returns | `nav_t / nav_t-1 − 1` | `returns_computed.csv` |
| CAGR 1yr/3yr/5yr | `(NAV_end/NAV_start)^(1/n)−1` | `cagr_report.csv` |
| Sharpe Ratio | `(Rp_ann − Rf) / (Std × √252)` | `sharpe_values.csv` |
| Sortino Ratio | `(Rp_ann − Rf) / (Downside_Std × √252)` | `sortino_values.csv` |
| Alpha & Beta | OLS regression vs Nifty 100 | `alpha_beta.csv` |
| Max Drawdown | `min(NAV / cummax(NAV) − 1)` | `max_drawdown.csv` |
| Fund Scorecard | Weighted composite 0–100 | `fund_scorecard.csv` |
| Benchmark comparison | Normalised to 100, tracking error | `benchmark_comparison.png` |

### Output locations
```
reports/performance/            - all CSV metric files
reports/charts/                 - PNG charts including benchmark_comparion.png
```