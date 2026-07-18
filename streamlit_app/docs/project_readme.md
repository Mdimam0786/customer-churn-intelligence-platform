# Customer Subscription & Churn Intelligence Platform

**Author: Md Imamuddin**

An end-to-end analytics and machine learning platform built on a real customer dataset (IBM Telco Customer Churn, 7,043 customers). The project covers data engineering, SQL, Power BI dashboards, statistics, machine learning, and a live Streamlit app — all built on real data, with no made-up records anywhere.

---

## What This Project Does

The goal is simple: figure out which customers are likely to cancel their subscription, understand why, and turn that into a clear action plan a business can actually use. This project delivers:

- A clean, structured database (star schema) built from real customer data
- 105+ business insights backed by real analysis, not guesses
- Machine learning models for churn prediction, customer lifetime value, segmentation, and upsell targeting
- A 9-dashboard Power BI report with a full set of DAX measures
- A clear, prioritized action plan with real revenue estimates
- A Streamlit web app that lets anyone explore the whole project live

## Key Results

| Metric | Value |
|---|---|
| Customers analyzed | 7,043 (real) |
| Overall churn rate | 26.54% |
| Revenue at risk (already-churned customers) | $139,130.85 / month |
| Churn model accuracy (ROC-AUC) | 0.854 |
| Strongest churn driver | Contract type |
| Best retention opportunity | Moving customers to longer contracts — up to ~$24K/month in protected revenue (estimate) |

## How It's Built

```
Real Data (Excel + CSV)
        ↓
Data Cleaning & ETL
        ↓
Star Schema Database (built for PostgreSQL)
        ↓
SQL Analysis + Exploratory Analysis + Statistics + Machine Learning
        ↓
Power BI Dashboards + Business Recommendations + Streamlit App
```

More detail on the architecture: [docs/technical_design_document.md](docs/technical_design_document.md)

## Tech Stack

Python (pandas, scikit-learn, scipy, numpy), PostgreSQL, SQLite (for local testing), Power BI, Streamlit, Git.

## Project Structure

```
├── config/                  # App settings
├── data/                    # Raw and processed data (real data only)
├── sql/                     # Database schema, views, stored procedures, queries
├── powerbi/                 # DAX measures, theme, data exports
├── streamlit_app/           # The live web app (13 pages) — see below
├── src/
│   ├── data_engineering/    # Data cleaning and loading pipeline
│   ├── eda/                 # Exploratory analysis
│   ├── stats/                # Statistical testing
│   ├── ml/                   # Machine learning models
│   ├── analysis/             # Business impact calculations
│   └── utils/                 # Shared helper code
├── docs/                     # Project reports and guides
│   └── powerbi_build_walkthrough/  # Step-by-step Power BI build guide
└── logs/                      # Program run logs
```

### Streamlit App (`streamlit_app/`)

A live, interactive version of this whole project — 13 pages covering the main dashboard, exploratory analysis, statistics, live SQL queries, search tools, live predictions, model explainability, and project documentation. To run it:

```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

Power BI is still the main reporting tool for this project — the Streamlit app is a companion way to explore it online.

### Power BI Build Guide (`docs/powerbi_build_walkthrough/`)

A full step-by-step guide for building the 9-dashboard Power BI report yourself, one page at a time, including the initial data setup.

## Documentation

| Document | What's Inside |
|---|---|
| [Data Quality Report](docs/data_quality_report.md) | Data cleaning and validation steps |
| [EDA Insights Report](docs/eda_insights_report.md) | 105 business insights |
| [SQL Verification Log](docs/sql_verification_log.md) | SQL queries and results |
| [Power BI Dashboard Guide](docs/powerbi_dashboard_guide.md) | Dashboard specifications |
| [Power BI Data Model](docs/powerbi_data_model.md) | Table relationships and structure |
| [Statistics Report](docs/statistics_report.md) | Hypothesis tests, ANOVA, regression |
| [ML Report](docs/ml_report.md) | Model details and results |
| [BI Synthesis Report](docs/bi_synthesis_report.md) | Business recommendations |
| [Data Dictionary](docs/data_dictionary.md) | Every field explained |
| [Business Glossary](docs/business_glossary.md) | Key terms explained |
| [Technical Design Document](docs/technical_design_document.md) | Architecture and design choices |
| [Project Report](docs/project_report.md) | Full project summary |
| [Resume Bullet Points](docs/resume_bullet_points.md) | Resume-ready bullet points |
| [Interview Questions](docs/interview_questions.md) | Practice questions and answers |
| [Power BI Build Walkthrough](docs/powerbi_build_walkthrough/) | Step-by-step dashboard build guide |
| [GitHub Publishing Checklist](GITHUB_CHECKLIST.md) | Steps to publish this repo |
| [Local Setup Guide](docs/local_vscode_postgres_setup.md) | Running this project in VS Code with PostgreSQL |

## Running This Project

```bash
pip install -r requirements.txt

python3 -m src.data_engineering.etl_pipeline       # Build the database
python3 src/data_engineering/refresh_mat_views.py   # Verify the SQL logic against real data
python3 -m src.eda.eda_analysis                    # Generate insights
python3 -m src.stats.hypothesis_testing             # Run statistical tests
python3 -m src.stats.regression_analysis            # Run regression analysis
python3 -m src.ml.churn_model                        # Train the churn model
python3 -m src.ml.explainability                     # Explain model predictions
python3 -m src.ml.segmentation                       # Run customer segmentation
python3 -m src.ml.ltv_model                          # Train the lifetime value model
python3 -m src.ml.upsell_model                       # Train the upsell model
python3 -m src.analysis.business_impact_analysis     # Calculate business impact
```

You'll need the two real source files (`Telco_customer_churn.xlsx`, `Telco-Customer-Churn.csv`) in `data/raw/` — both are already included in this repository.

## Data Source

This project uses the IBM Telco Customer Churn dataset, a widely used public dataset (also available on Kaggle) for churn analysis. It contains no personal information beyond a customer ID.

## Author

**Md Imamuddin**
[GitHub](https://github.com/mdimamuddin) · [LinkedIn](https://linkedin.com/in/mdimamuddin)
