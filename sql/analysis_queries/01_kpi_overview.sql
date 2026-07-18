-- ============================================================
-- Customer Subscription & Churn Intelligence Platform
-- Executive KPI Overview
-- Author: Md Imamuddin
-- Target: PostgreSQL 14+ (verified logic-equivalent on SQLite 3.45
--          against the star schema; syntax is ANSI-standard
--          CTE/window-function SQL that runs unmodified on Postgres)
-- ============================================================

-- ------------------------------------------------------------
-- KPI 1: Executive summary — single-row headline metrics
-- Business question: "What's our churn, revenue, and risk exposure
-- right now, in one number each?"
-- ------------------------------------------------------------
WITH base AS (
    SELECT
        f.*,
        c.customer_id
    FROM fact_subscription f
    JOIN dim_customer c ON f.customer_key = c.customer_key
)
SELECT
    COUNT(*)                                                   AS total_customers,
    SUM(churn_flag)                                            AS churned_customers,
    ROUND(100.0 * SUM(churn_flag) / COUNT(*), 2)               AS churn_rate_pct,
    ROUND(SUM(total_charges), 2)                               AS total_billed_revenue,
    ROUND(SUM(monthly_charges), 2)                             AS current_mrr,
    ROUND(SUM(CASE WHEN churn_flag = 1 THEN monthly_charges ELSE 0 END), 2) AS mrr_at_risk_from_churned,
    ROUND(AVG(cltv), 2)                                        AS avg_cltv,
    ROUND(AVG(tenure_months), 2)                               AS avg_tenure_months
FROM base;


-- ------------------------------------------------------------
-- KPI 2: Churn & revenue by contract type, with company-wide
-- comparison via window functions (no self-join needed)
-- Business question: "How does each contract tier compare to the
-- overall company average, side by side?"
-- ------------------------------------------------------------
WITH contract_kpi AS (
    SELECT
        p.contract_type,
        COUNT(*)                                    AS customers,
        SUM(f.churn_flag)                           AS churned,
        ROUND(100.0 * SUM(f.churn_flag) / COUNT(*), 2) AS churn_rate_pct,
        ROUND(AVG(f.monthly_charges), 2)            AS avg_monthly_charges,
        ROUND(SUM(f.total_charges), 2)              AS total_revenue
    FROM fact_subscription f
    JOIN dim_plan p ON f.plan_key = p.plan_key
    GROUP BY p.contract_type
)
SELECT
    contract_type,
    customers,
    churned,
    churn_rate_pct,
    avg_monthly_charges,
    total_revenue,
    -- Window function: compare each segment to the overall average
    ROUND(AVG(churn_rate_pct) OVER (), 2)            AS company_avg_churn_rate_pct,
    ROUND(churn_rate_pct - AVG(churn_rate_pct) OVER (), 2) AS churn_rate_vs_company_avg,
    ROUND(100.0 * total_revenue / SUM(total_revenue) OVER (), 2) AS pct_of_total_revenue,
    RANK() OVER (ORDER BY churn_rate_pct DESC)       AS churn_risk_rank
FROM contract_kpi
ORDER BY churn_risk_rank;


-- ------------------------------------------------------------
-- KPI 3: Tenure-cohort progression with period-over-period deltas
-- (LAG window function substitutes for a calendar-based
-- month-over-month comparison, since no real calendar dates exist
-- in this source data — tenure cohort IS the "time axis" here)
-- Business question: "How does churn change as customers age
-- through cohorts, and what's the incremental change cohort-to-cohort?"
-- ------------------------------------------------------------
WITH cohort_kpi AS (
    SELECT
        tc.tenure_cohort_label,
        tc.sort_order,
        COUNT(*)                                       AS customers,
        SUM(f.churn_flag)                              AS churned,
        ROUND(100.0 * SUM(f.churn_flag) / COUNT(*), 2) AS churn_rate_pct,
        ROUND(SUM(f.total_charges), 2)                 AS total_revenue
    FROM fact_subscription f
    JOIN dim_tenure_cohort tc ON f.tenure_cohort_key = tc.tenure_cohort_key
    GROUP BY tc.tenure_cohort_label, tc.sort_order
)
SELECT
    tenure_cohort_label,
    customers,
    churned,
    churn_rate_pct,
    total_revenue,
    LAG(churn_rate_pct) OVER (ORDER BY sort_order)                     AS prior_cohort_churn_rate,
    ROUND(churn_rate_pct - LAG(churn_rate_pct) OVER (ORDER BY sort_order), 2) AS churn_rate_change,
    SUM(total_revenue) OVER (ORDER BY sort_order
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)              AS cumulative_revenue_through_cohort
FROM cohort_kpi
ORDER BY sort_order;
