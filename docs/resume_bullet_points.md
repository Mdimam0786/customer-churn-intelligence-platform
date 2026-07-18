# Resume Bullet Points

Author: Md Imamuddin

*Pick 3–5 that best match the role you're applying for. All figures below are real, taken directly from this project's output.*

## Data Engineering / Analytics Engineering focus
- Built an end-to-end ETL pipeline transforming a real 7,043-customer telecom dataset into a validated star schema (6 dimensions + 1 fact table) designed for PostgreSQL, achieving 100% referential integrity and identifying and fixing 2 real-world data quality issues.
- Designed and validated a data quality framework (schema checks, domain checks, duplicate checks, and referential checks) achieving a 100% completeness and consistency score across a 33-column real-world dataset.

## SQL / Database focus
- Wrote 10+ advanced PostgreSQL business queries using CTEs, window functions (RANK, ROW_NUMBER, NTILE, LAG), materialized views, and stored procedures to power executive retention, revenue, and cohort reporting.
- Built a rule-based customer health-scoring SQL view combining 4 weighted business signals, cross-checked against machine learning model outputs.

## Business / Data Analyst focus
- Delivered 105+ statistically backed business insights from a real customer churn dataset, identifying contract type as the strongest churn driver (Cramér's V = 0.41) and quantifying $139K in monthly recurring revenue currently at risk.
- Turned churn analysis into a prioritized, numbers-based retention plan projecting up to $26K in protected monthly recurring revenue from a single targeted change (moving customers to automatic payment methods).

## Data Science / Machine Learning focus
- Trained and compared 3 churn prediction models (Logistic Regression, Random Forest, Gradient Boosting) on real customer data, reaching 0.854 test ROC-AUC while deliberately excluding vendor-provided risk scores so the model generalizes to new customers.
- Built a cost-based decision threshold for the churn model, reducing estimated operational cost by 54% compared to the standard 0.5 probability cutoff.
- Built model explainability using permutation importance and local feature-contribution analysis, providing clear global and individual-level explanations for model predictions.
- Built a K-Means customer segmentation model with a statistically validated number of clusters (using silhouette analysis), identifying 5 customer segments with churn rates ranging from 3.7% to 47.6%.

## BI / Power BI focus
- Designed a complete 9-dashboard Power BI reporting suite (Executive, Retention, Churn, Revenue, Segmentation, Subscription, Geographic, Cohort, and ML Prediction dashboards) with a 40+ measure DAX library and interactive field parameters.

## Statistics focus
- Ran a full hypothesis-testing suite (chi-square with Cramér's V, Welch's t-tests with Cohen's d, one-way ANOVA with η², Wilson confidence intervals) on a real 7,043-customer dataset, distinguishing statistically significant results from ones that were also practically meaningful.
- Implemented OLS and logistic regression with full statistical detail (standard errors, p-values, confidence intervals, odds ratios) built directly from the underlying statistical formulas in NumPy and SciPy.
