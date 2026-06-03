# Data Dictionary

## Bluestock Capstone I — Mutual Fund Analytics

**Day 2 Deliverable — SQLite Star Schema & Data Loading**

---

# Database Overview

**Database File:** `data/db/bluestock_mf.db`

**Schema Type:** Star Schema

**Dimensions:** 2

**Fact Tables:** 9

```
dim_fund
 ├── fact_nav
 ├── fact_transactions
 ├── fact_performance
 ├── fact_portfolio

dim_date
 └── fact_nav

fact_aum
fact_sip_industry
fact_benchmark_indices
fact_category_inflows
fact_industry_folio_count
```

---

# Table: dim_fund

**Type:** Dimension

**Source:** `clean_fund_master.csv`

**Rows:** 40

**Primary Key:** `amfi_code`

| Column        | Type |
| ------------- | ---- |
| amfi_code     | TEXT |
| scheme_name   | TEXT |
| fund_house    | TEXT |
| category      | TEXT |
| sub_category  | TEXT |
| risk_grade    | TEXT |
| benchmark     | TEXT |
| launch_date   | TEXT |
| fund_manager  | TEXT |
| aum_crore     | REAL |
| expense_ratio | REAL |
| exit_load_pct | REAL |

### Notes

* `amfi_code` uniquely identifies a mutual fund scheme.
* `aum_crore` contains the latest available AMC-level AUM mapped using `fund_house`.
* Text fields were cleaned and standardized.
* Duplicate AMFI codes were removed.

---

# Table: dim_date

**Type:** Dimension

**Source:** Generated from NAV history dates

**Rows:** 1,608

**Primary Key:** `date_id`

| Column     | Type    |
| ---------- | ------- |
| date_id    | INTEGER |
| date       | TEXT    |
| year       | INTEGER |
| month      | INTEGER |
| quarter    | INTEGER |
| month_name | TEXT    |
| is_weekday | INTEGER |

### Notes

Generated programmatically from the minimum and maximum NAV dates.

---

# Table: fact_nav

**Type:** Fact

**Source:** `clean_nav_history.csv`

**Rows:** 46,000

**Primary Key:** `nav_id`

**Foreign Keys**

* `amfi_code → dim_fund(amfi_code)`
* `date → dim_date(date)`

| Column           | Type    |
| ---------------- | ------- |
| nav_id           | INTEGER |
| amfi_code        | TEXT    |
| date             | TEXT    |
| nav              | REAL    |
| daily_return_pct | REAL    |

### Notes

Stores daily Net Asset Value history for each scheme.

---

# Table: fact_transactions

**Type:** Fact

**Source:** `clean_investor_transactions.csv`

**Rows:** 13,048

| Column             | Type    |
| ------------------ | ------- |
| investor_id        | INTEGER |
| amfi_code          | TEXT    |
| date               | TEXT    |
| type               | TEXT    |
| amount             | REAL    |
| state              | TEXT    |
| city               | TEXT    |
| city_tier          | TEXT    |
| age_group          | TEXT    |
| gender             | TEXT    |
| annual_income_lakh | REAL    |
| payment_mode       | TEXT    |
| kyc_status         | TEXT    |

### Notes

* `transaction_date` renamed to `date`
* `transaction_type` renamed to `type`
* `amount_inr` renamed to `amount`
* Used for investor behavior analysis

---

# Table: fact_performance

**Type:** Fact

**Source:** `clean_scheme_performance.csv`

**Rows:** 40

**Unique Constraint**

`(amfi_code, as_of_date)`

| Column        | Type    |
| ------------- | ------- |
| perf_id       | INTEGER |
| amfi_code     | TEXT    |
| as_of_date    | TEXT    |
| return_1yr    | REAL    |
| return_3yr    | REAL    |
| return_5yr    | REAL    |
| sharpe        | REAL    |
| alpha         | REAL    |
| beta          | REAL    |
| max_drawdown  | REAL    |
| std_deviation | REAL    |
| expense_ratio | REAL    |
| sharpe_flag   | TEXT    |

### Notes

Contains risk and return metrics for each scheme.

---

# Table: fact_portfolio

**Type:** Fact

