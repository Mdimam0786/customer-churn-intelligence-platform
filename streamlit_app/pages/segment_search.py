"""
Segment Search page.

Two real, independently-computed segmentation views:
1. K-Means (business k=5, same feature set and random_state as Phase 7)
   -- recomputed live here via sklearn, cached, so this is a genuine
   reproduction of the Phase 7 model, not a hardcoded lookup table.
2. RFM proxy segmentation (quintile-based, same logic as the Phase 4
   SQL / Power BI DAX version) -- also computed live.

A visitor can pick either segmentation, see its real profile table and
chart, then drill into the actual customers within any one segment.
"""

import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from config import COLOR_PRIMARY, COLOR_DANGER, COLOR_SUCCESS, COLOR_WARNING, COLOR_PURPLE
from utils.data_loader import load_customer_data
from utils.logger import get_logger

logger = get_logger(__name__)

CLUSTER_FEATURES = ["tenure_months", "monthly_charges", "total_charges", "addon_service_count", "cltv"]

RFM_SEGMENT_COLORS = {
    "Champion": COLOR_SUCCESS, "Loyal": "#1BAF7A", "Steady": COLOR_WARNING,
    "At Risk": "#E07B00", "Critical / New": COLOR_DANGER,
}


@st.cache_data(show_spinner="Running live K-Means clustering (k=5)...")
def compute_kmeans_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Reproduces the real Phase 7 business-actionable (k=5) segmentation live."""
    X = df[CLUSTER_FEATURES]
    X_scaled = StandardScaler().fit_transform(X)
    km = KMeans(n_clusters=5, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)
    result = df.copy()
    result["segment"] = [f"Segment {l}" for l in labels]
    return result


@st.cache_data(show_spinner=False)
def compute_rfm_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Reproduces the real RFM proxy quintile segmentation (Phase 4/5/7 logic) live."""
    result = df.copy()
    result["recency_q"] = pd.qcut(result["recency_tenure_months"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    result["frequency_q"] = pd.qcut(result["frequency_addon_breadth"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    result["monetary_q"] = pd.qcut(result["monetary_total_charges"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    result["rfm_score"] = result["recency_q"] + result["frequency_q"] + result["monetary_q"]

    def label_segment(s):
        if s >= 13:
            return "Champion"
        if s >= 10:
            return "Loyal"
        if s >= 7:
            return "Steady"
        if s >= 4:
            return "At Risk"
        return "Critical / New"

    result["segment"] = result["rfm_score"].apply(label_segment)
    return result


def _segment_browser(segmented_df: pd.DataFrame, segment_col: str = "segment"):
    profile = (
        segmented_df.groupby(segment_col)
        .agg(
            customers=("customer_id", "count"),
            avg_tenure=("tenure_months", "mean"),
            avg_cltv=("cltv", "mean"),
            churn_rate=("churn_flag", "mean"),
        )
        .round(2)
    )
    profile["churn_rate"] = (profile["churn_rate"] * 100).round(2)
    profile = profile.reset_index().sort_values("churn_rate", ascending=False)

    col_chart, col_table = st.columns([3, 2])
    with col_chart:
        fig = px.bar(
            profile, x=segment_col, y="churn_rate", text="churn_rate",
            color="churn_rate", color_continuous_scale=["#2CA02C", "#FF7F0E", "#D62728"],
        )
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(height=340, yaxis_title="Churn Rate (%)", margin=dict(t=10, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    with col_table:
        st.dataframe(
            profile.rename(columns={
                segment_col: "Segment", "customers": "Customers", "avg_tenure": "Avg Tenure",
                "avg_cltv": "Avg CLTV", "churn_rate": "Churn %",
            }),
            hide_index=True, use_container_width=True, height=340,
        )

    st.markdown("##### Browse Customers Within a Segment")
    chosen_segment = st.selectbox("Select a segment to view its real customers:", profile[segment_col].tolist())
    segment_customers = segmented_df[segmented_df[segment_col] == chosen_segment][
        ["customer_id", "contract_type", "tenure_months", "monthly_charges", "cltv", "churn_score", "churn_label"]
    ]
    st.dataframe(segment_customers, hide_index=True, use_container_width=True, height=300)
    csv = segment_customers.to_csv(index=False).encode("utf-8")
    st.download_button(f"⬇️ Download '{chosen_segment}' Customers (CSV)", data=csv, file_name=f"segment_{chosen_segment}.csv".replace(" ", "_"), mime="text/csv")


def render():
    st.title("👥 Segment Search")
    st.caption("Two real, independently-computed segmentations — recomputed live from your data, not hardcoded lookup tables.")

    df = load_customer_data()
    tab1, tab2 = st.tabs(["K-Means Behavioral Segments", "RFM Proxy Segments"])

    with tab1:
        st.info("ℹ️ K-Means clustering (k=5, business-actionable choice — see Phase 7 report for why k=2 was statistically optimal but too coarse) on tenure, billing, add-ons, and CLTV.")
        kmeans_df = compute_kmeans_segments(df)
        _segment_browser(kmeans_df, "segment")

    with tab2:
        st.info("ℹ️ RFM proxy segmentation — Recency (tenure), Frequency (add-on breadth), Monetary (total billed) — since this dataset has no transaction log for true RFM.")
        rfm_df = compute_rfm_segments(df)
        _segment_browser(rfm_df, "segment")

    logger.info("Segment Search page rendered.")
