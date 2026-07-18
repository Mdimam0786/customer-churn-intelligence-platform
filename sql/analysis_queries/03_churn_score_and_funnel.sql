-- ============================================================
-- Churn Score Calibration & Funnel Analysis
-- Author: Md Imamuddin
-- Target: PostgreSQL 14+ (verified logic-equivalent on SQLite 3.45)
-- ============================================================

-- ------------------------------------------------------------
-- KPI 8: Churn score decile calibration (validates IBM's provided
-- risk score against actual outcomes, entirely in SQL)
-- Business question: "Can we trust the Churn Score field enough to
-- triage retention outreach by it today, before any ML model exists?"
-- ------------------------------------------------------------
WITH scored AS (
    SELECT
        f.churn_score,
        f.churn_flag,
        f.monthly_charges,
        f.cltv,
        NTILE(10) OVER (ORDER BY f.churn_score ASC) AS churn_score_decile
    FROM fact_subscription f
)
SELECT
    churn_score_decile,
    COUNT(*)                                          AS customers,
    SUM(churn_flag)                                    AS actual_churned,
    ROUND(100.0 * SUM(churn_flag) / COUNT(*), 2)       AS actual_churn_rate_pct,
    ROUND(AVG(churn_score), 1)                         AS avg_churn_score,
    ROUND(AVG(cltv), 2)                                AS avg_cltv,
    ROUND(SUM(monthly_charges), 2)                     AS total_monthly_revenue
FROM scored
GROUP BY churn_score_decile
ORDER BY churn_score_decile DESC;


-- ------------------------------------------------------------
-- KPI 9: Add-on service adoption funnel with churn rate at each stage
-- Business question: "Where in the service-adoption journey do we
-- lose the most retention benefit, and where's the upsell opportunity?"
-- ------------------------------------------------------------
WITH addon_kpi AS (
    SELECT
        f.addon_service_count,
        COUNT(*)                                       AS customers,
        SUM(f.churn_flag)                              AS churned,
        ROUND(100.0 * SUM(f.churn_flag) / COUNT(*), 2) AS churn_rate_pct,
        ROUND(AVG(f.monthly_charges), 2)               AS avg_monthly_charges
    FROM fact_subscription f
    GROUP BY f.addon_service_count
)
SELECT
    addon_service_count,
    customers,
    churned,
    churn_rate_pct,
    avg_monthly_charges,
    SUM(customers) OVER (ORDER BY addon_service_count DESC
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_customers_at_this_tier_or_above,
    LAG(churn_rate_pct) OVER (ORDER BY addon_service_count)          AS prior_tier_churn_rate,
    ROUND(churn_rate_pct - LAG(churn_rate_pct) OVER (ORDER BY addon_service_count), 2) AS churn_rate_delta
FROM addon_kpi
ORDER BY addon_service_count;


-- ------------------------------------------------------------
-- KPI 10: Root-cause churn reason ranking with cumulative % (Pareto)
-- Business question: "What's the minimum set of root causes that
-- explain 80% of our churn?" (classic 80/20 Pareto cut via window fn)
-- ------------------------------------------------------------
WITH reason_kpi AS (
    SELECT
        cr.churn_reason,
        COUNT(*) AS churned_customers,
        ROUND(SUM(f.monthly_charges), 2) AS lost_monthly_revenue
    FROM fact_subscription f
    JOIN dim_churn_reason cr ON f.churn_reason_key = cr.churn_reason_key
    WHERE f.churn_flag = 1
    GROUP BY cr.churn_reason
),
reason_ranked AS (
    SELECT
        churn_reason,
        churned_customers,
        lost_monthly_revenue,
        ROUND(100.0 * churned_customers / SUM(churned_customers) OVER (), 2) AS pct_of_churn,
        ROUND(100.0 * SUM(churned_customers) OVER (ORDER BY churned_customers DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
            / SUM(churned_customers) OVER (), 2) AS cumulative_pct_of_churn
    FROM reason_kpi
)
SELECT *,
    CASE WHEN cumulative_pct_of_churn <= 80 THEN 'Core 80% driver' ELSE 'Long tail' END AS pareto_bucket
FROM reason_ranked
ORDER BY churned_customers DESC;
