-- ============================================================
-- Customer Subscription & Churn Intelligence Platform
-- MATERIALIZED VIEWS
-- Target: PostgreSQL 14+
-- Author: Md Imamuddin
--
-- Materialized views are used here because these two rollups
-- summarize the full fact table for Power BI, which queries them
-- often. Recomputing the summary from scratch on every dashboard
-- refresh would be slow, so the results are stored and refreshed on
-- a schedule instead (see the refresh stored procedure). This is a
-- fine trade-off for cohort/geography summaries, unlike the customer
-- health view, which always needs to show current data.
--
-- Note
-- This file uses PostgreSQL's materialized views, which SQLite does
-- not support. These were checked for correct SQL syntax and tested
-- against PostgreSQL. The same summary logic was also tested using
-- a regular table build in `src/data_engineering/refresh_mat_views.py`,
-- producing the same real numbers.
-- ============================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_tenure_cohort_rollup AS
SELECT
    tc.tenure_cohort_label,
    tc.sort_order,
    COUNT(*)                                       AS customers,
    SUM(f.churn_flag)                              AS churned,
    ROUND(100.0 * SUM(f.churn_flag) / COUNT(*), 2) AS churn_rate_pct,
    ROUND(AVG(f.monthly_charges), 2)               AS avg_monthly_charges,
    ROUND(SUM(f.total_charges), 2)                 AS total_revenue,
    ROUND(AVG(f.cltv), 2)                          AS avg_cltv
FROM fact_subscription f
JOIN dim_tenure_cohort tc ON f.tenure_cohort_key = tc.tenure_cohort_key
GROUP BY tc.tenure_cohort_label, tc.sort_order
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_tenure_cohort_label ON mv_tenure_cohort_rollup(tenure_cohort_label);

COMMENT ON MATERIALIZED VIEW mv_tenure_cohort_rollup IS
'Pre-aggregated tenure-cohort KPI rollup for the Power BI Cohort Dashboard. Refresh via sp_refresh_kpi_rollups() after each ETL load.';


CREATE MATERIALIZED VIEW IF NOT EXISTS mv_geography_rollup AS
SELECT
    g.city,
    g.state,
    COUNT(*)                                       AS customers,
    SUM(f.churn_flag)                              AS churned,
    ROUND(100.0 * SUM(f.churn_flag) / COUNT(*), 2) AS churn_rate_pct,
    ROUND(SUM(f.total_charges), 2)                 AS total_revenue,
    AVG(g.latitude)                                AS latitude,
    AVG(g.longitude)                               AS longitude
FROM fact_subscription f
JOIN dim_geography g ON f.geography_key = g.geography_key
GROUP BY g.city, g.state
WITH DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_geography_city ON mv_geography_rollup(city);

COMMENT ON MATERIALIZED VIEW mv_geography_rollup IS
'Pre-aggregated city-level KPI rollup for the Power BI Geographic Dashboard map visual. Refresh via sp_refresh_kpi_rollups() after each ETL load.';
