"""
Plan & Contract Search page.

Explore real plan/service combinations -- contract type, internet
service, payment method, and the 6 real add-on services -- with a
full risk-matrix heatmap and the deliberately-not-smoothed add-on-count
churn chart (same principle as Power BI Page 6: the non-monotonic
1-add-on spike is preserved, not binned away).
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import COLOR_PRIMARY, COLOR_DANGER, COLOR_SUCCESS, COLOR_WARNING
from utils.data_loader import load_customer_data
from utils.logger import get_logger

logger = get_logger(__name__)

ADDON_SERVICES = ["online_security", "online_backup", "device_protection", "tech_support", "streaming_tv", "streaming_movies"]


def _risk_color(pct: float) -> str:
    return COLOR_DANGER if pct >= 35 else COLOR_WARNING if pct >= 20 else COLOR_SUCCESS


def render():
    st.title("📄 Plan & Contract Search")
    st.caption("Explore real plan combinations, service adoption, and where risk concentrates across the product catalog.")

    df = load_customer_data()

    tab1, tab2, tab3 = st.tabs(["Plan Combination Explorer", "Risk Matrix", "Add-on Adoption"])

    # =========================================================
    # TAB 1: Plan combination explorer with filters + drill-down
    # =========================================================
    with tab1:
        st.markdown("##### Filter by Plan Attributes")
        c1, c2, c3 = st.columns(3)
        with c1:
            contracts = st.multiselect("Contract Type", sorted(df["contract_type"].unique()), default=sorted(df["contract_type"].unique()), key="pc_contract")
        with c2:
            internet = st.multiselect("Internet Service", sorted(df["internet_service"].unique()), default=sorted(df["internet_service"].unique()), key="pc_internet")
        with c3:
            payment = st.multiselect("Payment Method", sorted(df["payment_method"].unique()), default=sorted(df["payment_method"].unique()), key="pc_payment")

        st.markdown("##### Filter by Add-on Services (select 'Any' to ignore a service)")
        addon_filters = {}
        addon_cols = st.columns(3)
        for i, svc in enumerate(ADDON_SERVICES):
            with addon_cols[i % 3]:
                addon_filters[svc] = st.selectbox(svc.replace("_", " ").title(), ["Any"] + sorted(df[svc].unique()), key=f"pc_{svc}")

        filtered = df[
            df["contract_type"].isin(contracts)
            & df["internet_service"].isin(internet)
            & df["payment_method"].isin(payment)
        ]
        for svc, val in addon_filters.items():
            if val != "Any":
                filtered = filtered[filtered[svc] == val]

        st.markdown(f"##### {len(filtered):,} of {len(df):,} real customers match this plan configuration")

        if len(filtered) == 0:
            st.warning("No customers match this exact combination. Try loosening a filter.")
        else:
            m1, m2, m3 = st.columns(3)
            m1.metric("Customers", f"{len(filtered):,}")
            m2.metric("Churn Rate", f"{100*filtered['churn_flag'].mean():.2f}%")
            m3.metric("Avg Monthly Charge", f"${filtered['monthly_charges'].mean():.2f}")

            display_cols = ["customer_id", "contract_type", "internet_service", "payment_method", "tenure_months", "monthly_charges", "cltv", "churn_label"]
            st.dataframe(filtered[display_cols], hide_index=True, use_container_width=True, height=320)
            csv = filtered[display_cols].to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download Matching Customers (CSV)", data=csv, file_name="plan_search_results.csv", mime="text/csv")

    # =========================================================
    # TAB 2: Full risk matrix (Internet Service x Contract Type)
    # =========================================================
    with tab2:
        st.markdown("##### Churn Rate Heat Map — Internet Service × Contract Type")
        matrix = df.pivot_table(index="internet_service", columns="contract_type", values="churn_flag", aggfunc="mean").mul(100).round(2)
        # Reorder for a sensible risk-descending read
        matrix = matrix.reindex(index=["Fiber optic", "DSL", "No"], columns=["Month-to-month", "One year", "Two year"])
        fig = px.imshow(
            matrix, text_auto=".1f", color_continuous_scale=["#2CA02C", "#FF7F0E", "#D62728"],
            aspect="auto", labels=dict(color="Churn %"),
        )
        fig.update_layout(height=380, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.error("🔥 **Worst cell:** Fiber optic + Month-to-month customers churn at 54.61% — nearly 70x the best cell (No internet + Two year, 0.78%). These two categorical drivers compound rather than substitute for each other.")

        st.markdown("##### Plan Combinations Table (min. 20 customers)")
        plan_cols = ["contract_type", "internet_service", "payment_method"]
        plan_stats = df.groupby(plan_cols).agg(
            customers=("customer_id", "count"), churn_rate=("churn_flag", "mean"), avg_monthly=("monthly_charges", "mean"),
        ).reset_index()
        plan_stats["churn_rate"] = (plan_stats["churn_rate"] * 100).round(2)
        plan_stats["avg_monthly"] = plan_stats["avg_monthly"].round(2)
        plan_stats = plan_stats[plan_stats["customers"] >= 20].sort_values("churn_rate", ascending=False)
        st.dataframe(
            plan_stats,
            column_config={
                "churn_rate": st.column_config.ProgressColumn("Churn Rate", min_value=0, max_value=100, format="%.1f%%"),
                "avg_monthly": st.column_config.NumberColumn("Avg Monthly", format="$%.2f"),
            },
            hide_index=True, use_container_width=True, height=320,
        )

    # =========================================================
    # TAB 3: Add-on adoption (deliberately not smoothed)
    # =========================================================
    with tab3:
        st.markdown("##### Churn Rate by Number of Add-on Services")
        addon = df.groupby("addon_service_count")["churn_flag"].agg(["mean", "count"]).reset_index()
        addon["mean"] = (addon["mean"] * 100).round(2)
        fig = go.Figure(go.Bar(
            x=addon["addon_service_count"], y=addon["mean"],
            marker_color=[_risk_color(v) for v in addon["mean"]],
            text=addon["mean"].astype(str) + "%", textposition="outside",
        ))
        fig.update_layout(height=320, xaxis_title="Number of Add-on Services", yaxis_title="Churn Rate (%)", margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.warning("⚠️ Notice the spike at exactly 1 add-on (45.76%) — higher than 0 add-ons (21.41%). This is deliberately shown un-smoothed, not binned into ranges, because that specific anomaly is a real, worthwhile product question, not noise to hide.")

        st.markdown("##### Individual Add-on Adoption Rates")
        adoption_rates = []
        for svc in ADDON_SERVICES:
            eligible = df[df[svc] != "No internet service"]
            if len(eligible) > 0:
                rate = round(100 * (eligible[svc] == "Yes").mean(), 2)
                adoption_rates.append({"Service": svc.replace("_", " ").title(), "Adoption Rate (%)": rate})
        adoption_df = pd.DataFrame(adoption_rates).sort_values("Adoption Rate (%)", ascending=True)
        fig2 = px.bar(adoption_df, x="Adoption Rate (%)", y="Service", orientation="h", color_discrete_sequence=[COLOR_PRIMARY])
        fig2.update_layout(height=300, margin=dict(t=10, b=10))
        st.plotly_chart(fig2, use_container_width=True)

    logger.info("Plan & Contract Search page rendered.")
