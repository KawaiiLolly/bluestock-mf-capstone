-- ============================================================
-- queries.sql
-- Bluestock MF Capstone I — 10 Analytics Queries
--
-- Run from CLI:
--   sqlite3 data/db/bluestock_mf.db < sql/queries.sql
--
-- Run via Python:
--   python scripts/run_queries.py
-- ============================================================


-- Q1. Top 5 funds by AUM
-- Shows which schemes manage the most money.
SELECT
    amfi_code,
    scheme_name,
    fund_house,
    category,
    ROUND(aum_crore, 2)     AS aum_crore
FROM dim_fund
ORDER BY aum_crore DESC
LIMIT 5;


-- Q2. Average NAV per month (all schemes combined)
-- Useful for spotting broad market trends.
SELECT
    strftime('%Y-%m', date)     AS month,
    ROUND(AVG(nav), 2)          AS avg_nav,
    COUNT(*)                    AS nav_records
FROM fact_nav
GROUP BY strftime('%Y-%m', date)
ORDER BY month;


-- Q3. SIP inflow year-on-year growth (industry level)
-- Shows how the SIP habit has grown over years.
SELECT
    strftime('%Y', month)       AS year,
    ROUND(SUM(sip_inflow_crore), 2)   AS total_sip_inflow_crore,
    ROUND(AVG(sip_inflow_crore), 2)   AS avg_monthly_inflow_crore
FROM fact_sip_industry
GROUP BY strftime('%Y', month)
ORDER BY year;


-- Q4. Transactions count and total amount by state
-- Reveals which states drive the most investment activity.
SELECT
    state,
    COUNT(*)                        AS num_transactions,
    ROUND(SUM(amount), 2)           AS total_amount_rs,
    ROUND(AVG(amount), 2)           AS avg_amount_rs,
    COUNT(DISTINCT investor_id)     AS unique_investors
FROM fact_transactions
WHERE state IS NOT NULL
GROUP BY state
ORDER BY total_amount_rs DESC;


-- Q5. Funds with expense_ratio < 1%
-- Low-cost direct plans that save investors money.
SELECT
    d.amfi_code,
    d.scheme_name,
    d.fund_house,
    d.category,
    ROUND(p.expense_ratio, 2)       AS expense_ratio_pct,
    ROUND(p.return_1yr * 100, 2)    AS return_1yr_pct
FROM dim_fund d
JOIN fact_performance p ON d.amfi_code = p.amfi_code
WHERE p.expense_ratio < 1.0
  AND p.expense_ratio IS NOT NULL
ORDER BY p.expense_ratio ASC;


-- Q6. Top 10 best performing funds by 3-year return
-- Highlights consistent long-term outperformers.
SELECT
    d.scheme_name,
    d.fund_house,
    d.category,
    ROUND(p.return_1yr * 100, 2)    AS return_1yr_pct,
    ROUND(p.return_3yr * 100, 2)    AS return_3yr_pct,
    ROUND(p.return_5yr * 100, 2)    AS return_5yr_pct,
    ROUND(p.sharpe, 3)              AS sharpe_ratio
FROM dim_fund d
JOIN fact_performance p ON d.amfi_code = p.amfi_code
WHERE p.return_3yr IS NOT NULL
ORDER BY p.return_3yr DESC
LIMIT 10;


-- Q7. Category-wise average Sharpe ratio
-- Compares risk-adjusted returns across fund categories.
SELECT
    d.category,
    COUNT(*)                            AS num_funds,
    ROUND(AVG(p.sharpe), 3)             AS avg_sharpe,
    ROUND(AVG(p.return_1yr) * 100, 2)  AS avg_return_1yr_pct,
    ROUND(AVG(p.beta), 3)               AS avg_beta,
    ROUND(AVG(p.std_deviation), 4)      AS avg_std_dev
FROM dim_fund d
JOIN fact_performance p ON d.amfi_code = p.amfi_code
GROUP BY d.category
ORDER BY avg_sharpe DESC;


-- Q8. AUM trend per fund house over time
-- Tracks which AMCs are growing fastest.
SELECT
    fund_house,
    strftime('%Y-%m', date)         AS month,
    ROUND(aum_crore, 2)             AS aum_crore,
    num_schemes
FROM fact_aum
ORDER BY fund_house, month;


-- Q9. Top 10 most held stocks across all portfolios
-- Shows which stocks appear in the most mutual fund holdings.
SELECT
    stock_symbol,
    COUNT(DISTINCT amfi_code)           AS held_by_n_funds,
    ROUND(AVG(weight_pct), 2)           AS avg_weight_pct,
    sector
FROM fact_portfolio
GROUP BY stock_symbol, sector
ORDER BY held_by_n_funds DESC, avg_weight_pct DESC
LIMIT 10;


-- Q10. KYC compliance breakdown
-- Shows what share of transactions come from verified investors.
SELECT
    kyc_status,
    COUNT(*)                                AS num_transactions,
    COUNT(DISTINCT investor_id)             AS unique_investors,
    ROUND(SUM(amount), 2)                   AS total_amount_rs,
    ROUND(100.0 * COUNT(*) /
          SUM(COUNT(*)) OVER (), 2)         AS pct_of_total
FROM fact_transactions
GROUP BY kyc_status
ORDER BY num_transactions DESC;
