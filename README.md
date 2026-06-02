# Bluestock Capstone I — Mutual Fund Analytics
 
> **Start date:** 01 Jun 2026 &nbsp;|&nbsp; **Final due date:** 12 Jun 2026

---

## Day 1

### Prerequisites

### Step 1 — Clone / initialise the Git repository

```bash
# Option A: if the repo already exists on GitHub, clone it
git clone https://github.com/<your-org>/bluestock_mf_capstone.git
cd bluestock_mf_capstone

# Option B: start fresh locally and push to a new GitHub repo
mkdir bluestock_mf_capstone
cd bluestock_mf_capstone
git init
```

---

### Step 2 — Create the project folder structure 

Folder tree should look like this:

```
bluestock_mf_capstone/
├── data/
│   ├── raw/           ← original downloaded files
│   ├── processed/     ← cleaned, merged CSVs
│   └── db/            ← bluestock_mf.db (SQLite)  [git-ignored]
├── notebooks/
├── scripts/
├── sql/
├── dashboard/
├── reports/
└── README.md
```

---

### Step 3 — Place the 10 CSV datasets

Copy all 10 provided CSV files into `data/raw/`.

| Filename | Description |
|---|---|
| `fund_master.csv` | All AMFI scheme metadata |
| `nav_history.csv` | Historical NAV per scheme |
| `scheme_returns.csv` | 1Y / 3Y / 5Y trailing returns |
| `aum_history.csv` | AUM over time per scheme |
| `portfolio_holdings.csv` | Stock-level holdings per scheme |
| `investor_data.csv` | Investor account / transaction data |
| `benchmark_returns.csv` | Index (Nifty 100, etc.) daily returns |
| `expense_ratios.csv` | TER per scheme |
| `risk_metrics.csv` | Sharpe, Beta, SD, Sortino |
| `fund_manager.csv` | Manager names, tenure, schemes managed |

---

### Step 4 — Run data ingestion

```bash
python scripts/data_ingestion.py
```

This script will:
1. Load all 10 CSVs and print `.shape`, `.dtypes`, `.head()` for each
2. Detect anomalies (high nulls, duplicates, wrong dtypes)
3. Explore fund_master (unique fund houses, categories, risk grades)
4. Validate that every AMFI code in `fund_master` exists in `nav_history`
5. Write `reports/data_quality_report.txt`

---

### Step 5 — Fetch live NAV from mfapi.in 

```bash
python scripts/live_nav_fetch.py
```

This fetches real-time NAV history from `https://api.mfapi.in/mf/<code>` for 6 schemes:

| Scheme | AMFI Code |
|---|---|
| HDFC Top 100 Direct | 125497 |
| SBI Bluechip Direct | 119551 |
| ICICI Bluechip Direct | 120503 |
| Nippon India Large Cap Direct | 118632 |
| Axis Bluechip Direct | 119092 |
| Kotak Bluechip Direct | 120841 |

**Output files in `data/raw/`:**
```
nav_125497_HDFC_Top100_Direct.csv
nav_119551_SBI_Bluechip_Direct.csv
nav_120503_ICICI_Bluechip_Direct.csv
nav_118632_Nippon_LargeCap_Direct.csv
nav_119092_Axis_Bluechip_Direct.csv
nav_120841_Kotak_Bluechip_Direct.csv
```

**To manually test a single endpoint:**
```bash
curl https://api.mfapi.in/mf/125497
```

---

## Day 1 Deliverables Checklist

- [x] `scripts/data_ingestion.py` runs without errors
- [x] `scripts/live_nav_fetch.py` runs without errors
- [x] `requirements.txt` committed to repo
- [x] `data/raw/` contains all 10 CSVs + 6 live NAV files
- [x] `reports/data_quality_summary.txt` generated

---

