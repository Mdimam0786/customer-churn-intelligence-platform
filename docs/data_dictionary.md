# Data Dictionary

Author: Md Imamuddin

## 1. Raw Source Fields (IBM Telco Customer Churn — Excel File)

| Field | Type | Description | Example |
|---|---|---|---|
| CustomerID | String | Unique customer identifier | `3668-QPYBK` |
| Country / State / City / Zip Code | String | Real location data (100% California, 1,129 cities) | `United States / California / Los Angeles / 90003` |
| Latitude / Longitude | Decimal | Real map coordinates | `33.964131 / -118.272783` |
| Gender | String | `Male` / `Female` | |
| Senior Citizen | String | `Yes` / `No` | |
| Partner / Dependents | String | `Yes` / `No` — household details | |
| Tenure Months | Integer | How many months someone has been a customer (0–72) | `34` |
| Phone Service / Internet Service | String | What type of connection they have | `Fiber optic` |
| Multiple Lines, Online Security, Online Backup, Device Protection, Tech Support, Streaming TV, Streaming Movies | String | `Yes` / `No` / `No internet service` (or `No phone service`) | |
| Contract | String | `Month-to-month` / `One year` / `Two year` | |
| Paperless Billing | String | `Yes` / `No` | |
| Payment Method | String | 4 categories (see below) | `Electronic check` |
| Monthly Charges | Decimal | Current monthly bill | `70.35` |
| Total Charges | Decimal | Total amount billed so far | `1397.475` |
| Churn Label | String | `Yes` / `No` | |
| Churn Value | Integer | 0 or 1, always matches Churn Label | |
| Churn Score | Integer | IBM's own risk score, 0–100 | `86` |
| CLTV | Integer | IBM's own customer lifetime value estimate | `4400` |
| Churn Reason | String | Why they left (blank if still active); 20 real reasons for customers who churned | `Competitor offered higher download speeds` |

## 2. Cross-Reference File (Standard CSV)

Same customers as the main file, but with fewer columns (customer ID, basic demographics, service and billing fields, and churn status). This file was only used to double-check the main dataset — it wasn't loaded directly into the database.

## 3. Fields Added During Data Cleaning

| Field | How It's Calculated | Notes |
|---|---|---|
| `tenure_cohort` | Groups `tenure_months` into ranges (0-12, 13-24, ... 61-72 months) | Used as a stand-in for a calendar-based time grouping, since the data has no real subscription dates |
| `addon_service_count` | Counts how many of the 6 add-on services are set to "Yes" | Ranges from 0 to 6 |
| `has_internet`, `has_phone_and_internet`, `is_streaming_bundle` | True/false flags built from the real service fields | |
| `avg_revenue_per_tenure_month` | `total_charges / tenure_months` (uses `monthly_charges` for brand-new customers with 0 months tenure) | |
| `contract_based_risk_tier` | Simple rule: Month-to-month = High risk, One year = Medium, Two year = Low | Used as a baseline to compare the machine learning model against |
| `recency_tenure_months`, `frequency_addon_breadth`, `monetary_total_charges` | Estimated RFM values (Recency, Frequency, Monetary) | These are estimates, not calculated from real purchase history, since the dataset doesn't include one |
| `is_new_customer_imputed_charges` | Marks the 11 customers whose Total Charges had to be filled in (they were brand new, with 0 months of billing history) | |

## 4. Database Fact Table (`fact_subscription`)

One row per customer (this is a snapshot of current data, not a history of events over time). See `sql/schema/02_fact.sql` for the full table definition.

## 5. Database Dimension Tables

| Table | Number of Rows | What Each Row Represents |
|---|---|---|
| `dim_customer` | 7,043 | One customer |
| `dim_geography` | 1,652 | One city + zip code combination |
| `dim_plan` | 1,255 | One combination of contract and services |
| `dim_payment_method` | 4 | One payment method |
| `dim_tenure_cohort` | 6 | One tenure range |
| `dim_churn_reason` | 21 | One churn reason (or "Not Applicable") |

## 6. Machine Learning Output Fields

| Field | Where It Comes From | Range | Notes |
|---|---|---|---|
| Churn probability | The trained Gradient Boosting model | 0.0–1.0 | Doesn't use IBM's own `churn_score` or `cltv` as inputs |
| `churn_score_decile` | Splits `churn_score` into 10 equal groups | 1–10 | 10 means highest risk |
| `rfm_segment` | Based on the estimated RFM scores | Champion / Loyal / Steady / At Risk / Critical-New | |
| `customer_health_score` | A weighted score combining 4 factors | 0–100 | 40% churn risk + 25% tenure + 20% add-ons + 15% contract type |
| Customer segment (from K-Means clustering) | Machine learning segmentation, 5 groups | 0–4 | See `docs/ml_report.md` for details on each group |
