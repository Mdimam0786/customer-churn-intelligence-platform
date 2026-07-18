-- ============================================================
-- Customer Subscription & Churn Intelligence Platform
-- STORED PROCEDURES
-- Target: PostgreSQL 14+ (PL/pgSQL)
-- Author: Md Imamuddin
--
-- Note
-- This file uses PostgreSQL features (stored procedures and functions)
-- that SQLite cannot run. These were checked for correct SQL syntax
-- and tested against PostgreSQL. The Streamlit app uses an equivalent
-- pandas implementation for this same logic, which has been fully
-- tested — see docs/sql_verification_log.md for details.
-- ============================================================

-- ------------------------------------------------------------
-- Function 1: Return high-risk customers above a caller-specified
-- churn score threshold, optionally filtered to a contract type.
-- Business use: powers a daily Customer Success "call list" export
-- without needing a BI tool in the loop.
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_get_high_risk_customers(
    p_churn_score_threshold SMALLINT DEFAULT 70,
    p_contract_type VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    customer_id VARCHAR,
    contract_type VARCHAR,
    churn_score SMALLINT,
    cltv INTEGER,
    monthly_charges DECIMAL,
    tenure_months SMALLINT,
    health_tier TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.customer_id,
        p.contract_type,
        f.churn_score,
        f.cltv,
        f.monthly_charges,
        f.tenure_months,
        h.health_tier
    FROM fact_subscription f
    JOIN dim_customer c ON f.customer_key = c.customer_key
    JOIN dim_plan p     ON f.plan_key = p.plan_key
    JOIN vw_customer_health_score h ON h.customer_id = c.customer_id
    WHERE f.churn_score >= p_churn_score_threshold
      AND f.churn_flag = 0
      AND (p_contract_type IS NULL OR p.contract_type = p_contract_type)
    ORDER BY f.cltv DESC, f.churn_score DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_get_high_risk_customers IS
'Returns active (non-churned) customers at or above a churn-score threshold, highest-value first. Usage: SELECT * FROM fn_get_high_risk_customers(80, ''Month-to-month'');';


-- ------------------------------------------------------------
-- Procedure 2: Refresh both materialized views after an ETL load.
-- ------------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_refresh_kpi_rollups()
LANGUAGE plpgsql
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_tenure_cohort_rollup;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_geography_rollup;
    RAISE NOTICE 'KPI rollups refreshed at %', clock_timestamp();
END;
$$;

-- Usage: CALL sp_refresh_kpi_rollups();


-- ------------------------------------------------------------
-- Procedure 3: Upsert a single customer's churn score after a
-- scoring re-run, without reloading the entire fact table.
-- ------------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_update_customer_churn_score(
    p_customer_id VARCHAR,
    p_new_churn_score SMALLINT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_customer_key INTEGER;
BEGIN
    SELECT customer_key INTO v_customer_key
    FROM dim_customer
    WHERE customer_id = p_customer_id;

    IF v_customer_key IS NULL THEN
        RAISE EXCEPTION 'Customer % not found in dim_customer', p_customer_id;
    END IF;

    UPDATE fact_subscription
    SET churn_score = p_new_churn_score
    WHERE customer_key = v_customer_key;

    RAISE NOTICE 'Updated churn_score for customer % to %', p_customer_id, p_new_churn_score;
END;
$$;

-- Usage: CALL sp_update_customer_churn_score('3668-QPYBK', 92);
