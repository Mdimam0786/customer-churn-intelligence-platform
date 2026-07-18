"""
Home page — Executive Overview.

Mirrors Power BI Page 1 (Executive Overview) conceptually, but built
natively for the web: gradient KPI cards, an interactive Plotly donut,
a churn-by-contract bar chart, and a cumulative revenue area chart --
all computed live from the real, cached dataset via utils/data_loader.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import COLOR_PRIMARY, COLOR_DANGER, COLOR_SUCCESS, COLOR_WARNING
from utils.data_loader import load_customer_data, get_headline_kpis
from utils.theme import kpi_card, status_badge
from utils.logger import get_logger

logger = get_logger(__name__)

TENURE_COHORT_ORDER = ["0-12 mo", "13-24 mo", "25-36 mo", "37-48 mo", "49-60 mo", "61-72 mo"]


def _churn_rate_badge(rate_pct: float) -> tuple:
    if rate_pct >= 35:
        return "badge-red", "High Risk"
    elif rate_pct >= 20:
        return "badge-amber", "Moderate Risk"
    return "badge-green", "Healthy"


def render():
    df = load_customer_data()
    kpis = get_headline_kpis(df)

    # ---------------------------------------------------------------
    # Header
    # ---------------------------------------------------------------
    col_title, col_badge = st.columns([5, 1])
    with col_title:
        st.title("Executive Overview")
        st.caption(
    "Real-time dashboard built from 7,043 IBM Telco Customer Churn records, with live KPIs calculated directly from the PostgreSQL database."
)
       
    with col_badge:
        badge_class, badge_text = _churn_rate_badge(kpis["churn_rate_pct"])
        st.markdown(
            f'<div style="text-align:right; padding-top: 1.5rem;">{status_badge(badge_text, badge_class.replace("badge-", ""))}</div>',
            unsafe_allow_html=True,
        )

    st.write("")

    # ---------------------------------------------------------------
    # KPI Cards (gradient-accented, hover animation via theme.py)
    # ---------------------------------------------------------------
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi_card("Total Customers", f"{kpis['total_customers']:,}", accent=COLOR_PRIMARY)
    with c2:
        kpi_card(
            "Churn Rate", f"{kpis['churn_rate_pct']:.2f}%",
            delta="95% CI: 25.52–27.58%", delta_type="neutral",
            accent=COLOR_DANGER,
        )
    with c3:
        kpi_card("Total Billed Revenue", f"${kpis['total_revenue']:,.0f}", accent=COLOR_SUCCESS)
    with c4:
        kpi_card("Current MRR", f"${kpis['current_mrr']:,.0f}", accent=COLOR_PRIMARY)
    with c5:
        kpi_card(
            "MRR At Risk", f"${kpis['mrr_at_risk']:,.0f}",
            delta="from already-churned customers", delta_type="negative",
            accent=COLOR_DANGER,
        )

    st.write("")
    st.write("")

    # ---------------------------------------------------------------
    # Row 2: Donut + Contract-type bar chart
    # ---------------------------------------------------------------
    col_donut, col_bar = st.columns(2)

    with col_donut:
        with st.container(border=True):
            st.subheader("Customer Base Split")
            status_counts = (
                df["churn_flag"].map({1: "Churned", 0: "Retained"}).value_counts().reset_index()
            )
            status_counts.columns = ["status", "count"]
            fig = px.pie(
                status_counts, names="status", values="count", hole=0.55,
                color="status",
                color_discrete_map={"Churned": COLOR_DANGER, "Retained": COLOR_SUCCESS},
            )
            fig.update_traces(textinfo="percent+label", textfont_size=13)
            fig.update_layout(
                showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=320,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_bar:
        with st.container(border=True):
            st.subheader("Churn Rate by Contract Type")
            contract_stats = (
                df.groupby("contract_type")["churn_flag"]
                .mean().mul(100).round(2).reset_index()
                .rename(columns={"churn_flag": "churn_rate_pct"})
                .sort_values("churn_rate_pct", ascending=True)
            )
            colors = [
                COLOR_DANGER if v >= 35 else COLOR_WARNING if v >= 20 else COLOR_SUCCESS
                for v in contract_stats["churn_rate_pct"]
            ]
            fig = go.Figure(go.Bar(
                x=contract_stats["churn_rate_pct"], y=contract_stats["contract_type"],
                orientation="h", marker_color=colors,
                text=contract_stats["churn_rate_pct"].astype(str) + "%",
                textposition="outside",
            ))
            fig.update_layout(
                margin=dict(t=10, b=10, l=10, r=30), height=320,
                xaxis_title="Churn Rate (%)", yaxis_title=None,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)

    st.write("")

    # ---------------------------------------------------------------
    # Row 3: Cumulative revenue by tenure cohort (area chart)
    # ---------------------------------------------------------------
    with st.container(border=True):
        st.subheader("Cumulative Revenue by Tenure Cohort")
        cohort_rev = (
            df.groupby("tenure_cohort", observed=True)["total_charges"]
            .sum().reindex(TENURE_COHORT_ORDER).cumsum().reset_index()
        )
        cohort_rev.columns = ["tenure_cohort", "cumulative_revenue"]
        fig = px.area(
            cohort_rev, x="tenure_cohort", y="cumulative_revenue",
            color_discrete_sequence=[COLOR_PRIMARY],
        )
        fig.update_traces(line_width=2.5)
        fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=10), height=300,
            xaxis_title=None, yaxis_title="Cumulative Revenue ($)",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------------------
    # Row 4: Priority outreach table (lowest health score customers)
    # ---------------------------------------------------------------
    with st.container(border=True):
        st.subheader("🚨 Top 10 Priority Outreach — Lowest Health Score")

        df_health = df.copy()
        df_health["score_churn"] = 100 - df_health["churn_score"]
        df_health["score_tenure"] = (df_health["tenure_months"] * 100 / 72).clip(upper=100)
        df_health["score_addon"] = (df_health["addon_service_count"] * 100 / 6).clip(upper=100)
        contract_score_map = {"Two year": 100, "One year": 60, "Month-to-month": 20}
        df_health["score_contract"] = df_health["contract_type"].map(contract_score_map)
        df_health["health_score"] = (
            0.40 * df_health["score_churn"] + 0.25 * df_health["score_tenure"]
            + 0.20 * df_health["score_addon"] + 0.15 * df_health["score_contract"]
        ).round(1)

        priority = df_health.nsmallest(10, "health_score")[
            ["customer_id", "contract_type", "tenure_months", "cltv", "health_score"]
        ]
        st.dataframe(
            priority,
            column_config={
                "customer_id": "Customer ID",
                "contract_type": "Contract",
                "tenure_months": st.column_config.NumberColumn("Tenure (mo)"),
                "cltv": st.column_config.NumberColumn("CLTV", format="$%d"),
                "health_score": st.column_config.ProgressColumn(
                    "Health Score", min_value=0, max_value=100, format="%.1f"
                ),
            },
            hide_index=True,
            use_container_width=True,
        )

        csv = priority.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Priority List (CSV)", data=csv,
            file_name="priority_outreach_list.csv", mime="text/csv",
        )

    logger.info("Home page rendered successfully.")