**Source:** `clean_portfolio_holdings.csv`

**Rows:** 322

| Column       | Type    |
| ------------ | ------- |
| portfolio_id | INTEGER |
| amfi_code    | TEXT    |
| stock_symbol | TEXT    |
| weight_pct   | REAL    |
| sector       | TEXT    |
| date         | TEXT    |
| isin         | TEXT    |

### Notes

Stores scheme portfolio holdings and sector allocations.

---

# Table: fact_aum

**Type:** Fact

**Source:** `clean_aum_by_fund_house.csv`

**Rows:** 90

| Column      | Type    |
| ----------- | ------- |
| aum_id      | INTEGER |
| fund_house  | TEXT    |
| date        | TEXT    |
| aum_crore   | REAL    |
| num_schemes | INTEGER |

### Notes

Monthly AMC-level Assets Under Management.

---

# Table: fact_sip_industry

**Type:** Fact

**Source:** `clean_monthly_sip_inflows.csv`

**Rows:** 36

| Column             | Type    |
| ------------------ | ------- |
| sip_id             | INTEGER |
| month              | TEXT    |
| sip_inflow_crore   | REAL    |
| sip_accounts_crore | REAL    |

### Notes

Industry-wide SIP inflows and active SIP accounts.

---

# Table: fact_benchmark_indices

**Type:** Fact

**Source:** `clean_benchmark_indicies.csv`

**Rows:** 8,050

| Column      | Type |
| ----------- | ---- |
| date        | TEXT |
| index_name  | TEXT |
| close_value | REAL |

### Notes

Historical benchmark index closing values used for performance comparisons.

---

# Table: fact_category_inflows

**Type:** Fact

**Source:** `clean_category_inflows.csv`

**Rows:** 144

| Column           | Type |
| ---------------- | ---- |
| month            | TEXT |
| category         | TEXT |
| net_inflow_crore | REAL |

### Notes

Monthly category-wise mutual fund inflows and outflows.

---

# Table: fact_industry_folio_count

**Type:** Fact

**Source:** `clean_industry_folio_count.csv`

**Rows:** 36

| Column              | Type |
| ------------------- | ---- |
| month               | TEXT |
| total_folios_crore  | REAL |
| equity_folios_crore | REAL |
| debt_folios_crore   | REAL |
| hybrid_folios_crore | REAL |
| others_folios_crore | REAL |

### Notes

Monthly industry folio statistics segmented by category.

---

# Common Joins

## NAV History With Fund Details

```sql
SELECT d.scheme_name,
       n.date,
       n.nav
FROM dim_fund d
JOIN fact_nav n
ON d.amfi_code = n.amfi_code;
```

## Performance Metrics With Fund Metadata

```sql
SELECT d.scheme_name,
       d.fund_house,
       p.return_3yr,
       p.sharpe
FROM dim_fund d
JOIN fact_performance p
ON d.amfi_code = p.amfi_code;
```

## Investor Transactions By Scheme

```sql
SELECT t.date,
       d.scheme_name,
       t.type,
       t.amount
FROM fact_transactions t
JOIN dim_fund d
ON t.amfi_code = d.amfi_code;
```

---

# Dataset Summary

| Dataset                         | Table                     | Rows   |
| ------------------------------- | ------------------------- | ------ |
| clean_fund_master.csv           | dim_fund                  | 40     |
| generated                       | dim_date                  | 1,608  |
| clean_nav_history.csv           | fact_nav                  | 46,000 |
| clean_investor_transactions.csv | fact_transactions         | 13,048 |
| clean_scheme_performance.csv    | fact_performance          | 40     |
| clean_portfolio_holdings.csv    | fact_portfolio            | 322    |
| clean_aum_by_fund_house.csv     | fact_aum                  | 90     |
| clean_monthly_sip_inflows.csv   | fact_sip_industry         | 36     |
| clean_benchmark_indicies.csv    | fact_benchmark_indices    | 8,050  |
| clean_category_inflows.csv      | fact_category_inflows     | 144    |
| clean_industry_folio_count.csv  | fact_industry_folio_count | 36     |

```

**Total Records Loaded:** **69,378+ rows**
```
