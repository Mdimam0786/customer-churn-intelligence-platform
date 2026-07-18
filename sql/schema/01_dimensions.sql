-- ============================================================
-- Customer Subscription & Churn Intelligence Platform
-- Star Schema: DIMENSION TABLES
-- Author: Md Imamuddin
-- Target: PostgreSQL 14+
--
-- Design notes:
--   - Surrogate integer keys (xxx_key) are used for all dimension PKs,
--     with the natural/business key retained as a unique column.
--   - This schema deliberately has NO dim_date. The source dataset
--     provides tenure in elapsed months only, not a calendar
--     subscription start/renewal date, so no date dimension is
--     fabricated. dim_tenure_cohort substitutes for time-based
--     slicing using the real tenure field.
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_key        SERIAL PRIMARY KEY,
    customer_id         VARCHAR(20) NOT NULL UNIQUE,   -- natural key, e.g. '3668-QPYBK'
    gender              VARCHAR(10) NOT NULL,
    senior_citizen      BOOLEAN NOT NULL,
    has_partner         BOOLEAN NOT NULL,
    has_dependents      BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_geography (
    geography_key        SERIAL PRIMARY KEY,
    country               VARCHAR(50) NOT NULL,
    state                 VARCHAR(50) NOT NULL,
    city                  VARCHAR(100) NOT NULL,
    zip_code              VARCHAR(10) NOT NULL,
    latitude              DECIMAL(9,6),
    longitude             DECIMAL(9,6),
    UNIQUE (city, zip_code)
);

CREATE TABLE IF NOT EXISTS dim_plan (
    plan_key              SERIAL PRIMARY KEY,
    contract_type         VARCHAR(20) NOT NULL,      -- Month-to-month / One year / Two year
    internet_service      VARCHAR(20) NOT NULL,      -- DSL / Fiber optic / No
    phone_service         BOOLEAN NOT NULL,
    multiple_lines        VARCHAR(25) NOT NULL,
    online_security       VARCHAR(25) NOT NULL,
    online_backup         VARCHAR(25) NOT NULL,
    device_protection     VARCHAR(25) NOT NULL,
    tech_support          VARCHAR(25) NOT NULL,
    streaming_tv          VARCHAR(25) NOT NULL,
    streaming_movies      VARCHAR(25) NOT NULL,
    paperless_billing     BOOLEAN NOT NULL,
    contract_based_risk_tier VARCHAR(10) NOT NULL,   -- High / Medium / Low
    UNIQUE (
        contract_type, internet_service, phone_service, multiple_lines,
        online_security, online_backup, device_protection, tech_support,
        streaming_tv, streaming_movies, paperless_billing
    )
);

CREATE TABLE IF NOT EXISTS dim_payment_method (
    payment_method_key    SERIAL PRIMARY KEY,
    payment_method        VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dim_tenure_cohort (
    tenure_cohort_key     SERIAL PRIMARY KEY,
    tenure_cohort_label   VARCHAR(20) NOT NULL UNIQUE,   -- e.g. '0-12 mo'
    sort_order            SMALLINT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_churn_reason (
    churn_reason_key      SERIAL PRIMARY KEY,
    churn_reason          VARCHAR(100) NOT NULL UNIQUE
);

COMMENT ON TABLE dim_customer IS 'One row per unique real customer (surrogate keyed on customer_id).';
COMMENT ON TABLE dim_geography IS 'Real city/state/zip/lat-long combinations present in the source data (California only in this sample).';
COMMENT ON TABLE dim_plan IS 'Distinct combinations of contract and service attributes subscribed.';
COMMENT ON TABLE dim_tenure_cohort IS 'Tenure-based time bucket, used in place of a calendar date dimension (no real subscription dates exist in source).';
