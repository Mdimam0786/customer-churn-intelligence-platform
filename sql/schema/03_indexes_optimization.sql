-- ============================================================
-- Indexing & Optimization
-- Author: Md Imamuddin
-- Target: PostgreSQL 14+
-- ============================================================

-- Beyond the foreign-key indexes already created earlier
-- (sql/schema/02_fact.sql), the following support the specific
-- query patterns used in the KPI queries.

-- Supports: churn-score threshold filtering (fn_get_high_risk_customers,
-- KPI 8 decile analysis) — a partial index further optimizes the common
-- "active customers only" access pattern used by CS outreach queries.
CREATE INDEX IF NOT EXISTS idx_fact_churn_score ON fact_subscription(churn_score);
CREATE INDEX IF NOT EXISTS idx_fact_active_churn_score
    ON fact_subscription(churn_score)
    WHERE churn_flag = 0;

-- Supports: CLTV-based ranking (KPI 4 top-N-per-segment, RFM proxy scoring)
CREATE INDEX IF NOT EXISTS idx_fact_cltv ON fact_subscription(cltv);

-- Supports: city-level rollups (KPI 6) — composite index matches the
-- GROUP BY city / HAVING COUNT(*) >= 30 access pattern directly.
CREATE INDEX IF NOT EXISTS idx_geography_city_state ON dim_geography(city, state);

-- Supports: payment-method risk ranking (KPI 7) — already has a unique
-- constraint, which Postgres uses as an index automatically;
-- listed here for documentation completeness.
-- (dim_payment_method.payment_method already UNIQUE per 01_dimensions.sql)

-- Supports: churn_reason lookups in Pareto analysis (KPI 10)
CREATE INDEX IF NOT EXISTS idx_churn_reason_lookup ON dim_churn_reason(churn_reason);

-- ------------------------------------------------------------
-- EXPLAIN ANALYZE guidance (documented, not executable here without
-- a live Postgres instance — see docs/sql_verification_log.md for
-- the SQLite EXPLAIN QUERY PLAN equivalent actually run against real
-- data in this local demo).
-- ------------------------------------------------------------
-- Before adding idx_fact_active_churn_score, a query filtering
-- WHERE churn_flag = 0 AND churn_score >= 80 would perform a full
-- sequential scan of all 7,043 fact rows. With the partial index,
-- Postgres can use an Index Scan restricted to only the ~5,174
-- active-customer rows, cutting the scanned row count by ~26.5%
-- (matching the real overall churn rate found in the EDA report) before
-- the churn_score predicate is even applied.
--
-- EXPLAIN ANALYZE SELECT * FROM fact_subscription
-- WHERE churn_flag = 0 AND churn_score >= 80;
