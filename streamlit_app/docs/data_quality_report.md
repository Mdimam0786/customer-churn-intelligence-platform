# Data Quality Report — Phase 2: Data Engineering

Author: Md Imamuddin

## 1. Data Sources (Real, Verified)

| Source | Format | Rows | Columns | Role |
|---|---|---|---|---|
| `Telco_customer_churn.xlsx` (IBM enriched) | XLSX | 7,043 | 33 | **Primary** — geography, CLTV, Churn Score, Churn Reason |
| `Telco-Customer-Churn.csv` (IBM standard) | CSV | 7,043 | 21 | **Cross-reference** — validates identity & key fields |

Both files were user-uploaded, real, and unmodified prior to ingestion. No synthetic or fabricated records were introduced at any stage.

**Cross-validation result:** the two sources describe the **identical population** — 7,043/7,043 matching `customerID` values, 0 unique-ID mismatches, 0 `MonthlyCharges` mismatches, 0 `Churn` label mismatches across sources.

---

## 2. Schema & Structural Validation (Pre-Cleaning)

- **Schema conformance:** all 33 expected columns present, 0 missing, 0 unexpected extras.
- **Duplicates:** 0 full-row duplicates, 0 duplicate `CustomerID` values (customer key is genuinely unique).
- **Categorical domain checks:** 0 violations across Gender, Senior Citizen, Partner, Dependents, Phone Service, Internet Service, Contract, Paperless Billing, and Churn Label — every value falls within its documented valid set.
- **Numeric range checks:** 0 negative charges, 0 negative tenure, 0 Churn Score outside 0–100, 0 negative CLTV.
- **Referential consistency:** 0 mismatches between `Churn Value` (0/1) and `Churn Label` (Yes/No) — fully consistent.
- **Geographic scope (verified, not assumed):** 100% of records are `United States` / `California`, spanning 1,129 distinct real cities. This is a real characteristic of this IBM sample population, not a filter applied by this pipeline — documented so downstream consumers don't mistake it for a national dataset.

---

## 3. Known Data Quality Issues Found & Resolved

### Issue 1 — Blank `Total Charges` for zero-tenure customers
- **Finding:** 11 records (0.16% of rows) have `tenure_months = 0` and a blank/whitespace `Total Charges` string. These are brand-new customers who signed up but haven't accrued a full billing cycle yet — a well-documented real-world quirk of this specific dataset, not a corrupted field.
- **Resolution:** Coerced to numeric (`errors='coerce'`), then imputed **only these 11 rows** using that same customer's own `monthly_charges` value (0 elapsed months → total billed equals one month's rate). Every imputed row is flagged via `is_new_customer_imputed_charges` for full transparency in downstream analysis.
- **Result:** 0 unexplained nulls remain in `total_charges` after the fix.

### Issue 2 — Null `Churn Reason` for active customers
- **Finding:** 5,174 records (73.5%) have a null `Churn Reason` — expected, since a reason only exists for customers who actually churned (1,869 churned records all have a reason populated).
- **Resolution:** Filled with the explicit category `"Not Applicable - Active Customer"` rather than left null, so the field groups/filters safely in SQL and Power BI without null-handling surprises.

### Issue 3 — Export artifact column
- **Finding:** The `Count` column is constant (`=1`) across all 7,043 rows — an IBM export artifact, not a real business measure.
- **Resolution:** Dropped after confirming constancy (not assumed).

### Issue 4 — Redundant geography encoding
- **Finding:** `Lat Long` is a string-concatenation of the already-separate `Latitude`/`Longitude` columns.
- **Resolution:** Dropped the redundant combined string field; kept the two numeric columns.

---

## 4. Feature Engineering — Provenance of Every Derived Field

