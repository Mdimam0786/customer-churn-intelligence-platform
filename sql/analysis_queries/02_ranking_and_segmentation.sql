-- ============================================================
-- Ranking, Segmentation & Top-N Analysis
-- Author: Md Imamuddin
-- Target: PostgreSQL 14+ (verified logic-equivalent on SQLite 3.45)
-- ============================================================

-- ------------------------------------------------------------
-- KPI 4: Top 5 highest-CLTV churned customers PER contract type
-- Business question: "Within each contract tier, who were our
-- most valuable customers that we actually lost?" — a retention
-- war-room list, segmented so month-to-month losses don't drown
-- out the (rarer, more alarming) two-year contract losses.
-- ------------------------------------------------------------
WITH churned_customers AS (
    SELECT
        c.customer_id,
        p.contract_type,
        f.cltv,
        f.monthly_charges,
        f.tenure_months,
        cr.churn_reason,
        ROW_NUMBER() OVER (
            PARTITION BY p.contract_type
            ORDER BY f.cltv DESC
        ) AS cltv_rank_within_contract
    FROM fact_subscription f
    JOIN dim_customer c       ON f.customer_key = c.customer_key
    JOIN dim_plan p           ON f.plan_key = p.plan_key
    JOIN dim_churn_reason cr  ON f.churn_reason_key = cr.churn_reason_key
    WHERE f.churn_flag = 1
)
SELECT customer_id, contract_type, cltv, monthly_charges, tenure_months, churn_reason
FROM churned_customers
WHERE cltv_rank_within_contract <= 5
ORDER BY contract_type, cltv_rank_within_contract;


-- ------------------------------------------------------------
-- KPI 5: RFM-proxy quintile scoring via NTILE()
-- Business question: "Which customers are our best combination of
-- long-tenured, service-engaged, and high-billing — i.e. our
-- highest-value retention-priority segment?"
-- Note: this is an RFM PROXY (see the Business Glossary) since
-- this dataset has no transaction-level purchase history.
-- ------------------------------------------------------------
WITH rfm_base AS (
    SELECT
        c.customer_id,
        f.recency_tenure_months,
        f.frequency_addon_breadth,
        f.monetary_total_charges,
        f.churn_flag
    FROM fact_subscription f
    JOIN dim_customer c ON f.customer_key = c.customer_key
),
rfm_scored AS (
    SELECT
        customer_id,
        churn_flag,
        NTILE(5) OVER (ORDER BY recency_tenure_months ASC)      AS recency_quintile,   -- 5 = longest tenure (best)
        NTILE(5) OVER (ORDER BY frequency_addon_breadth ASC)    AS frequency_quintile, -- 5 = most add-ons (best)
        NTILE(5) OVER (ORDER BY monetary_total_charges ASC)     AS monetary_quintile   -- 5 = highest billed (best)
    FROM rfm_base
)
SELECT
    customer_id,
    recency_quintile,
    frequency_quintile,
    monetary_quintile,
    (recency_quintile + frequency_quintile + monetary_quintile) AS rfm_proxy_score,
    churn_flag,
    CASE
        WHEN (recency_quintile + frequency_quintile + monetary_quintile) >= 13 THEN 'Champion'
        WHEN (recency_quintile + frequency_quintile + monetary_quintile) >= 10 THEN 'Loyal'
        WHEN (recency_quintile + frequency_quintile + monetary_quintile) >= 7  THEN 'Steady'
        WHEN (recency_quintile + frequency_quintile + monetary_quintile) >= 4  THEN 'At Risk'
        ELSE 'Critical / New'
    END AS rfm_segment
FROM rfm_scored
ORDER BY rfm_proxy_score DESC;


-- ------------------------------------------------------------
-- KPI 6: Churn rate rank by city, minimum sample size enforced via CTE
-- Business question: "Which real markets (with statistically
-- meaningful customer counts) have the worst retention?"
-- ------------------------------------------------------------
WITH city_kpi AS (
    SELECT
        g.city,
        COUNT(*)                                       AS customers,
        SUM(f.churn_flag)                              AS churned,
        ROUND(100.0 * SUM(f.churn_flag) / COUNT(*), 2) AS churn_rate_pct,
        ROUND(SUM(f.total_charges), 2)                 AS total_revenue
    FROM fact_subscription f
    JOIN dim_geography g ON f.geography_key = g.geography_key
    GROUP BY g.city
    HAVING COUNT(*) >= 30    -- enforce a minimum sample size to avoid noisy small-n rates
)
SELECT
    city,
    customers,
    churned,
    churn_rate_pct,
    total_revenue,
    RANK() OVER (ORDER BY churn_rate_pct DESC) AS churn_rank
FROM city_kpi
ORDER BY churn_rank
LIMIT 15;


-- ------------------------------------------------------------
-- KPI 7: Payment method risk ranking with revenue share
-- Business question: "Which payment channels should Finance/Ops
-- prioritize migrating customers away from?"
-- ------------------------------------------------------------
WITH payment_kpi AS (
    SELECT
        pm.payment_method,
        COUNT(*)                                       AS customers,
        SUM(f.churn_flag)                              AS churned,
        ROUND(100.0 * SUM(f.churn_flag) / COUNT(*), 2) AS churn_rate_pct,
        ROUND(SUM(f.total_charges), 2)                 AS total_revenue,
        ROUND(AVG(f.tenure_months), 2)                 AS avg_tenure_months
    FROM fact_subscription f
    JOIN dim_payment_method pm ON f.payment_method_key = pm.payment_method_key
    GROUP BY pm.payment_method
)
SELECT
    payment_method,
    customers,
    churned,
    churn_rate_pct,
    avg_tenure_months,
    total_revenue,
    ROUND(100.0 * total_revenue / SUM(total_revenue) OVER (), 2) AS pct_of_total_revenue,
    RANK() OVER (ORDER BY churn_rate_pct DESC) AS churn_risk_rank
FROM payment_kpi
ORDER BY churn_risk_rank;
