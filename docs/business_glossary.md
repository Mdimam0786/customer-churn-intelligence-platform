# Business Glossary

Author: Md Imamuddin

**Churn** — A customer who has canceled their service (`Churn Label = Yes`, `Churn Value = 1`). This data is a single snapshot, so "churned" here means "has left as of this snapshot," not a specific date.

**Churn Rate** — The percentage of customers who have churned out of the total customer base. Overall rate in this data: 26.54%.

**Churn Score** — IBM's own 0–100 risk score, included in the source data. It turns out to be well-calibrated against real outcomes — the highest-risk group (decile 10) had a 100% actual churn rate.

**CLTV (Customer Lifetime Value)** — IBM's own estimate of a customer's total value to the company. Ranges from $2,003–$6,500 in this data, averaging $4,400.30. It can only be partly reconstructed from the other fields in this dataset (R² ≈ 0.22) — it likely factors in extra information not included here.

**Tenure** — How many months someone has been a customer (0–72 in this data). Used as the main "time" measure throughout, since the dataset has no real subscription start or renewal date.

**Tenure Cohort** — A 12-month grouping of tenure (like "0–12 months"), used in place of a calendar-based grouping since there are no real dates in the source data.

**RFM (Recency, Frequency, Monetary)** — A common way to score customer value. True RFM needs individual purchase history, which this dataset doesn't have. Instead, this project uses close estimates: tenure stands in for recency, number of add-on services stands in for frequency, and total amount billed stands in for monetary value. These are always labeled as estimates, never presented as the real thing.

**Add-on Services** — The 6 optional services a customer can add beyond basic phone/internet: Online Security, Online Backup, Device Protection, Tech Support, Streaming TV, and Streaming Movies.

**Contract-Based Risk Tier** — A simple, rule-based risk label (High/Medium/Low) based only on contract type — used as an easy-to-understand baseline that the machine learning models are expected to beat.

**Customer Health Score** — A weighted score from 0–100 combining churn risk (40%), tenure (25%), add-on adoption (20%), and contract length (15%). Useful as a simple cross-check against the machine learning model's own prediction.

**MRR (Monthly Recurring Revenue)** — The total of all customers' current monthly charges added together. Current MRR: $456,116.60.

**MRR at Risk** — The portion of MRR that comes from customers who have already churned: $139,130.85.

**Churn Reason** — A real, IBM-documented category explaining why a customer left (for example, "Competitor offered higher download speeds"). Blank for customers who are still active.

**Cramér's V** — A statistical measure (0 to 1) showing how strong the relationship is between two categories. Used to tell the difference between a result that's just "statistically significant" and one that's actually meaningful in practice.

**Cohen's d** — A statistical measure showing how big the difference is between two group averages, used alongside p-values to judge whether a difference actually matters.

**Wilson Score Interval** — A way of calculating a confidence interval for a percentage (like churn rate) that's more accurate than the simple method, especially for smaller groups.

**McFadden's Pseudo-R²** — The standard way to measure how well a logistic regression model fits the data (since regular R² doesn't apply to this kind of model). A value of 0.2–0.4 is considered a strong fit by convention.

**ROC-AUC** — A standard score (0 to 1) for how well a model tells churned and retained customers apart, regardless of what cutoff point you use to make a final yes/no decision.

**Business Cost-Optimized Threshold** — Instead of using the default 50% cutoff for a "will churn" prediction, this is the cutoff that minimizes the estimated real-world cost of getting it wrong.

**Star Schema** — A common database design used in reporting and analytics, with one central "facts" table connected to several "dimension" tables that describe it.

**Segment (K-Means)** — A group of customers found by an unsupervised clustering method, based on tenure, billing, CLTV, and add-on usage. This is a different, separate approach from the RFM-based segments described above.
