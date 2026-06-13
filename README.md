# Bluestock Capstone I — Mutual Fund Analytics

---

## Quick Start

```bash
# 1. Clone and enter the project
git clone https://github.com/<your-org>/bluestock_mf_capstone.git
cd bluestock_mf_capstone

# 2. Create virtual environment and install dependencies
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Run the full pipeline in order
python scripts/etl_pipeline.py            # data ingestion + data cleaning + database loading
python scripts/live_nav_fetch.py          # Fetches live NAV csv
python scripts/setup_cron.py              # Setup for automation of live_nav_fetch
python scripts/run_queries.py             # Run 10 SQL queries
jupyter notebook notebooks/03_EDA_Analysis.ipynb  # 17 EDA charts
jupyter notebook notebooks/04_Performance_Analytics.ipynb  #CAGR, Sharpe, Alpha, Scorecard
jupyter notebook notebooks/05_advanced_analytics.ipynb  # VaR, Cohort, HHI
python scripts/monte_carlo_simulation.py # Monte Carlo projections
python scripts/efficient_frontier.py     #  Markowitz Frontier

# 4. Launch interactive dashboard
streamlit run dashboard/dashboard.py     

# 5. Fund recommender (CLI)
python scripts/recommender.py --risk Low
python scripts/recommender.py --risk Moderate
python scripts/recommender.py --risk High

# 6. Email Report Generator
python scripts/email_report_generator.py --html-only
python scripts/email_report_generator.py                   # credentials in .env file
python scripts/email_report_generator.py --schedule        # schedule weekly at Friday 20:00 hrs

```

---

## Project Structure

```
bluestock_mf_capstone/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── db/
│       └── bluestock_mf.db
│
├── dashboard/
│   └── dashboard.py
│
├── notebooks/
│   ├── 01_data_ingestion.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_EDA_Analysis.ipynb
│   ├── 04_Performance_Analytics.ipynb
│   └── 05_Advanced_Analytics.ipynb
│
├── scripts/
│   ├── data_cleaning.py
│   ├── data_ingestion.py
│   ├── db_loader.py
│   ├── efficient_frontier.py
│   ├── email_report_generator.py
│   ├── etl_pipeline.py
│   ├── live_nav_fetch.py
│   ├── monte_carlo_simulation.py
│   ├── recommender.py
│   ├── run_queries.py
│   └── setup_cron.py
│
├── sql/
│   ├── schema.sql
│   └── queries.sql
│
├── reports/
│   ├── Final_Report.pdf
│   ├── Bluestock_MF_Presentation.pptx
│   ├── charts/
│   ├── advanced/
│   ├── performance/
│   ├── bonus/
│   ├── email/
│   ├── query_results/
│   ├── EDA_Findings.md
│   ├── data_dictionary.md
│   ├── data_quality_report.txt
│   ├── data_quality_summary.csv
│   └── cleaning_report.txt
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Day-by-Day Workflow

### Day 1 — Data Ingestion
```bash
python scripts/data_ingestion.py    # inspect all 10 raw CSVs
python scripts/live_nav_fetch.py    # fetch 6 scheme NAVs from mfapi.in
```
**Output:** Raw data in `data/raw/` + `reports/data_quality_summary.txt`

---

### Day 2 — Data Cleaning + SQL Database
```bash
python scripts/data_cleaning.py      # clean all 10 datasets → data/processed/
python scripts/db_loader.py --fresh  # build 8-table SQLite star schema
python scripts/run_queries.py        # run 10 queries → reports/query_results/
```

**Cleaning highlights:**
- `nav_history`: Parse dates, deduplicate, `ffill()` holidays on `pd.bdate_range`, validate NAV > 0
- `investor_transactions`: Standardise types (sip→SIP), parse DD/MM/YYYY, remove negatives
- `scheme_performance`: Coerce to numeric, flag negative Sharpe, clamp expense_ratio [0.1–2.5]

**Database (8 tables, ~180K rows):** `dim_fund`, `dim_date`, `fact_nav`, `fact_transactions`, `fact_performance`, `fact_portfolio`, `fact_aum`, `fact_sip_industry`

---

### Day 3 — Exploratory Data Analysis
```bash
jupyter notebook notebooks/03_EDA_Analysis.ipynb
```
**Output:** 17 PNG charts in `reports/charts/` + `reports/EDA_Findings.md`

---

### Day 4 — Fund Performance Analytics
```bash
jupyter notebook notebooks/04_Performance_Analytics.ipynb
```

| File | Metric | Formula |
|---|---|---|
| `returns_computed.csv` | Daily + annualised return | `nav_t/nav_t-1 − 1` |
| `cagr_report.csv` | 1yr/3yr/5yr CAGR | `(NAV_end/NAV_start)^(1/n)−1` |
| `sharpe_values.csv` | Sharpe Ratio | `(Rp_ann−Rf)/(σ×√252)`, Rf=6.5% |
| `sortino_values.csv` | Sortino Ratio | Downside std only |
| `alpha_beta.csv` | Alpha & Beta | OLS vs Nifty 100 |
| `max_drawdown.csv` | Max Drawdown | `min(NAV/cummax−1)` |
| `fund_scorecard.csv` | Composite Score 0–100 | 30% CAGR + 25% Sharpe + 20% Alpha + 15% ER + 10% DD |
| `tracking_error.csv` | Tracking Error | `std(fund−benchmark)×√252` |

---

### Day 5 — Dashboard Development
```bash
# Launch Streamlit dashboard (all OS)
streamlit run dashboard/dashboard.py   
```
---

### Day 6 — Advanced Analytics
```bash
jupyter notebook notebooks/05_advanced_analytics.ipynb
python scripts/recommender.py --all    # fund recommendations by risk appetite
```

| Analysis | Method | Output |
|---|---|---|
| VaR (95%) & CVaR | `np.percentile(returns, 5)` | `var_cvar_report.csv` |
| Rolling Sharpe | `rolling(90).mean()/rolling(90).std()×√252` | `rolling_sharpe_chart.png` |
| Cohort Analysis | Group by first-transaction year | `cohort_analysis.csv` |
| SIP Continuity | Avg gap > 90 days = at-risk | `sip_continuity.csv` |
| Fund Recommender | Filter by risk_grade, rank by Sharpe | `fund_recommendations.csv` |
| Sector HHI | `Σ(weight_i²)` per equity fund | `sector_hhi.csv` |

---

### Bonus Tasks
```bash
# B1: Scheduled ETL (weekdays 20:00 IST)
python scripts/etl_scheduler.py --run-now   # test
python scripts/etl_scheduler.py             # start daemon
python scripts/setup_cron.py --install      # or OS cron (Linux/macOS)

