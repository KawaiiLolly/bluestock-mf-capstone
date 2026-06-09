# Bluestock Capstone I — Mutual Fund Analytics
 
> **Start date:** 01 Jun 2026 &nbsp;|&nbsp; **Final due date:** 12 Jun 2026

---

## Day 1: Data Ingestion

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


## Day 2 — Data Cleaning + SQL Database

## Deliverables Checklist

- [x] `data/processed/` has 10 clean CSVs
- [x] `data/db/bluestock_mf.db` exists with 11 tables
- [x] `sql/schema.sql` defines all tables and indexes
- [x] `sql/queries.sql` has 10 working queries
- [x] `sql/data_dictionary.md` documents all columns
- [x] `reports/cleaning_report.txt` generated
---

## Day 3 — Exploratory Data Analysis (EDA)

## Deliverables Checklist

* [x] EDA completed on cleaned datasets
* [x] Multiple charts generated and saved as PNG
* [x] Key trends and insights identified
* [x] Charts stored in `reports/charts/`
---
## Day 4 - Fund Performance Analystics

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

---
## Day 5 - Dashboard

As an alternative to Power Bi, a fully functional and interactive dashboard has been developedusing Steamlit and connected to the 
cleaned CSV datasets and SQLite database. The application reproduces the same four analytical pages originally planned for Power BI while offering a lightweight, browser-based experience that is easy to run and share.
---
## Day 6 - Advanced Analytics + Risk Metrics

```bash
jupyter notebook notebooks/05_advanced_analytics.ipynb

# Fund recommender — standalone CLI
python scripts/recommender.py --risk Low
python scripts/recommender.py --risk Moderate
python scripts/recommender.py --risk High
python scripts/recommender.py --all     # for all three appetites
```

**Tasks and outputs (all in `reports/advanced/`):**

| Task | Method | Output |
|---|---|---|
| VaR (95%) + CVaR | `np.percentile(returns, 5)` | `var_cvar_report.csv` + `var_distribution_chart.png` |
| Rolling 90-day Sharpe | `rolling(90).mean() / rolling(90).std() × √252` | `rolling_sharpe_chart.png` |
| Investor cohort analysis | Group by first-transaction year | `cohort_analysis.csv` + `cohort_chart.png` |
| SIP continuation / at-risk | Avg gap > 90 days = at-risk | `sip_continuity.csv` + `sip_continuity_chart.png` |
| Fund recommender | Filter by risk_grade, rank by Sharpe | `fund_recommendations.csv` + `recommendation_chart.png` |
| Sector HHI | `Σ(weight_i²)` per equity fund | `sector_hhi.csv` + `sector_hhi_chart.png` |

**Recommender risk mapping:**

| Investor Appetite | Eligible Fund Risk Grades |
|---|---|
| Low | Low |
| Moderate | Moderate, Moderately High |
| High | High, Very High |
---