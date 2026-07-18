"""
Exploratory Data Analysis page.

Reproduces the Phase 3 EDA report's key findings as live, interactive
Plotly charts -- organized into tabs mirroring the report's own section
structure (Overview, Contract & Tenure, Services, Payment & Demographics,
Churn Score & Reasons, Correlations). A sidebar-style filter panel at the
top lets a visitor slice every chart on this page by contract type and
internet service simultaneously, recomputed live (not pre-cached per
filter combination, since slicing a 7,043-row DataFrame is cheap enough
not to need it -- only the initial load is cached).
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import COLOR_PRIMARY, COLOR_DANGER, COLOR_SUCCESS, COLOR_WARNING, COLOR_PURPLE
from utils.data_loader import load_customer_data
from utils.logger import get_logger

logger = get_logger(__name__)

TENURE_COHORT_ORDER = ["0-12 mo", "13-24 mo", "25-36 mo", "37-48 mo", "49-60 mo", "61-72 mo"]


def _risk_color(pct: float) -> str:
    return COLOR_DANGER if pct >= 35 else COLOR_WARNING if pct >= 20 else COLOR_SUCCESS


def _apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    with st.expander("🔎 Filters (apply to every chart on this page)", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            contracts = st.multiselect(
                "Contract Type", options=sorted(df["contract_type"].unique()),
                default=sorted(df["contract_type"].unique()),
            )
        with c2:
            internet = st.multiselect(
                "Internet Service", options=sorted(df["internet_service"].unique()),
                default=sorted(df["internet_service"].unique()),
            )
    filtered = df[df["contract_type"].isin(contracts) & df["internet_service"].isin(internet)]
    if len(filtered) == 0:
        st.warning("No customers match the current filter selection — showing unfiltered data instead.")
        return df
    if len(filtered) < len(df):
        st.caption(f"Showing {len(filtered):,} of {len(df):,} real customers matching your filters.")
    return filtered


def render():
    df_full = load_customer_data()

    st.title("📈 Exploratory Data Analysis")
    st.caption(
    "Interactive visualizations generated from the IBM Telco Customer Churn dataset, with every chart calculated directly from the PostgreSQL database."
)
    

    df = _apply_filters(df_full)

    tabs = st.tabs([
        "Overview", "Contract & Tenure", "Services & Add-ons",
        "Payment & Demographics", "Churn Score & Reasons", "Correlations",
    ])

    # =========================================================
    # TAB 1: Overview
    # =========================================================
    with tabs[0]:
        n = len(df)
        churned = int(df["churn_flag"].sum())
        rate = round(100 * churned / n, 2) if n else 0
        col1, col2, col3 = st.columns(3)
        col1.metric("Customers (filtered)", f"{n:,}")
        col2.metric("Churned", f"{churned:,}")
        col3.metric("Churn Rate", f"{rate:.2f}%")

        st.markdown("##### Revenue Concentration by CLTV")
        sorted_df = df.sort_values("cltv", ascending=False).reset_index(drop=True)
        total_rev = sorted_df["total_charges"].sum()
        shares = []
        for pct in [10, 20, 50]:
            cutoff = int(len(sorted_df) * pct / 100)
            share = round(100 * sorted_df.loc[:cutoff, "total_charges"].sum() / total_rev, 1) if total_rev else 0
            shares.append({"Top %": f"Top {pct}%", "Revenue Share": share})
        shares_df = pd.DataFrame(shares)
        fig = px.bar(shares_df, x="Top %", y="Revenue Share", text="Revenue Share",
                     color_discrete_sequence=[COLOR_PRIMARY])
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(height=280, yaxis_title="% of Total Revenue", margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 **Insight:** Revenue is moderately concentrated — the top 20% of customers by CLTV generate roughly a quarter of total revenue. No single 'whale' dependency risk exists.")

    # =========================================================
    # TAB 2: Contract & Tenure
    # =========================================================
    with tabs[1]:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### Churn Rate by Contract Type")
            cs = df.groupby("contract_type")["churn_flag"].mean().mul(100).round(2).reset_index()
            cs.columns = ["contract_type", "churn_rate_pct"]
            cs = cs.sort_values("churn_rate_pct")
            fig = go.Figure(go.Bar(
                x=cs["churn_rate_pct"], y=cs["contract_type"], orientation="h",
                marker_color=[_risk_color(v) for v in cs["churn_rate_pct"]],
                text=cs["churn_rate_pct"].astype(str) + "%", textposition="outside",
            ))
            fig.update_layout(height=280, xaxis_title="Churn Rate (%)", margin=dict(t=10, b=10, r=40))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("##### Churn Rate by Tenure Cohort")
            tc = df.groupby("tenure_cohort", observed=True)["churn_flag"].mean().mul(100).round(2)
            tc = tc.reindex(TENURE_COHORT_ORDER).reset_index()
            tc.columns = ["tenure_cohort", "churn_rate_pct"]
            fig = px.line(tc, x="tenure_cohort", y="churn_rate_pct", markers=True,
                          color_discrete_sequence=[COLOR_DANGER])
            fig.update_layout(height=280, yaxis_title="Churn Rate (%)", xaxis_title=None, margin=dict(t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)

        st.success("✅ **Insight:** Contract type is the single strongest churn driver found across the entire project (Cramér's V = 0.41) — month-to-month customers churn at up to 15x the rate of two-year customers. Tenure shows the same pattern: the first 12 months carry by far the highest risk.")

    # =========================================================
    # TAB 3: Services & Add-ons
    # =========================================================
    with tabs[2]:
        st.markdown("##### Churn Rate by Number of Add-on Services")
        addon = df.groupby("addon_service_count")["churn_flag"].agg(["mean", "count"]).reset_index()
        addon["mean"] = (addon["mean"] * 100).round(2)
        fig = go.Figure(go.Bar(
            x=addon["addon_service_count"], y=addon["mean"],
            marker_color=[_risk_color(v) for v in addon["mean"]],
            text=addon["mean"].astype(str) + "%", textposition="outside",
        ))
        fig.update_layout(height=300, xaxis_title="Number of Add-on Services", yaxis_title="Churn Rate (%)",
                          margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.warning("⚠️ **Insight (deliberately not smoothed):** Customers with exactly 1 add-on churn at the *highest* rate of any tier (45.76%) — even higher than customers with zero add-ons. This non-monotonic pattern is real and worth product investigation, not something to hide by grouping add-on counts into broader bins.")

        st.markdown("##### Average Monthly Charges by Add-on Count")
        addon_rev = df.groupby("addon_service_count")["monthly_charges"].mean().round(2).reset_index()
        fig2 = px.line(addon_rev, x="addon_service_count", y="monthly_charges", markers=True,
                       color_discrete_sequence=[COLOR_SUCCESS])
        fig2.update_layout(height=260, xaxis_title="Number of Add-on Services", yaxis_title="Avg Monthly Charges ($)",
                           margin=dict(t=10, b=10))
        st.plotly_chart(fig2, use_container_width=True)

    # =========================================================
    # TAB 4: Payment & Demographics
    # =========================================================
    with tabs[3]:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### Churn Rate by Payment Method")
            pm = df.groupby("payment_method")["churn_flag"].mean().mul(100).round(2).sort_values(ascending=True).reset_index()
            pm.columns = ["payment_method", "churn_rate_pct"]
            fig = go.Figure(go.Bar(
                x=pm["churn_rate_pct"], y=pm["payment_method"], orientation="h",
                marker_color=[_risk_color(v) for v in pm["churn_rate_pct"]],
                text=pm["churn_rate_pct"].astype(str) + "%", textposition="outside",
            ))
            fig.update_layout(height=280, xaxis_title="Churn Rate (%)", margin=dict(t=10, b=10, r=40))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("##### Churn Rate by Demographic Factor")
            demo_rows = []
            for col, label in [("gender", "Gender"), ("senior_citizen", "Senior Citizen"),
                                ("has_partner", "Has Partner"), ("has_dependents", "Has Dependents")]:
                for val, rate in df.groupby(col)["churn_flag"].mean().mul(100).round(2).items():
                    demo_rows.append({"Factor": f"{label}: {val}", "Churn Rate": rate})
            demo_df = pd.DataFrame(demo_rows).sort_values("Churn Rate")
            fig = go.Figure(go.Bar(
                x=demo_df["Churn Rate"], y=demo_df["Factor"], orientation="h",
                marker_color=[_risk_color(v) for v in demo_df["Churn Rate"]],
            ))
            fig.update_layout(height=280, xaxis_title="Churn Rate (%)", margin=dict(t=10, b=10, r=40))
            st.plotly_chart(fig, use_container_width=True)

        st.error("🚫 **Non-finding worth knowing:** Gender shows almost no difference in churn (26.9% vs 26.2%) — statistically confirmed as not significant in the Phase 6 hypothesis testing (p=0.487). Having dependents, by contrast, shows the largest demographic gap found (32.6% vs 6.5%).")

    # =========================================================
    # TAB 5: Churn Score & Reasons
    # =========================================================
    with tabs[4]:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("##### Churn Score Decile Calibration")
            if df["churn_score"].nunique() > 10:
                df_dec = df.copy()
                df_dec["decile"] = pd.qcut(df_dec["churn_score"], 10, labels=False, duplicates="drop") + 1
                dec = df_dec.groupby("decile")["churn_flag"].mean().mul(100).round(2).reset_index()
                fig = px.line(dec, x="decile", y="churn_flag", markers=True, color_discrete_sequence=[COLOR_DANGER])
                fig.update_layout(height=300, xaxis_title="Churn Score Decile (10=highest risk)",
                                  yaxis_title="Actual Churn Rate (%)", margin=dict(t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)
                st.caption("IBM's vendor-provided risk score, validated against real outcomes.")
            else:
                st.info("Not enough score variation in the current filter selection to compute deciles.")

        with col2:
            st.markdown("##### Top Documented Churn Reasons")
            churned_df = df[df["churn_flag"] == 1]
            if len(churned_df) > 0:
                reasons = (
                    churned_df["churn_reason"].value_counts().head(8).reset_index()
                )
                reasons.columns = ["churn_reason", "count"]
                fig = px.bar(reasons, x="count", y="churn_reason", orientation="h",
                            color_discrete_sequence=[COLOR_PURPLE])
                fig.update_layout(height=300, xaxis_title="Churned Customers", yaxis_title=None,
                                  yaxis=dict(autorange="reversed"), margin=dict(t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No churned customers in the current filter selection.")

        st.success("✅ **Insight:** IBM's Churn Score is already well-calibrated — the highest-risk decile shows dramatically higher real churn than the lowest. Root-cause analysis shows competitor pressure (33% of churn) and service/support experience (24%) dominate documented reasons — the latter being the most directly controllable.")

    # =========================================================
    # TAB 6: Correlations
    # =========================================================
    with tabs[5]:
        st.markdown("##### Correlation Matrix (Key Numeric Fields)")
        corr_cols = ["tenure_months", "monthly_charges", "total_charges", "churn_score", "cltv", "addon_service_count", "churn_flag"]
        corr = df[corr_cols].corr().round(2)
        fig = px.imshow(
            corr, text_auto=True, color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
            aspect="auto",
        )
        fig.update_layout(height=450, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 **Insight:** `churn_score` correlates most strongly with actual churn (as expected — it's a vendor-derived risk field). `tenure_months` shows the strongest *negative* correlation among the genuinely independent business fields, consistent with every other finding on this page.")

    logger.info(f"EDA page rendered with {len(df)} filtered rows (of {len(df_full)} total).")
