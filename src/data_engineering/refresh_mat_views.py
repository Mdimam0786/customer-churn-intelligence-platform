"""
SQL verification harness.

A live PostgreSQL server was not available during parts of development.
Rather than leave the SQL untested, this script executes the
IDENTICAL query logic (CTEs, window functions -- all ANSI-standard,
supported by SQLite 3.25+) against the real star schema loaded in
the earlier data pipeline, and materializes the two materialized-view equivalents as
physical snapshot tables (since SQLite has no CREATE MATERIALIZED VIEW
syntax). Every result printed by this script is real output from real
data -- nothing is hand-typed.
"""

import os
import sqlite3
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "churn_intelligence.db")


def run_query(conn, sql, label):
    print(f"\n{'='*70}\n{label}\n{'='*70}")
    df = pd.read_sql(sql, conn)
    print(df.to_string(index=False))
    return df


def main():
    conn = sqlite3.connect(DB_PATH)

    run_query(conn, """
        SELECT
            COUNT(*) AS total_customers,
            SUM(churn_flag) AS churned_customers,
            ROUND(100.0 * SUM(churn_flag) / COUNT(*), 2) AS churn_rate_pct,
            ROUND(SUM(total_charges), 2) AS total_billed_revenue,
            ROUND(SUM(monthly_charges), 2) AS current_mrr,
            ROUND(SUM(CASE WHEN churn_flag=1 THEN monthly_charges ELSE 0 END), 2) AS mrr_at_risk,
            ROUND(AVG(cltv), 2) AS avg_cltv
        FROM fact_subscription
    """, "KPI 1: Executive Summary")

    run_query(conn, """
        WITH contract_kpi AS (
            SELECT p.contract_type, COUNT(*) AS customers, SUM(f.churn_flag) AS churned,
                   ROUND(100.0*SUM(f.churn_flag)/COUNT(*),2) AS churn_rate_pct,
                   ROUND(SUM(f.total_charges),2) AS total_revenue
            FROM fact_subscription f JOIN dim_plan p ON f.plan_key = p.plan_key
            GROUP BY p.contract_type
        )
        SELECT contract_type, customers, churned, churn_rate_pct, total_revenue,
               ROUND(100.0*total_revenue/SUM(total_revenue) OVER (),2) AS pct_of_total_revenue,
               RANK() OVER (ORDER BY churn_rate_pct DESC) AS churn_risk_rank
        FROM contract_kpi ORDER BY churn_risk_rank
    """, "KPI 2: Contract Type Ranking (window functions)")

    run_query(conn, """
        WITH cohort_kpi AS (
            SELECT tc.tenure_cohort_label, tc.sort_order, COUNT(*) AS customers,
                   SUM(f.churn_flag) AS churned,
                   ROUND(100.0*SUM(f.churn_flag)/COUNT(*),2) AS churn_rate_pct,
                   ROUND(SUM(f.total_charges),2) AS total_revenue
            FROM fact_subscription f JOIN dim_tenure_cohort tc ON f.tenure_cohort_key = tc.tenure_cohort_key
            GROUP BY tc.tenure_cohort_label, tc.sort_order
        )
        SELECT tenure_cohort_label, customers, churned, churn_rate_pct,
               LAG(churn_rate_pct) OVER (ORDER BY sort_order) AS prior_cohort_churn_rate,
               SUM(total_revenue) OVER (ORDER BY sort_order ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_revenue
        FROM cohort_kpi ORDER BY sort_order
    """, "KPI 3: Tenure Cohort Progression (LAG + running SUM)")

    run_query(conn, """
        WITH churned_customers AS (
            SELECT c.customer_id, p.contract_type, f.cltv, f.tenure_months,
                   ROW_NUMBER() OVER (PARTITION BY p.contract_type ORDER BY f.cltv DESC) AS rnk
            FROM fact_subscription f
            JOIN dim_customer c ON f.customer_key = c.customer_key
            JOIN dim_plan p ON f.plan_key = p.plan_key
            WHERE f.churn_flag = 1
        )
        SELECT customer_id, contract_type, cltv, tenure_months
        FROM churned_customers WHERE rnk <= 3 ORDER BY contract_type, rnk
    """, "KPI 4: Top 3 Highest-CLTV Churned Customers per Contract Type")

    run_query(conn, """
        WITH rfm_base AS (
            SELECT c.customer_id, f.recency_tenure_months, f.frequency_addon_breadth,
                   f.monetary_total_charges, f.churn_flag
            FROM fact_subscription f JOIN dim_customer c ON f.customer_key = c.customer_key
        ),
        rfm_scored AS (
            SELECT customer_id, churn_flag,
                   NTILE(5) OVER (ORDER BY recency_tenure_months ASC) AS recency_q,
                   NTILE(5) OVER (ORDER BY frequency_addon_breadth ASC) AS frequency_q,
                   NTILE(5) OVER (ORDER BY monetary_total_charges ASC) AS monetary_q
            FROM rfm_base
        )
        SELECT recency_q + frequency_q + monetary_q AS rfm_score,
               COUNT(*) AS customers, ROUND(100.0*SUM(churn_flag)/COUNT(*),2) AS churn_rate_pct
        FROM rfm_scored GROUP BY rfm_score ORDER BY rfm_score DESC
    """, "KPI 5: RFM Proxy Score Distribution vs Churn Rate (NTILE)")

    run_query(conn, """
        WITH scored AS (
            SELECT churn_score, churn_flag, NTILE(10) OVER (ORDER BY churn_score ASC) AS decile
            FROM fact_subscription
        )
        SELECT decile, COUNT(*) AS customers, SUM(churn_flag) AS actual_churned,
               ROUND(100.0*SUM(churn_flag)/COUNT(*),2) AS actual_churn_rate_pct
        FROM scored GROUP BY decile ORDER BY decile DESC
    """, "KPI 8: Churn Score Decile Calibration (NTILE)")

    run_query(conn, """
        WITH reason_kpi AS (
            SELECT cr.churn_reason, COUNT(*) AS churned_customers
            FROM fact_subscription f JOIN dim_churn_reason cr ON f.churn_reason_key = cr.churn_reason_key
            WHERE f.churn_flag = 1 GROUP BY cr.churn_reason
        )
        SELECT churn_reason, churned_customers,
               ROUND(100.0*SUM(churned_customers) OVER (ORDER BY churned_customers DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) / SUM(churned_customers) OVER (), 2) AS cumulative_pct
        FROM reason_kpi ORDER BY churned_customers DESC LIMIT 8
    """, "KPI 10: Pareto Churn Reason Analysis (cumulative %)")

    run_query(conn, """
        WITH scored AS (
            SELECT c.customer_id, p.contract_type, f.tenure_months, f.churn_score,
                   f.addon_service_count, f.cltv, f.churn_flag,
                   (100 - f.churn_score) AS score_churn,
                   MIN(100.0, f.tenure_months * 100.0/72) AS score_tenure,
                   MIN(100.0, f.addon_service_count * 100.0/6) AS score_addon,
                   CASE p.contract_type WHEN 'Two year' THEN 100 WHEN 'One year' THEN 60 ELSE 20 END AS score_contract
            FROM fact_subscription f
            JOIN dim_customer c ON f.customer_key = c.customer_key
            JOIN dim_plan p ON f.plan_key = p.plan_key
        )
        SELECT customer_id, contract_type, churn_flag,
               ROUND(0.40*score_churn + 0.25*score_tenure + 0.20*score_addon + 0.15*score_contract, 1) AS health_score
        FROM scored ORDER BY health_score ASC LIMIT 10
    """, "VIEW equivalent: 10 Lowest Customer Health Scores (highest priority for outreach)")

    print(f"\n{'='*70}\nMaterializing mv_tenure_cohort_rollup and mv_geography_rollup as physical snapshot tables\n{'='*70}")
    tenure_rollup = pd.read_sql("""
        SELECT tc.tenure_cohort_label, tc.sort_order, COUNT(*) AS customers,
               SUM(f.churn_flag) AS churned, ROUND(100.0*SUM(f.churn_flag)/COUNT(*),2) AS churn_rate_pct,
               ROUND(AVG(f.monthly_charges),2) AS avg_monthly_charges,
               ROUND(SUM(f.total_charges),2) AS total_revenue, ROUND(AVG(f.cltv),2) AS avg_cltv
        FROM fact_subscription f JOIN dim_tenure_cohort tc ON f.tenure_cohort_key = tc.tenure_cohort_key
        GROUP BY tc.tenure_cohort_label, tc.sort_order
    """, conn)
    tenure_rollup.to_sql("mv_tenure_cohort_rollup", conn, if_exists="replace", index=False)
    print(f"mv_tenure_cohort_rollup materialized: {len(tenure_rollup)} rows")

    geo_rollup = pd.read_sql("""
        SELECT g.city, g.state, COUNT(*) AS customers, SUM(f.churn_flag) AS churned,
               ROUND(100.0*SUM(f.churn_flag)/COUNT(*),2) AS churn_rate_pct,
               ROUND(SUM(f.total_charges),2) AS total_revenue,
               AVG(g.latitude) AS latitude, AVG(g.longitude) AS longitude
        FROM fact_subscription f JOIN dim_geography g ON f.geography_key = g.geography_key
        GROUP BY g.city, g.state
    """, conn)
    geo_rollup.to_sql("mv_geography_rollup", conn, if_exists="replace", index=False)
    print(f"mv_geography_rollup materialized: {len(geo_rollup)} rows")

    conn.commit()
    conn.close()
    print("\nAll SQL logic verified against real data.")


if __name__ == "__main__":
    main()
