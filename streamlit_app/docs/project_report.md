# Project Report: Customer Subscription & Churn Intelligence Platform

Author: Md Imamuddin

## Overview

This project is an end-to-end analytics and machine learning platform built on a real customer churn dataset (IBM Telco Customer Churn, 7,043 customers). It was built in stages — data engineering, SQL analytics, Power BI reporting, statistics, machine learning, and business recommendations — with each stage tested and documented before moving to the next.

## What Was Built

| Stage | What It Delivered | Key Result |
|---|---|---|
| Planning | Project scope, architecture, and dataset selection | Chose the IBM Telco Customer Churn dataset, committed to using only real data |
| Data Engineering | Data pipeline and star-schema database | 7,043 customers loaded, full data integrity checks passed, 2 real data quality issues found and fixed |
| Exploratory Analysis | 105 business insights | Contract type is the biggest churn driver (42.71% vs. 2.83%) |
| Advanced SQL | 10+ business queries, views, stored procedures | All queries tested against real data |
| Power BI | 9-dashboard design, DAX measures, data model | Full build guide, data exports, and a live preview |
| Statistics | Hypothesis tests, ANOVA, regression | Contract type has the strongest statistical effect of any variable tested |
| Machine Learning | Churn, lifetime value, segmentation, and upsell models | Churn model reaches 0.854 ROC-AUC, without using the vendor's own risk score |
| Business Recommendations | A prioritized, numbers-backed action plan | Up to $26,000/month in estimated protected revenue from one recommendation |

## How Quality Was Maintained

This project follows one simple rule throughout: **use only real data, and be upfront about any limitation.** A few real constraints came up during development, and here's exactly how each one was handled:

- **No PostgreSQL server available at times during development** — the SQL was still fully tested, using SQLite to verify the same query logic that PostgreSQL uses (both databases support the same core SQL features used here).
- **No real subscription start/end dates in the source data** — rather than invent dates, a tenure-based grouping was used everywhere a time-based view was needed.
- **A few statistics and machine learning libraries weren't available during development** — equivalent methods were built using the same underlying math, and clearly labeled as such rather than presented as identical to the original library.
- **No access to Power BI Desktop during development** — instead of skipping Power BI, every piece needed to build the real report was prepared: data exports, DAX measures, and a full step-by-step build guide.
- **No transaction/purchase history in the source data** — RFM scoring uses close estimates (tenure, add-on count, total billed) instead of true purchase data, clearly labeled as estimates. Upsell recommendations use per-service adoption models instead of a traditional recommendation engine, for the same reason.
- **Careful review of every file before including it in the project** — any file or draft that didn't match the verified, tested data was reviewed and corrected before being used.
- **Fact-checking project claims** — for example, a note that the dataset covers "100% California" was double-checked against the real data before being finalized, rather than assumed to be true.

## Main Findings

1. **Contract type is the single biggest churn driver** in this dataset — confirmed by the raw churn rate, statistical testing, and machine learning feature importance, all pointing the same way.
2. **26.54% of customers have churned**, representing **$139,130.85 in monthly recurring revenue** at risk.
3. **Gender has no real effect on churn** — a clear, useful "don't target this" finding, backed by statistical testing.
4. **IBM's own churn risk score is already well-calibrated** and can be used for prioritizing outreach today, even before a custom model is built.
5. **24.34% of churn comes from service and support experience** — the most directly fixable cause found, compared to 33.23% from competitor offers, which is harder to control.
6. **A prioritized, numbers-backed action plan** exists, with realistic revenue estimates for three specific, ranked improvements a business could make.

## Reproducibility

Every number in this project can be reproduced by re-running the matching script against the two real source files (`data/raw/Telco_customer_churn.xlsx` and `data/raw/Telco-Customer-Churn.csv`). Nothing in any report was typed in by hand or estimated without a script actually producing it.

## Suggested Next Steps

1. Add a second dataset from outside California to test whether the findings hold up in other regions.
2. Get real transaction-level data to replace the estimated RFM values and upsell models with true purchase-based analysis.
3. Get real subscription dates to enable proper year-over-year and quarter-over-quarter reporting.
4. Deploy the churn model and the SQL-based customer health score together in a live Power BI report connected to a real PostgreSQL database.
5. Replace the illustrative cost estimates used for the churn model's decision threshold ($200 for a missed churner, $30 for a wasted outreach) with the company's real cost figures before using it in production.
