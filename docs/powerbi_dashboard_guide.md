# Power BI Dashboard Build Guide — 9 Executive Dashboards

Author: Md Imamuddin

*Follow this guide in Power BI Desktop after completing the data model setup in `powerbi_data_model.md` and pasting in the measures from `dax_measures.md`. Every field and measure referenced below is real and already exists in the model — nothing here requires data that doesn't exist.*

---

## Dashboard 1 — Executive Overview

**Stakeholder:** CEO / Executive Team
**Decision it supports:** "Is the business healthy right now, and where's the biggest risk?"

| Visual | Fields | Purpose |
|---|---|---|
| KPI Cards (row of 5) | `[Total Customers]`, `[Churn Rate % (Formatted)]`, `[Total Billed Revenue (Formatted)]`, `[Current MRR]`, `[MRR At Risk (Formatted)]` | Single-glance headline health check |
| Donut chart | `churn_flag` (Retained/Churned) | Visual proportion of churned vs retained |
| Bar chart | `contract_type` × `[Churn Rate %]`, colored by `[Churn Rate KPI Color]` | Immediately shows contract type is the top risk driver |
| Line/area chart | `tenure_cohort_label` (sorted by `sort_order`) × `[Cumulative Revenue Through Cohort]` | Shows how revenue compounds with tenure |
| Table | Top 10 rows from `vw_customer_health_score` (SQL view), lowest health score first | Direct "who to call today" list |

**Navigation:** buttons linking to Retention, Churn, and Revenue dashboards. **Bookmark:** "Default View" resets all slicers.

---

## Dashboard 2 — Retention Dashboard

**Stakeholder:** VP of Customer Success
**Decision it supports:** "Where in the customer lifecycle are we losing people, and is it getting better or worse?"

| Visual | Fields | Purpose |
|---|---|---|
| Line chart | `tenure_cohort_label` (sorted) × `[Cohort Churn Rate %]` | The core retention curve — shows the steep early-tenure drop-off |
| Column chart with reference line | `[Cohort-over-Cohort Churn Rate Change]` per cohort | Highlights where retention improves/worsens most sharply cohort-to-cohort |
| Matrix | `contract_type` (rows) × `tenure_cohort_label` (columns) × `[Churn Rate %]` (values) | Cross-tab showing the compounding effect of contract type AND tenure together |
| Card | `[Rolling 3-Cohort Avg Churn Rate]` | Smoothed trend indicator |
| Slicer | `dim_customer[has_partner]`, `dim_customer[has_dependents]` | Lets CS filter to household-stability segments (Phase 3 Insight 58–61) |

**Drill-through:** right-click any cohort bar → drill through to a filtered customer list table.

---

## Dashboard 3 — Churn Dashboard

**Stakeholder:** VP of Customer Success + Product
**Decision it supports:** "Why are people actually leaving, and what should we fix first?"

| Visual | Fields | Purpose |
|---|---|---|
| Treemap | `churn_reason` sized by `churned_customers` | Visual Pareto of root causes (Phase 3 Section H) |
| Bar chart | `churn_reason` × `[MRR At Risk (Churned)]`, sorted descending | Ranks reasons by dollar impact, not just count |
| KPI card | `Cumulative % of top 5 reasons` (from Phase 4 KPI 10 Pareto query) | "44.78% of churn from just 5 causes" headline stat |
| Stacked bar | `internet_service` × `contract_type`, colored by `[Churn Rate %]` | Shows the two strongest categorical drivers together |
| Tooltip page | Hover any churn_reason bar → dynamic tooltip showing avg tenure, avg monthly charge for that reason | Adds context without cluttering the main visual |

---

## Dashboard 4 — Revenue Dashboard

**Stakeholder:** Finance / RevOps
**Decision it supports:** "Where does our revenue actually come from, and how exposed is it?"

| Visual | Fields | Purpose |
|---|---|---|
| KPI Cards | `[Total Billed Revenue]`, `[Current MRR]`, `[Revenue at Risk % of Total]` | Financial headline |
| Waterfall-style bar | Revenue by `contract_type` | Shows two-year contracts generate the most revenue despite fewest customers |
| Area chart | `tenure_cohort_label` × `[Cumulative Revenue Through Cohort]` | Revenue build-up curve across the customer base |
| Scatter plot | X = `tenure_months`, Y = `monthly_charges`, size = `cltv`, color = `churn_flag` | Visualizes Phase 3 Insight 104 (new, high-paying customers = highest-risk combination) |
| Card | `[Top 20% CLTV Revenue Share]` | Revenue concentration headline |

---

## Dashboard 5 — Customer Segmentation Dashboard

**Stakeholder:** Marketing + Product
**Decision it supports:** "Who are our different customer types, and how do they behave?"