| Derived Field | Formula / Source | Notes |
|---|---|---|
| `tenure_cohort` | Binned from real `tenure_months` | 6 buckets, 12-month width |
| `addon_service_count` | Count of "Yes" across 6 real add-on service fields | 0–6 |
| `has_internet` / `has_phone_and_internet` / `is_streaming_bundle` | Boolean combinations of real service fields | — |
| `avg_revenue_per_tenure_month` | `total_charges / tenure_months` (real fields); falls back to `monthly_charges` only when `tenure_months = 0` | No fabricated denominator |
| `contract_based_risk_tier` | Rule-based map from real `contract_type` | Transparent baseline for ML to beat in Phase 7 |
| `recency_tenure_months`, `frequency_addon_breadth`, `monetary_total_charges` | RFM **proxies** built from real tenure/service/billing fields | Explicitly labeled as proxies — this dataset has no transaction-level purchase history, so true RFM cannot be computed, and we do not pretend otherwise |

**Explicitly not fabricated:** this dataset has no real subscription start/renewal calendar date — only elapsed tenure in months. No calendar date dimension or synthetic signup date was created. Time-based analysis uses the real tenure field via `tenure_cohort` instead.

---

## 5. Star Schema — Load Verification

| Table | Row Count | Type |
|---|---|---|
| `dim_customer` | 7,043 | Dimension |
| `dim_geography` | 1,652 | Dimension (distinct city + zip combos) |
| `dim_plan` | 1,255 | Dimension (distinct service/contract combos) |
| `dim_payment_method` | 4 | Dimension |
| `dim_tenure_cohort` | 6 | Dimension |
| `dim_churn_reason` | 21 | Dimension |
| `fact_subscription` | 7,043 | Fact (grain: one row per real customer) |

**Referential integrity check:** 0 unresolved foreign keys across all 6 relationships (`customer_key`, `geography_key`, `plan_key`, `payment_method_key`, `tenure_cohort_key`, `churn_reason_key`) — every fact row joins cleanly to its dimensions.

**Spot-check business query result** (contract type vs. churn, run against the loaded database):

| Contract Type | Customers | Total Revenue (real, billed) |
|---|---|---|
| Month-to-month | 3,875 | $5,305,861.50 |
| One year | 1,473 | $4,467,073.20 |
| Two year | 1,695 | $6,283,689.60 |

**Database note:** a live PostgreSQL server wasn't available during parts of development. The production database scripts (`sql/schema/01_dimensions.sql`, `02_fact.sql`) are written for PostgreSQL 14+ and haven't changed; to fully test everything, the same tables were also loaded into a local SQLite file (`data/processed/churn_intelligence.db`) using the exact same table and column names, so the data transformations and referential integrity are genuinely verified against real data. Connecting to a real PostgreSQL database instead only requires changing the connection details, not the schema or the pipeline logic — see `docs/local_vscode_postgres_setup.md` for the steps to do this yourself.

---

## 6. Headline Real-Data Summary Statistics

- **Total real customers:** 7,043
- **Overall churn rate:** 26.54%
- **Total historical billed revenue:** $16,056,624.30
- **Average CLTV (IBM-provided):** 4,400.3
- **Contract mix:** Month-to-month 55.0% / Two year 24.1% / One year 20.9%

---

## 7. Data Quality Scorecard

| Dimension | Result |
|---|---|
| Completeness (post-cleaning) | 100% — 0 unexplained nulls in any field |
| Uniqueness | 100% — 0 duplicate customers |
| Validity (domain/range) | 100% — 0 violations found |
| Consistency (cross-source) | 100% — 0 mismatches between primary and cross-reference sources |
| Referential integrity (star schema) | 100% — 0 unresolved foreign keys |
| Fabrication check | **0 synthetic rows or invented field values anywhere in the pipeline** |

---

## 8. Files Produced This Phase

```
config/config.yaml
src/utils/logger.py
src/data_engineering/ingest.py
src/data_engineering/validate.py
src/data_engineering/clean.py
src/data_engineering/feature_engineering.py
src/data_engineering/etl_pipeline.py
sql/schema/01_dimensions.sql
sql/schema/02_fact.sql
data/raw/Telco_customer_churn.xlsx
data/raw/Telco-Customer-Churn.csv
data/processed/customer_churn_processed.csv     (flat, feature-engineered)
data/processed/churn_intelligence.db            (SQLite star schema, local demo)
docs/data_quality_report.md                     (this file)
```

---

### Next Step

Ready to proceed to **Phase 3: Exploratory Data Analysis** (100+ business insights across retention, revenue, cohorts, RFM proxies, and funnel analysis) whenever you confirm.
