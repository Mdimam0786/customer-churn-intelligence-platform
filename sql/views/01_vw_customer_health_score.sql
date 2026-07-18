-- ============================================================
-- VIEW: Customer Health Score
-- Author: Md Imamuddin
-- Target: PostgreSQL 14+ (verified logic-equivalent on SQLite 3.45)
--
-- A regular (non-materialized) VIEW is used here deliberately —
-- health score must reflect the current fact table on every read,
-- since it's meant to back a live Customer Success dashboard where
-- staleness would be actively misleading.
-- ============================================================

CREATE OR REPLACE VIEW vw_customer_health_score AS
WITH scored AS (
    SELECT
        c.customer_id,
        p.contract_type,
        p.contract_based_risk_tier,
        f.tenure_months,
        f.monthly_charges,
        f.cltv,
        f.churn_score,
        f.addon_service_count,
        f.churn_flag,
        -- Health components, each normalized 0-100 in the direction of "healthier = higher"
        (100 - f.churn_score)                                            AS score_from_churn_risk,
        LEAST(100, f.tenure_months * 100.0 / 72)                         AS score_from_tenure,
        LEAST(100, f.addon_service_count * 100.0 / 6)                    AS score_from_addon_adoption,
        CASE p.contract_type
            WHEN 'Two year' THEN 100
            WHEN 'One year' THEN 60
            ELSE 20
        END                                                              AS score_from_contract_commitment
    FROM fact_subscription f
    JOIN dim_customer c ON f.customer_key = c.customer_key
    JOIN dim_plan p     ON f.plan_key = p.plan_key
)
SELECT
    customer_id,
    contract_type,
    tenure_months,
    monthly_charges,
    cltv,
    churn_score,
    addon_service_count,
    churn_flag,
    ROUND(
        0.40 * score_from_churn_risk +
        0.25 * score_from_tenure +
        0.20 * score_from_addon_adoption +
        0.15 * score_from_contract_commitment
    , 1) AS customer_health_score,
    CASE
        WHEN (
            0.40 * score_from_churn_risk +
            0.25 * score_from_tenure +
            0.20 * score_from_addon_adoption +
            0.15 * score_from_contract_commitment
        ) >= 70 THEN 'Healthy'
        WHEN (
            0.40 * score_from_churn_risk +
            0.25 * score_from_tenure +
            0.20 * score_from_addon_adoption +
            0.15 * score_from_contract_commitment
        ) >= 45 THEN 'Watch'
        ELSE 'At Risk'
    END AS health_tier
FROM scored;

COMMENT ON VIEW vw_customer_health_score IS
'Weighted composite health score (0-100): 40% inverse churn-risk score, 25% tenure, 20% add-on adoption, 15% contract commitment. Weights are a transparent, documented business rule (the business recommendations use this rule-based score alongside the ML model for cross-checking).';

-- Example usage: find at-risk, high-value customers for CS outreach
-- SELECT * FROM vw_customer_health_score
-- WHERE health_tier = 'At Risk' AND cltv > (SELECT AVG(cltv) FROM vw_customer_health_score)
-- ORDER BY cltv DESC;
