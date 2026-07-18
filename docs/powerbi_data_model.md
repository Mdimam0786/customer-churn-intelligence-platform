# Power BI Data Model Documentation

Author: Md Imamuddin

## 1. Import Instructions

1. Open Power BI Desktop → Get Data → Text/CSV
2. Import each file in `powerbi/data_export/`:
   `dim_customer.csv`, `dim_geography.csv`, `dim_plan.csv`, `dim_payment_method.csv`, `dim_tenure_cohort.csv`, `dim_churn_reason.csv`, `fact_subscription.csv`
3. In Power Query, set correct data types per the schema below before loading (Power BI sometimes mis-infers integer keys as text).

## 2. Star Schema Relationships (Model View)

```
dim_customer (1) ────────────< (∞) fact_subscription
dim_geography (1) ───────────< (∞) fact_subscription
dim_plan (1) ─────────────────< (∞) fact_subscription
dim_payment_method (1) ──────< (∞) fact_subscription
dim_tenure_cohort (1) ───────< (∞) fact_subscription
dim_churn_reason (1) ────────< (∞) fact_subscription
```

All relationships: **one-to-many, single direction (dimension → fact)**, cross-filter direction set to "Single" — standard star-schema best practice. Do not enable bidirectional filtering; it isn't needed here and would only slow the model and create ambiguity risk.

| From (dim) | Key | To (fact) | Key |
|---|---|---|---|
| dim_customer | customer_key | fact_subscription | customer_key |
| dim_geography | geography_key | fact_subscription | geography_key |
| dim_plan | plan_key | fact_subscription | plan_key |
| dim_payment_method | payment_method_key | fact_subscription | payment_method_key |
| dim_tenure_cohort | tenure_cohort_key | fact_subscription | tenure_cohort_key |
| dim_churn_reason | churn_reason_key | fact_subscription | churn_reason_key |

## 3. No Date Table — Documented Deliberately

Standard Power BI star schemas include a `dim_date` marked as the model's official date table (via Mark as Date Table), enabling `DATEADD`/`TOTALYTD`/etc. **This model deliberately has none**, because the source data contains no real calendar subscription date (see Phase 2/3/4 documentation). Adding a synthetic date table populated with fabricated dates would violate this project's no-fabrication principle. `dim_tenure_cohort` serves as the ordered "pseudo-time" axis instead — sort it by `sort_order`, not alphabetically, via Column Tool → Sort by Column in the Power BI model view.

## 4. Recommended Calculated Columns (added during Power Query, not as DAX measures)

For performance on repeated visual interactions, add these as Power Query calculated columns on `fact_subscription` before loading (values are already available from the Phase 4 SQL `NTILE()` queries — re-export from SQL rather than recompute in Power Query if possible):

- `churn_score_decile` (1–10, from `NTILE(10) OVER (ORDER BY churn_score)`)
- `rfm_recency_quintile`, `rfm_frequency_quintile`, `rfm_monetary_quintile` (1–5 each, from Phase 4 KPI 5 logic)
- `rfm_total_score` = sum of the three quintiles above
- `rfm_segment` = the CASE/SWITCH label from Phase 4 KPI 5 / DAX Section 5

## 5. Field Parameters (Power BI Field Parameters feature)

Two field parameters recommended for interactive dashboard flexibility:

**Field Parameter: "Segment By"**
- `dim_plan[contract_type]`
- `dim_plan[internet_service]`
- `dim_payment_method[payment_method]`
- `dim_tenure_cohort[tenure_cohort_label]`
- `dim_customer[gender]`
- `dim_customer[senior_citizen]`

Used on the Executive Overview and Segmentation dashboards to let users swap the breakdown dimension on a chart via a slicer, without duplicating visuals.

**Field Parameter: "Metric to Chart"**
- `[Churn Rate %]`
- `[Average CLTV]`
- `[Total Billed Revenue]`
- `[Average Tenure (Months)]`
- `[Customer Health Score]`

Used on the Cohort and Geographic dashboards to let one chart serve multiple KPI views.

## 6. Data Types Reference

| Table | Column | Type |
|---|---|---|
| fact_subscription | churn_flag | Whole Number (0/1), used as both measure input and slicer |
| fact_subscription | churn_score, cltv | Whole Number |
| fact_subscription | monthly_charges, total_charges | Fixed Decimal Number (currency format) |
| dim_geography | latitude, longitude | Decimal Number |
| dim_customer | senior_citizen, has_partner, has_dependents | True/False |

## 7. Performance Notes

- `fact_subscription` is 7,043 rows — small enough that Import mode (not DirectQuery) is strongly recommended; there is no practical benefit to DirectQuery at this scale, and it would only add latency.
- `dim_geography` has 1,652 rows (distinct city/zip combos) — well within normal Power BI map-visual limits.
- No aggregation tables are needed at this data volume; the materialized-view rollups from Phase 4 (`mv_tenure_cohort_rollup`, `mv_geography_rollup`) are optional performance aids, useful mainly if this model is later scaled up with a much larger customer base.
