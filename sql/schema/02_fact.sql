-- ============================================================
-- Customer Subscription & Churn Intelligence Platform
-- Star Schema: FACT TABLE
-- Author: Md Imamuddin
-- Target: PostgreSQL 14+
-- Grain: one row per customer (this dataset is a single snapshot,
--        not a transaction log — each customer appears exactly once)
-- ============================================================

CREATE TABLE IF NOT EXISTS fact_subscription (
    subscription_fact_key     SERIAL PRIMARY KEY,

    -- Foreign keys to dimensions
    customer_key              INTEGER NOT NULL REFERENCES dim_customer(customer_key),
    geography_key             INTEGER NOT NULL REFERENCES dim_geography(geography_key),
    plan_key                  INTEGER NOT NULL REFERENCES dim_plan(plan_key),
    payment_method_key        INTEGER NOT NULL REFERENCES dim_payment_method(payment_method_key),
    tenure_cohort_key         INTEGER NOT NULL REFERENCES dim_tenure_cohort(tenure_cohort_key),
    churn_reason_key          INTEGER NOT NULL REFERENCES dim_churn_reason(churn_reason_key),

    -- Degenerate / measure fields (real, from source)
    tenure_months             SMALLINT NOT NULL CHECK (tenure_months >= 0),
    monthly_charges           DECIMAL(8,2) NOT NULL CHECK (monthly_charges >= 0),
    total_charges             DECIMAL(10,2) NOT NULL CHECK (total_charges >= 0),
    is_new_customer_imputed_charges BOOLEAN NOT NULL DEFAULT FALSE,

    churn_flag                SMALLINT NOT NULL CHECK (churn_flag IN (0,1)),
    churn_score               SMALLINT NOT NULL CHECK (churn_score BETWEEN 0 AND 100),
    cltv                       INTEGER NOT NULL,

    -- Derived features (from the feature engineering step, all traceable to real fields)
    addon_service_count            SMALLINT NOT NULL,
    avg_revenue_per_tenure_month   DECIMAL(8,2) NOT NULL,
    recency_tenure_months          SMALLINT NOT NULL,
    frequency_addon_breadth        SMALLINT NOT NULL,
    monetary_total_charges         DECIMAL(10,2) NOT NULL,

    loaded_at                  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fact_customer_key ON fact_subscription(customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_geography_key ON fact_subscription(geography_key);
CREATE INDEX IF NOT EXISTS idx_fact_plan_key ON fact_subscription(plan_key);
CREATE INDEX IF NOT EXISTS idx_fact_churn_flag ON fact_subscription(churn_flag);
CREATE INDEX IF NOT EXISTS idx_fact_tenure_cohort ON fact_subscription(tenure_cohort_key);

COMMENT ON TABLE fact_subscription IS
'Grain: one row per real customer. Snapshot fact (not transactional) — this source dataset has no repeated-measure/event history, only a single current-state record per customer.';
