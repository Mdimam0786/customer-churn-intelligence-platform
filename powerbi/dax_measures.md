# Power BI DAX Measures Library

Author: Md Imamuddin

*Written against the Phase 2 star schema (`fact_subscription` + 6 dimension tables). Import the CSVs in `powerbi/data_export/` into Power BI Desktop, build the relationships per `docs/powerbi_data_model.md`, then paste these measures into a dedicated `_Measures` table (best practice: create a disconnected table named `_Measures` to hold all of them, rather than scattering measures across fact/dim tables).*

**Note on time intelligence:** this dataset has no real calendar subscription-start or renewal date — only elapsed `tenure_months` (see Phase 2/3 documentation). Genuine Power BI time intelligence functions (`TOTALYTD`, `SAMEPERIODLASTYEAR`, `DATEADD`) require a real date column tied to a marked date table, which does not exist here. Rather than fabricate a synthetic date, this library substitutes **tenure-cohort-over-cohort** comparisons (using `dim_tenure_cohort.sort_order` as the ordering axis) everywhere a calendar-based "YoY/QoQ" measure would normally go, and labels every such measure clearly as a cohort-based proxy. If a future version of this project incorporates a dataset with real transaction dates, these measures are the ones to replace with true `DATEADD`-based time intelligence.

---

## 1. Core KPI Measures

```dax
Total Customers = DISTINCTCOUNT(fact_subscription[customer_key])

Churned Customers = CALCULATE([Total Customers], fact_subscription[churn_flag] = 1)

Retained Customers = CALCULATE([Total Customers], fact_subscription[churn_flag] = 0)

Churn Rate % =
DIVIDE([Churned Customers], [Total Customers], 0)

Retention Rate % = 1 - [Churn Rate %]

Total Billed Revenue = SUM(fact_subscription[total_charges])

Current MRR = SUM(fact_subscription[monthly_charges])

MRR At Risk (Churned) =
CALCULATE(SUM(fact_subscription[monthly_charges]), fact_subscription[churn_flag] = 1)

Average CLTV = AVERAGE(fact_subscription[cltv])

Average Tenure (Months) = AVERAGE(fact_subscription[tenure_months])

Average Monthly Charges = AVERAGE(fact_subscription[monthly_charges])

Average Add-on Services = AVERAGE(fact_subscription[addon_service_count])
```

---

## 2. Revenue & Financial Impact Measures

```dax
Revenue per Customer = DIVIDE([Total Billed Revenue], [Total Customers], 0)

% of Total Revenue =
DIVIDE([Total Billed Revenue], CALCULATE([Total Billed Revenue], ALL(dim_plan)), 0)

Revenue at Risk % of Total =
DIVIDE([MRR At Risk (Churned)], [Current MRR], 0)

Top 20% CLTV Revenue Share =
VAR CustomerRank =
    RANKX(ALL(fact_subscription), fact_subscription[cltv], , DESC)
VAR TotalCustomerCount = [Total Customers]
VAR Top20Cutoff = ROUNDUP(TotalCustomerCount * 0.2, 0)
RETURN
    DIVIDE(
        CALCULATE([Total Billed Revenue], FILTER(ALL(fact_subscription), CustomerRank <= Top20Cutoff)),
        [Total Billed Revenue]
    )

Avg Revenue per Tenure Month = AVERAGE(fact_subscription[avg_revenue_per_tenure_month])
```

---

## 3. Tenure-Cohort "Time Intelligence" Proxy Measures

*(Substitutes for calendar-based time intelligence — see note above.)*

```dax
Cohort Churn Rate % (Current Filter Context) = [Churn Rate %]

Prior Cohort Churn Rate % =
VAR CurrentSortOrder = SELECTEDVALUE(dim_tenure_cohort[sort_order])
VAR PriorSortOrder = CurrentSortOrder - 1
RETURN
    CALCULATE(
        [Churn Rate %],
        ALL(dim_tenure_cohort),
        dim_tenure_cohort[sort_order] = PriorSortOrder
    )

Cohort-over-Cohort Churn Rate Change =
[Cohort Churn Rate % (Current Filter Context)] - [Prior Cohort Churn Rate %]

Cumulative Revenue Through Cohort =
CALCULATE(
    [Total Billed Revenue],
    FILTER(
        ALL(dim_tenure_cohort),
        dim_tenure_cohort[sort_order] <= MAX(dim_tenure_cohort[sort_order])
    )
)

Cumulative Customers Through Cohort =
CALCULATE(
    [Total Customers],
    FILTER(
        ALL(dim_tenure_cohort),
        dim_tenure_cohort[sort_order] <= MAX(dim_tenure_cohort[sort_order])
    )
)
```

---

## 4. Rolling / Ranking Measures

