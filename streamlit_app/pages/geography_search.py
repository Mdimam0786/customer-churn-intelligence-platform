"""
Geography Search page.

Search and explore real California cities. Uses Plotly's built-in
mapbox scatter (a hard dependency already in requirements.txt) as the
interactive map.

Carries forward the SAME minimum-30-customer guardrail filter used in
the Phase 4 SQL layer and the Power BI Geographic Dashboard build guide
-- small towns with 5-10 customers show wildly noisy churn rates that
aren't statistically meaningful, and this page defaults to excluding
them from the map/table exactly as those two other layers do.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from config import COLOR_SUCCESS, COLOR_DANGER
from utils.data_loader import load_customer_data
from utils.logger import get_logger

logger = get_logger(__name__)


@st.cache_data(show_spinner=False)
def build_city_stats(df: pd.DataFrame) -> pd.DataFrame:
    stats = df.groupby("city").agg(
        customers=("customer_id", "count"),
        churned=("churn_flag", "sum"),
        total_revenue=("total_charges", "sum"),
        avg_cltv=("cltv", "mean"),
        latitude=("latitude", "mean"),
        longitude=("longitude", "mean"),
    ).reset_index()
    stats["churn_rate_pct"] = (stats["churned"] / stats["customers"] * 100).round(2)
    stats["total_revenue"] = stats["total_revenue"].round(2)
    stats["avg_cltv"] = stats["avg_cltv"].round(2)
    return stats


def render():
    st.title("🗺️ Geography Search")
    st.warning(
        "📍 **Scope note:** 100% of customers in this dataset are located in California "
        "(1,129 real cities). This is **not** a national dataset — every finding below is a within-California observation."
    )

    df = load_customer_data()
    city_stats = build_city_stats(df)

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_city = st.text_input("Search by city name", placeholder="e.g. San Diego")
    with col2:
        min_customers = st.number_input("Minimum customers (reliability guardrail)", min_value=1, max_value=100, value=30, step=1)
    with col3:
        churn_range = st.slider("Churn rate range (%)", 0.0, 100.0, (0.0, 100.0))

    filtered = city_stats[city_stats["customers"] >= min_customers]
    filtered = filtered[filtered["churn_rate_pct"].between(*churn_range)]
    if search_city:
        filtered = filtered[filtered["city"].str.contains(search_city, case=False, na=False)]

    if min_customers < 30:
        st.info("ℹ️ You've lowered the reliability guardrail below 30 customers — smaller cities can show noisy, statistically unreliable churn rates (see Phase 3 Insight 91). Interpret results below with extra caution.")

    st.markdown(f"##### {len(filtered):,} cities match your search (of {len(city_stats):,} real cities total, {len(city_stats[city_stats['customers']>=30]):,} with ≥30 customers)")

    if len(filtered) == 0:
        st.warning("No cities match your criteria. Try widening your filters.")
        return

    # ---------------------------------------------------------------
    # Interactive map
    # ---------------------------------------------------------------
    st.markdown("##### Interactive Map — bubble size = customers, color = churn rate")
    fig = px.scatter_mapbox(
        filtered, lat="latitude", lon="longitude", size="customers", color="churn_rate_pct",
        color_continuous_scale=[COLOR_SUCCESS, "#FF7F0E", COLOR_DANGER],
        hover_name="city",
        hover_data={"customers": True, "churn_rate_pct": ":.2f", "total_revenue": ":$,.0f", "latitude": False, "longitude": False},
        size_max=35, zoom=5, height=480,
    )
    fig.update_layout(
        mapbox_style="carto-positron",
        margin=dict(t=10, b=10, l=10, r=10),
        coloraxis_colorbar_title="Churn %",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------------------
    # Results table
    # ---------------------------------------------------------------
    st.markdown("##### City Details")
    display = filtered[["city", "customers", "churn_rate_pct", "total_revenue", "avg_cltv"]].sort_values(
        "total_revenue", ascending=False
    )
    st.dataframe(
        display,
        column_config={
            "city": "City", "customers": "Customers",
            "churn_rate_pct": st.column_config.ProgressColumn("Churn Rate", min_value=0, max_value=100, format="%.1f%%"),
            "total_revenue": st.column_config.NumberColumn("Total Revenue", format="$%.0f"),
            "avg_cltv": st.column_config.NumberColumn("Avg CLTV", format="$%.0f"),
        },
        hide_index=True, use_container_width=True, height=380,
    )

    csv = display.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download City Results (CSV)", data=csv, file_name="city_search_results.csv", mime="text/csv")

    logger.info(f"Geography Search rendered with {len(filtered)} cities (guardrail={min_customers}).")