# B2: Streamlit Web App
streamlit run dashboard/dashboard.py

# B3: Monte Carlo Simulation
python scripts/monte_carlo_simulation.py    # 1,000 paths × 5yr × 40 funds

# B4: Markowitz Efficient Frontier
python scripts/efficient_frontier.py        # MSR + MinVar portfolios

# B5: HTML Email Report
python scripts/email_report_generator.py --html-only       # HTML only (locally stored)
python scripts/email_report_generator.py                   # Need setups in .env for credentials
```

---

### Day 7 — Final Report & Presentation
- Comprehensive Final Report - reports/Final_Report.pdf
- Presentation - reports/Bluestock_MF_Presentation.pptx

---

## Key Metrics

| Metric                    | Value                           |
| ------------------------- | ------------------------------- |
| Schemes analyzed          | 40                              |
| NAV data range            | Jan 2022 – Dec 2025             |
| Total NAV rows            | 19,798                          |
| Investor transactions     | 32,778                          |
| Python scripts            | 15                              |
| Jupyter notebooks         | 6                               |
| Charts generated          | 30 PNG + 3 HTML                 |
| CSV files generated       | 24                              |
| Dashboard pages           | 4 (Streamlit + Plotly)          |
| SQL queries               | 10                              |
| Top 3-year CAGR           | 33.62% — Axis Midcap Fund       |
| Best Sharpe ratio         | 1.7298 — Mirae Asset Large Cap  |
| Peak SIP inflow           | Rs. 31,002 Crore (Dec 2025 ATH) |
| Total Industry AUM FY2025 | Rs. 117 Lakh Crore              |

---


## Requirements

```
pandas==2.2.2
numpy==1.26.4
matplotlib==3.9.0
seaborn==0.13.2
plotly==5.22.0
sqlalchemy==2.0.30
requests==2.32.3
scipy==1.13.1
jupyter==1.0.0
ipykernel==6.29.4
openpyxl==3.1.3
schedule==1.2.2
streamlit>=1.35.0
kaleido
```

Install all Python deps: `pip install -r requirements.txt`

---

## Deliverables Rubric

| ID | Deliverable           | Format           | Status                                     |
| -- | --------------------- | ---------------- | ------------------------------------------ |
| D1 | ETL pipeline          | `.py`            | `etl_pipeline.py` (data ingestion + data cleaning + database loading) + `live_nav_fetch.py` + `setup_cron`        |
| D2 | SQLite database       | `.db`            | `bluestock_mf.db` (8 tables, ~180K rows)   |
| D3 | EDA notebook          | `.ipynb`         | `03_EDA_Analysis.ipynb` (17 charts)        |
| D4 | Performance metrics   | `.ipynb` + CSVs  | `04_Performance_Analytics.ipynb` (8 CSVs)  |
| D5 | Interactive dashboard | Streamlit        | `dashboard.py` (4 pages, 2+ slicers each)  |
| D6 | Advanced analytics    | `.ipynb`         | `05_Advanced_Analytics.ipynb` (6 analyses) |
| D7 | Final report + slides | `.pdf` + `.pptx` | `Final_Report.pdf` + `Presentation.pptx`   |
| B1 | Scheduled ETL         | `.py`            | `etl_scheduler.py` + `setup_cron.py`       |
| B2 | Streamlit dashboard   | `.py`            | `dashboard/dashboard.py`                   |
| B3 | Monte Carlo           | `.py`            | `monte_carlo_simulation.py`                |
| B4 | Efficient Frontier    | `.py`            | `efficient_frontier.py`                    |
| B5 | Email report          | `.py`            | `email_report_generator.py`                |

