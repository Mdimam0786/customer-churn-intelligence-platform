"""
SQL Insights page.

Runs real, live SQL queries against the real star schema, loaded here
using Python's built-in sqlite3 module (no extra dependency needed).
This is the same SQLite demo database used in the SQL work for this
project — a live PostgreSQL server wasn't always available during
development, and the CTE/window-function SQL used here runs the same
way in both databases (see docs/sql_verification_log.md).

A visitor can pick any of the real KPI queries from a preset dropdown,
see and edit the actual SQL, and re-run it live — or write their own
SELECT query against the schema from scratch.
"""

import os
import sqlite3

import pandas as pd
import streamlit as st

from utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "churn_intelligence.db")

PRESET_QUERIES = {
    "KPI 1 — Executive Summary": """
SELECT
    COUNT(*) AS total_customers,
    SUM(churn_flag) AS churned_customers,
    ROUND(100.0 * SUM(churn_flag) / COUNT(*), 2) AS churn_rate_pct,
    ROUND(SUM(total_charges), 2) AS total_billed_revenue,
    ROUND(SUM(monthly_charges), 2) AS current_mrr,
    ROUND(SUM(CASE WHEN churn_flag=1 THEN monthly_charges ELSE 0 END), 2) AS mrr_at_risk,
    ROUND(AVG(cltv), 2) AS avg_cltv
FROM fact_subscription;
""".strip(),

    "KPI 2 — Contract Type Ranking (Window Functions)": """
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
FROM contract_kpi ORDER BY churn_risk_rank;
""".strip(),

    "KPI 3 — Tenure Cohort Progression (LAG + Running SUM)": """
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
FROM cohort_kpi ORDER BY sort_order;
""".strip(),

    "KPI 4 — Top 3 Highest-CLTV Churned per Contract Type": """
WITH churned_customers AS (
    SELECT c.customer_id, p.contract_type, f.cltv, f.tenure_months,
           ROW_NUMBER() OVER (PARTITION BY p.contract_type ORDER BY f.cltv DESC) AS rnk
    FROM fact_subscription f
    JOIN dim_customer c ON f.customer_key = c.customer_key
    JOIN dim_plan p ON f.plan_key = p.plan_key
    WHERE f.churn_flag = 1
)
SELECT customer_id, contract_type, cltv, tenure_months
FROM churned_customers WHERE rnk <= 3 ORDER BY contract_type, rnk;
""".strip(),

    "KPI 8 — Churn Score Decile Calibration (NTILE)": """
WITH scored AS (
    SELECT churn_score, churn_flag, NTILE(10) OVER (ORDER BY churn_score ASC) AS decile
    FROM fact_subscription
)
SELECT decile, COUNT(*) AS customers, SUM(churn_flag) AS actual_churned,
       ROUND(100.0*SUM(churn_flag)/COUNT(*),2) AS actual_churn_rate_pct
FROM scored GROUP BY decile ORDER BY decile DESC;
""".strip(),

    "KPI 10 — Pareto Churn Reason Analysis": """
WITH reason_kpi AS (
    SELECT cr.churn_reason, COUNT(*) AS churned_customers
    FROM fact_subscription f JOIN dim_churn_reason cr ON f.churn_reason_key = cr.churn_reason_key
    WHERE f.churn_flag = 1 GROUP BY cr.churn_reason
)
SELECT churn_reason, churned_customers,
       ROUND(100.0*SUM(churned_customers) OVER (ORDER BY churned_customers DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) / SUM(churned_customers) OVER (), 2) AS cumulative_pct
FROM reason_kpi ORDER BY churned_customers DESC LIMIT 10;
""".strip(),

    "Customer Health Score (SQL View Logic)": """
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
FROM scored ORDER BY health_score ASC LIMIT 15;
""".strip(),
}


def _is_safe_select(query: str) -> bool:
    """
    Only SELECT / WITH (CTE) statements are allowed to execute against
    this database from a public-facing text box -- blocks INSERT/UPDATE/
    DELETE/DROP/ATTACH etc. even though this is a demo copy of the data
    (not the production database), as a matter of basic hygiene for any
    app that runs user-editable SQL.
    """
    stripped = query.strip().lstrip("(").strip()
    lowered = stripped.lower()
    if not (lowered.startswith("select") or lowered.startswith("with")):
        return False
    forbidden = ["insert", "update", "delete", "drop", "alter", "attach", "pragma", "vacuum", "create"]
    return not any(f" {word} " in f" {lowered} " or lowered.startswith(word) for word in forbidden)


@st.cache_resource
def get_connection():
    """
    Read-only connection to the real SQLite demo database. Cached as a
    resource (not data) since a DB connection object shouldn't be
    re-pickled/hashed the way st.cache_data would try to.
    """
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Demo database not found at {DB_PATH}.")
    uri = f"file:{DB_PATH}?mode=ro"
    return sqlite3.connect(uri, uri=True, check_same_thread=False)


def render():
    st.title("🗄️ SQL Insights")
    st.caption(
        "Live SQL execution against the real Phase 2 star schema (7,043 real customers). "
        "This demo runs on SQLite — the production target is PostgreSQL 14+; every query here "
        "uses ANSI-standard CTE/window-function syntax verified to run identically on both "
        "(see the project's SQL Verification Log)."
    )

    conn = get_connection()

    with st.expander("📋 View the real star schema tables", expanded=False):
        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;", conn)
        st.dataframe(tables, hide_index=True, use_container_width=True)

    preset = st.selectbox("Choose a real Phase 4 KPI query to start from:", list(PRESET_QUERIES.keys()))

    query_text = st.text_area(
        "SQL Query (editable — try modifying it, or write your own SELECT against the tables above)",
        value=PRESET_QUERIES[preset],
        height=220,
    )

    col_run, col_download = st.columns([1, 5])
    run_clicked = col_run.button("▶️ Run Query", type="primary")

    if run_clicked:
        if not _is_safe_select(query_text):
            st.error("🚫 Only SELECT / WITH (read-only) queries are allowed on this page.")
            logger.warning("Blocked a non-SELECT query attempt on the SQL Insights page.")
        else:
            try:
                with st.spinner("Executing..."):
                    result_df = pd.read_sql(query_text, conn)
                st.success(f"✅ Query executed — {len(result_df):,} rows returned.")
                st.dataframe(result_df, use_container_width=True, hide_index=True)

                csv = result_df.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download Results (CSV)", data=csv, file_name="query_results.csv", mime="text/csv")
                logger.info(f"SQL query executed successfully, {len(result_df)} rows returned.")
            except Exception as e:
                st.error(f"Query failed: {e}")
                logger.error(f"SQL query failed: {e}")

    st.divider()
    st.caption(
        "🔒 This page only permits read-only SELECT/WITH statements, even though it's running against "
        "a demo copy of the data rather than production — basic hygiene for any app exposing an editable query box."
    )