```dax
Customer CLTV Rank (Overall) =
RANKX(ALL(fact_subscription), fact_subscription[cltv], , DESC)

Customer CLTV Rank within Contract Type =
RANKX(
    ALLEXCEPT(fact_subscription, dim_plan[contract_type]),
    fact_subscription[cltv], , DESC
)

Churn Risk Rank by Contract Type =
RANKX(ALL(dim_plan[contract_type]), [Churn Rate %], , DESC)

Rolling 3-Cohort Avg Churn Rate =
VAR CurrentSort = SELECTEDVALUE(dim_tenure_cohort[sort_order])
RETURN
    CALCULATE(
        [Churn Rate %],
        FILTER(
            ALL(dim_tenure_cohort),
            dim_tenure_cohort[sort_order] <= CurrentSort
                && dim_tenure_cohort[sort_order] > CurrentSort - 3
        )
    )
```

---

## 5. RFM Proxy Segmentation Measures

```dax
RFM Recency Quintile =
VAR R = SELECTEDVALUE(fact_subscription[recency_tenure_months])
RETURN
    SWITCH(
        TRUE(),
        R >= PERCENTILEX.INC(ALL(fact_subscription), fact_subscription[recency_tenure_months], 0.8), 5,
        R >= PERCENTILEX.INC(ALL(fact_subscription), fact_subscription[recency_tenure_months], 0.6), 4,
        R >= PERCENTILEX.INC(ALL(fact_subscription), fact_subscription[recency_tenure_months], 0.4), 3,
        R >= PERCENTILEX.INC(ALL(fact_subscription), fact_subscription[recency_tenure_months], 0.2), 2,
        1
    )

-- Frequency and Monetary quintiles follow the identical PERCENTILEX.INC
-- pattern substituting frequency_addon_breadth and monetary_total_charges.
-- (Precomputing these as calculated columns in Power Query is recommended
-- over row-context DAX measures for performance at scale — see
-- docs/powerbi_data_model.md Section 4.)

RFM Segment Label =
VAR TotalScore = [RFM Recency Quintile] + [RFM Frequency Quintile] + [RFM Monetary Quintile]
RETURN
    SWITCH(
        TRUE(),
        TotalScore >= 13, "Champion",
        TotalScore >= 10, "Loyal",
        TotalScore >= 7,  "Steady",
        TotalScore >= 4,  "At Risk",
        "Critical / New"
    )
```

---

## 6. Customer Health Score Measures

```dax
Health Score - Churn Risk Component =
100 - AVERAGE(fact_subscription[churn_score])

Health Score - Tenure Component =
MIN(100, DIVIDE(AVERAGE(fact_subscription[tenure_months]) * 100, 72))

Health Score - Addon Component =
MIN(100, DIVIDE(AVERAGE(fact_subscription[addon_service_count]) * 100, 6))

Health Score - Contract Component =
SWITCH(
    SELECTEDVALUE(dim_plan[contract_type]),
    "Two year", 100,
    "One year", 60,
    20
)

Customer Health Score =
0.40 * [Health Score - Churn Risk Component] +
0.25 * [Health Score - Tenure Component] +
0.20 * [Health Score - Addon Component] +
0.15 * [Health Score - Contract Component]

Health Tier =
SWITCH(
    TRUE(),
    [Customer Health Score] >= 70, "Healthy",
    [Customer Health Score] >= 45, "Watch",
    "At Risk"
)
```

---

## 7. Churn Score Calibration Measures (for ML Prediction Dashboard)

```dax
Avg Churn Score = AVERAGE(fact_subscription[churn_score])

Churn Score Decile =
-- Precomputed as a calculated column via Power Query / SQL NTILE(10)
-- rather than a measure, since decile assignment must be stable
-- regardless of the current visual's filter context.
SELECTEDVALUE(fact_subscription[churn_score_decile])

Actual Churn Rate by Decile = [Churn Rate %]

Model Calibration Gap =
-- Compares IBM's provided churn_score (scaled 0-100) against actual
-- observed churn rate within the same decile, as a sanity check that
-- the Phase 7 ML model should also pass.
ABS([Avg Churn Score] / 100 - [Actual Churn Rate by Decile])
```

---

## 8. Formatted Display Measures (for KPI cards)

```dax
Churn Rate % (Formatted) = FORMAT([Churn Rate %], "0.0%")

Total Billed Revenue (Formatted) = FORMAT([Total Billed Revenue], "$#,##0,,\"M\"")

MRR At Risk (Formatted) = FORMAT([MRR At Risk (Churned)], "$#,##0")

Churn Rate KPI Color =
-- Used to drive conditional formatting on cards
SWITCH(
    TRUE(),
    [Churn Rate %] >= 0.35, "#D62728",
    [Churn Rate %] >= 0.20, "#FF7F0E",
    "#2CA02C"
)
```

---

## Notes on Implementation

- All measures reference real fields established in the Phase 2 star schema (`fact_subscription`, `dim_plan`, `dim_tenure_cohort`, etc.) — none introduce a field that doesn't exist in the real data.
- RFM quintile measures are shown in DAX for completeness, but per the comment above, precomputing `recency_quintile` / `frequency_quintile` / `monetary_quintile` as calculated columns during Power Query load (or carrying them over from the SQL `NTILE()` version already built in Phase 4) will perform far better on a 7,043-row fact table than recalculating `PERCENTILEX.INC` per-visual.
- `churn_score_decile` should likewise be loaded as a column (Phase 4's SQL already computes it) rather than calculated live in DAX.
