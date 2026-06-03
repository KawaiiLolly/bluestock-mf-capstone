-- ============================================================
-- schema.sql
-- Bluestock MF Capstone I — SQLite Star Schema
--
-- Tables :
--   dim_fund           40 rows
--   dim_date         1500 rows
--   fact_nav        46000 rows
--   fact_transactions 32000+ rows
--   fact_performance    40 rows
--   fact_portfolio     320 rows
--   fact_aum            90 rows
--   fact_sip_industry   48 rows
--
-- Run:
--   sqlite3 data/db/bluestock_mf.db < sql/schema.sql
-- ============================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;



-- DIMENSION TABLES
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code       TEXT    PRIMARY KEY,
    scheme_name     TEXT    NOT NULL,
    fund_house      TEXT    NOT NULL,
    category        TEXT,
    sub_category    TEXT,
    risk_grade      TEXT,
    benchmark       TEXT,
    launch_date     TEXT,
    fund_manager    TEXT,
    aum_crore       REAL,
    expense_ratio   REAL,
    exit_load_pct   REAL
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT    NOT NULL UNIQUE,
    year        INTEGER NOT NULL,
    month       INTEGER NOT NULL,
    quarter     INTEGER NOT NULL,
    month_name  TEXT    NOT NULL,
    is_weekday  INTEGER NOT NULL    -- 1 = weekday, 0 = weekend
);

-- FACT TABLES
CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code           TEXT    NOT NULL REFERENCES dim_fund(amfi_code),
    date                TEXT    NOT NULL REFERENCES dim_date(date),
    nav                 REAL    NOT NULL CHECK (nav > 0),
    daily_return_pct    REAL,
    UNIQUE (amfi_code, date)
);

CREATE TABLE fact_transactions (
    tx_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id         INTEGER NOT NULL,
    amfi_code           TEXT NOT NULL  REFERENCES dim_fund(amfi_code),
    date                TEXT NOT NULL,
    amount              REAL NOT NULL,
    type                TEXT NOT NULL,
    state               TEXT,
    city                TEXT,
    city_tier           TEXT,
    age_group           TEXT,
    gender              TEXT,
    annual_income_lakh  REAL,
    payment_mode        TEXT,
    kyc_status          TEXT
);

CREATE TABLE IF NOT EXISTS fact_performance (
    perf_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code       TEXT    NOT NULL REFERENCES dim_fund(amfi_code),
    as_of_date      TEXT    NOT NULL,
    return_1yr      REAL,
    return_3yr      REAL,
    return_5yr      REAL,
    sharpe          REAL,
    alpha           REAL,
    beta            REAL,
    max_drawdown    REAL,
    std_deviation   REAL,
    expense_ratio   REAL,
    sharpe_flag     TEXT,
    UNIQUE (amfi_code, as_of_date)
);

CREATE TABLE IF NOT EXISTS fact_portfolio (
    portfolio_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code       TEXT    NOT NULL REFERENCES dim_fund(amfi_code),
    stock_symbol    TEXT    NOT NULL,
    weight_pct      REAL,
    sector          TEXT,
    date            TEXT    NOT NULL,
    isin            TEXT,
    UNIQUE (amfi_code, stock_symbol, date)
);

CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_house      TEXT    NOT NULL,
    date            TEXT    NOT NULL,
    aum_crore       REAL    NOT NULL CHECK (aum_crore > 0),
    num_schemes     INTEGER,
    UNIQUE (fund_house, date)
);

CREATE TABLE IF NOT EXISTS fact_sip_industry (
    sip_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    month               TEXT    NOT NULL UNIQUE,
    sip_inflow_crore    REAL    NOT NULL,
    sip_accounts_crore  REAL
);

CREATE TABLE IF NOT EXISTS fact_benchmark_indices (
    benchmark_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    index_name TEXT NOT NULL,
    close_value REAL
);

CREATE TABLE IF NOT EXISTS fact_category_inflows (
    inflow_id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL,
    category TEXT NOT NULL,
    net_inflow_crore REAL
);

CREATE TABLE IF NOT EXISTS fact_industry_folio_count (
    folio_id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL,
    total_folios_crore REAL,
    equity_folios_crore REAL,
    debt_folios_crore REAL,
    hybrid_folios_crore REAL,
    others_folios_crore REAL
);


-- INDEXES — speed up common queries
CREATE INDEX IF NOT EXISTS idx_nav_amfi_date
    ON fact_nav (amfi_code, date);

CREATE INDEX IF NOT EXISTS idx_nav_date
    ON fact_nav (date);

CREATE INDEX IF NOT EXISTS idx_tx_amfi
    ON fact_transactions (amfi_code);

CREATE INDEX IF NOT EXISTS idx_tx_date
    ON fact_transactions (date);

CREATE INDEX IF NOT EXISTS idx_tx_type
    ON fact_transactions (type);

CREATE INDEX IF NOT EXISTS idx_tx_state
    ON fact_transactions (state);

CREATE INDEX IF NOT EXISTS idx_fund_house
    ON dim_fund (fund_house);

CREATE INDEX IF NOT EXISTS idx_fund_category
    ON dim_fund (category);
