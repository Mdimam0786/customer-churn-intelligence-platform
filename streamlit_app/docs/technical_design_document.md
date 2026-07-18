# Technical Design Document

Author: Md Imamuddin

## 1. System Architecture

```
Real IBM Telco Customer Churn Data (Excel + CSV)
            │
            ▼
   Data Engineering Layer (src/data_engineering/)
   ingest → validate → clean → feature_engineer → etl_pipeline
            │
            ▼
   Star Schema (sql/schema/) — 6 dimension tables + 1 fact table
   Built for PostgreSQL 14+, also tested locally in SQLite
            │
     ┌──────┼──────────────┬──────────────┐
     ▼      ▼              ▼              ▼
   SQL    EDA (src/eda)  Stats (src/stats) ML (src/ml)
 Analytics                                   │
     │                                       ▼
     └──────────────► Power BI ◄──── Business Insights (src/analysis)
                    (9 dashboards)
```

## 2. Key Design Decisions

### 2.1 No fake calendar dates
The source data doesn't include a real subscription start or renewal date — only how many months someone has been a customer (tenure). Rather than invent dates just to build a standard date table, this project uses a tenure-based grouping (`dim_tenure_cohort`) as its time axis across SQL, Power BI, and the statistics work. This was a deliberate choice to avoid adding data that isn't real.

### 2.2 SQLite used for local testing, PostgreSQL for production
All database scripts (tables, views, stored procedures) are written for PostgreSQL 14+. During development, a local PostgreSQL server wasn't always available, so the core query logic (CTEs and window functions, which work the same way in both databases) was tested in SQLite first. Some PostgreSQL-specific features — materialized views and stored procedures — don't exist in SQLite, so their underlying `SELECT` logic was tested separately. See `docs/sql_verification_log.md` for the full results, and `docs/local_vscode_postgres_setup.md` for running everything against a real PostgreSQL database.

### 2.3 Leaving out the vendor's churn score and CLTV from the model's inputs
IBM's data includes its own churn risk score and customer lifetime value estimate. These were deliberately left out of the machine learning models' input features — including them would let the model just copy IBM's own answer instead of learning from the real, independent business data. This keeps the model useful for brand-new customers who won't have a vendor-provided score yet.

### 2.4 Library choices
A few well-known libraries (`statsmodels`, `XGBoost`, `LightGBM`, `shap`) weren't available during development. Here's what was used instead, and why it still gives real, correct results:
- **Regression statistics:** built directly using the same mathematical formulas that `statsmodels` uses internally (see `src/stats/regression_analysis.py`)
- **Gradient boosting:** scikit-learn's `GradientBoostingClassifier` and `Regressor` — a genuine, different implementation, not a stand-in
- **Model explainability:** permutation importance and a feature-contribution method, which are standard, well-established techniques — not the same as SHAP, but not an imitation of it either

### 2.5 Power BI without a `.pbix` file
A `.pbix` file can only be created inside Power BI Desktop itself. Since that wasn't available during development, this project instead includes everything needed to build the real report quickly: ready-to-import data files, full documentation of the data model, a complete set of DAX measures, and a step-by-step build guide for all 9 dashboard pages.

### 2.6 RFM scoring uses estimates, not true purchase history
This dataset doesn't include a transaction log, so true Recency/Frequency/Monetary analysis (based on individual purchases) isn't possible. Instead, this project uses close estimates — tenure, number of add-on services, and total amount billed — clearly labeled as estimates everywhere they appear (SQL, Power BI, and the machine learning code).

### 2.7 Upsell recommendations without purchase history
A true product recommendation engine needs purchase history, which this dataset doesn't have. Instead, this project trains one classifier per add-on service to predict which customers are most similar to current subscribers of that service — a solid, real signal for targeting, built from the data that's actually available.

## 3. Reproducing the Results

Every step below can be re-run against the same real data to get the same results:
```bash
python3 -m src.data_engineering.etl_pipeline        # Build the database
python3 src/data_engineering/refresh_mat_views.py   # Verify the SQL logic
python3 -m src.eda.eda_analysis                     # Generate insights
python3 -m src.stats.hypothesis_testing             # Run hypothesis tests
python3 -m src.stats.regression_analysis            # Run regression analysis
python3 -m src.ml.churn_model                       # Train the churn model
python3 -m src.ml.explainability                    # Explain model predictions
python3 -m src.ml.segmentation                      # Run customer segmentation
python3 -m src.ml.ltv_model                         # Train the lifetime value model
python3 -m src.ml.upsell_model                      # Train the upsell model
python3 -m src.analysis.business_impact_analysis    # Calculate business impact
```

## 4. Coding Standards

- Code follows PEP 8 formatting
- Shared logic (like logging) lives in one place (`src/utils/logger.py`) instead of being repeated in every file
- Logging is structured and timestamped, written to both the console and a log file
- Data checks use clear error handling (`assert`/`raise`) instead of failing silently
- Settings are centralized in `config/config.yaml` rather than scattered across scripts
- `requirements.txt` lists all dependencies with version numbers
- The folder structure separates data, SQL, source code, and documentation clearly — the same way a real analytics team would organize a project

## 5. Known Limitations

| Limitation | Where It Applies | How It Was Handled |
|---|---|---|
| No PostgreSQL server available during parts of development | Data pipeline, SQL | Verified core query logic in SQLite instead |
| No real calendar dates in the source data | Data pipeline, EDA, SQL, Power BI | Used tenure-based grouping instead |
| A few libraries (`statsmodels`, `XGBoost`, `LightGBM`, `shap`) weren't available during development | Statistics, Machine Learning | Used equivalent methods built from the same math, clearly documented |
| No Power BI Desktop available during development | Power BI | Provided a full build guide, data exports, and DAX measures instead |
| No purchase/transaction history in the source data | Machine Learning | Used estimated RFM values and per-service adoption models instead |
| Customer lifetime value is only moderately predictable from the available fields (R² ≈ 0.22) | Machine Learning | Reported honestly — IBM's CLTV value likely uses additional data not included in this dataset |