| Visual | Fields | Purpose |
|---|---|---|
| Field-parameter-driven bar chart | "Segment By" field parameter × `[Churn Rate %]` | One flexible chart replaces 6 static ones |
| Scatter plot | `rfm_recency_quintile` (X) × `rfm_monetary_quintile` (Y), size = customer count, color = `rfm_segment` | Classic RFM quadrant visualization |
| Donut | `rfm_segment` distribution | Segment size at a glance |
| Table | `rfm_segment` × `[Churn Rate %]`, `[Average CLTV]` | Confirms Champions churn least, Critical/New churns most (Phase 4 verification) |

---

## Dashboard 6 — Subscription Analysis Dashboard

**Stakeholder:** Product Manager
**Decision it supports:** "Which plans/services should we promote, bundle, or redesign?"

| Visual | Fields | Purpose |
|---|---|---|
| Matrix | `internet_service` × `contract_type` × `[Churn Rate %]` | Full plan-combination risk grid |
| Bar chart | `addon_service_count` × `[Churn Rate %]` | Shows the non-monotonic 1-addon spike (Phase 3 Insight 35) — deliberately NOT smoothed over |
| Line chart | `addon_service_count` × `[Average Monthly Charges]` | Shows revenue-per-addon-tier alongside churn for side-by-side reading |
| Card | `% of customers with full 6-service bundle` | Upsell opportunity headline (4.03%, Phase 3 Insight 44) |

---

## Dashboard 7 — Geographic Dashboard

**Stakeholder:** Regional Ops / Marketing
**Decision it supports:** "Are there specific markets that need attention?"

| Visual | Fields | Purpose |
|---|---|---|
| Map (bubble) | `latitude`/`longitude` from `dim_geography`, size = customer count, color = `[Churn Rate %]` | Geographic churn hot-spot view |
| Table | Top 15 cities by revenue (min. 30 customers, per Phase 4 KPI 6) | Enforces the same small-sample-size guardrail used in the SQL layer |
| Card | "100% California — 1,129 cities" | Explicit scope label so this is never mistaken for a national view |

**Filter guardrail:** apply a visual-level filter `customers >= 30` on the map and table by default, matching the Phase 4 SQL `HAVING` clause, to avoid the noisy small-city distortion documented in Phase 3 Insight 91.

---

## Dashboard 8 — Cohort Dashboard

**Stakeholder:** Analytics Manager / CS
**Decision it supports:** "How does customer behavior evolve through the tenure lifecycle?"

| Visual | Fields | Purpose |
|---|---|---|
| Field-parameter-driven line chart | "Metric to Chart" parameter × `tenure_cohort_label` (sorted) | Toggle between churn rate / CLTV / revenue / tenure on one chart |
| Bar chart | `tenure_cohort_label` × customer count | Shows the 0–12mo cohort is both riskiest AND largest |
| Table | Full `mv_tenure_cohort_rollup` materialized-view output | Direct pull from the Phase 4 pre-aggregated rollup |

---

## Dashboard 9 — ML Prediction Dashboard

**Stakeholder:** Data/Analytics Manager, CS leadership
**Decision it supports:** "How much can we trust the churn score today, and who are our highest-confidence risk cases?"

| Visual | Fields | Purpose |
|---|---|---|
| Line chart | `churn_score_decile` × `[Actual Churn Rate by Decile]` | The calibration curve — proves Deciles 8–10 capture nearly all real churn |
| Card | `[Model Calibration Gap]` (aggregated) | Single trust metric for the score's reliability |
| Table | Output of `fn_get_high_risk_customers(80)` (Phase 4 SQL function) | The literal, ready-to-call outreach list |
| Note: this dashboard will be extended in Phase 7 once the custom ML model (beyond IBM's provided score) is built, to show model vs. score side-by-side. | | |

---

## Cross-Dashboard Features

- **Bookmarks:** "Default View" (all filters cleared) on every dashboard page, plus "At-Risk Focus" bookmark (pre-filters `health_tier = "At Risk"`) available on Overview, Retention, and ML Prediction pages.
- **Drill-through:** every dashboard with a `contract_type`, `tenure_cohort_label`, or `city` visual supports right-click drill-through to a common "Customer Detail" page showing the individual customer table filtered to that selection.
- **Dynamic tooltips:** custom tooltip page showing tenure, monthly charge, CLTV, and churn score for any customer/segment hovered, used across Churn, Segmentation, and Cohort dashboards.
- **Theme:** a single custom JSON theme file (`powerbi/theme.json`, referenced below) applied to all 9 pages for visual consistency.
- **Navigation bar:** a persistent left-side navigation bar (built with bookmark-triggered buttons) present on all pages, linking to each of the 9 dashboards.

See the mockup previews below for a visual sense of Dashboards 1 and 3 before building in Power BI Desktop.
