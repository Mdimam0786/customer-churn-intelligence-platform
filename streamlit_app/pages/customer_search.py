"""
Customer Search page.

Search and filter across all 7,043 real customers by ID, contract,
service, payment method, tenure, and monthly charge range. Uses
AgGrid for an enterprise-grid feel (sortable, resizable columns,
built-in pagination) when the streamlit-aggrid package is installed,
with a graceful fallback to st.dataframe + manual pagination controls
otherwise -- same fallback pattern used for the sidebar nav in app.py,
so the app never hard-crashes over an optional dependency.
"""

import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import COLOR_PRIMARY, COLOR_DANGER, COLOR_SUCCESS
from utils.data_loader import load_customer_data
from utils.logger import get_logger

logger = get_logger(__name__)

DISPLAY_COLUMNS = [
    "customer_id", "contract_type", "internet_service", "payment_method",
    "tenure_months", "monthly_charges", "total_charges", "cltv",
    "churn_score", "churn_label",
]

PAGE_SIZE = 15


def _apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.markdown("##### Search & Filter")
    c1, c2 = st.columns([2, 1])
    with c1:
        search_term = st.text_input("Search by Customer ID (partial match allowed)", placeholder="e.g. 3668 or QPYBK")
    with c2:
        churn_filter = st.selectbox("Churn Status", ["All", "Churned Only", "Retained Only"])

    c3, c4, c5 = st.columns(3)
    with c3:
        contracts = st.multiselect("Contract Type", sorted(df["contract_type"].unique()), default=sorted(df["contract_type"].unique()))
    with c4:
        internet = st.multiselect("Internet Service", sorted(df["internet_service"].unique()), default=sorted(df["internet_service"].unique()))
    with c5:
        payment = st.multiselect("Payment Method", sorted(df["payment_method"].unique()), default=sorted(df["payment_method"].unique()))

    c6, c7 = st.columns(2)
    with c6:
        tenure_range = st.slider("Tenure (months)", 0, 72, (0, 72))
    with c7:
        charge_min, charge_max = float(df["monthly_charges"].min()), float(df["monthly_charges"].max())
        charge_range = st.slider("Monthly Charges ($)", charge_min, charge_max, (charge_min, charge_max))

    filtered = df.copy()
    if search_term:
        filtered = filtered[filtered["customer_id"].str.contains(search_term, case=False, na=False)]
    if churn_filter == "Churned Only":
        filtered = filtered[filtered["churn_flag"] == 1]
    elif churn_filter == "Retained Only":
        filtered = filtered[filtered["churn_flag"] == 0]
    filtered = filtered[
        filtered["contract_type"].isin(contracts)
        & filtered["internet_service"].isin(internet)
        & filtered["payment_method"].isin(payment)
        & filtered["tenure_months"].between(*tenure_range)
        & filtered["monthly_charges"].between(*charge_range)
    ]
    return filtered


def _render_grid(display_df: pd.DataFrame) -> str:
    """Renders the results grid, returning the selected customer_id (or None)."""
    try:
        from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

        gb = GridOptionsBuilder.from_dataframe(display_df)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=PAGE_SIZE)
        gb.configure_selection(selection_mode="single", use_checkbox=False)
        gb.configure_default_column(resizable=True, sortable=True, filter=True)
        grid_options = gb.build()

        grid_response = AgGrid(
            display_df, gridOptions=grid_options, update_mode=GridUpdateMode.SELECTION_CHANGED,
            height=420, fit_columns_on_grid_load=True, theme="alpine",
        )
        selected = grid_response.get("selected_rows")
        if selected is not None and len(selected) > 0:
            row = selected.iloc[0] if hasattr(selected, "iloc") else selected[0]
            return row["customer_id"] if hasattr(row, "__getitem__") else None
        return None

    except ImportError:
        logger.warning("streamlit-aggrid not installed; falling back to st.dataframe + manual pagination.")
        total_pages = max(1, math.ceil(len(display_df) / PAGE_SIZE))
        page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
        start = (page - 1) * PAGE_SIZE
        st.dataframe(display_df.iloc[start:start + PAGE_SIZE], use_container_width=True, hide_index=True)
        st.caption(f"Page {page} of {total_pages}")
        selected_id = st.selectbox(
            "Select a Customer ID to view full profile:",
            ["—"] + display_df["customer_id"].tolist(),
        )
        return selected_id if selected_id != "—" else None


def _render_customer_detail(df_full: pd.DataFrame, customer_id: str):
    row = df_full[df_full["customer_id"] == customer_id]
    if row.empty:
        st.warning("Customer not found in the current dataset.")
        return
    c = row.iloc[0]

    st.markdown("---")
    st.markdown(f"### 👤 Customer Profile: `{customer_id}`")

    status_color = COLOR_DANGER if c["churn_flag"] == 1 else COLOR_SUCCESS
    status_text = "Churned" if c["churn_flag"] == 1 else "Active"
    st.markdown(
        f'<span style="background:{status_color}22; color:{status_color}; padding:0.3rem 0.8rem; '
        f'border-radius:999px; font-weight:600; font-size:0.85rem;">{status_text}</span>',
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tenure", f"{int(c['tenure_months'])} months")
    col2.metric("Monthly Charges", f"${c['monthly_charges']:.2f}")
    col3.metric("CLTV", f"{int(c['cltv']):,}")
    col4.metric("Churn Score", f"{int(c['churn_score'])}/100")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Account Details**")
        st.write(f"- Contract: {c['contract_type']}")
        st.write(f"- Internet Service: {c['internet_service']}")
        st.write(f"- Payment Method: {c['payment_method']}")
        st.write(f"- Paperless Billing: {c['paperless_billing']}")
        st.write(f"- City: {c['city']}, {c['state']}")
    with col_b:
        st.markdown("**Services Subscribed**")
        for svc, label in [
            ("phone_service", "Phone Service"), ("multiple_lines", "Multiple Lines"),
            ("online_security", "Online Security"), ("online_backup", "Online Backup"),
            ("device_protection", "Device Protection"), ("tech_support", "Tech Support"),
            ("streaming_tv", "Streaming TV"), ("streaming_movies", "Streaming Movies"),
        ]:
            val = c[svc]
            icon = "✅" if val == "Yes" else "➖" if "internet service" in str(val) or "phone service" in str(val) else "❌"
            st.write(f"{icon} {label}: {val}")

    if c["churn_flag"] == 1:
        st.error(f"**Churn Reason:** {c['churn_reason']}")

    # Small radar-style comparison: this customer vs. dataset average
    st.markdown("**This Customer vs. Company Average**")
    df_avg = df_full[["tenure_months", "monthly_charges", "cltv", "addon_service_count"]].mean()
    categories = ["Tenure (mo)", "Monthly Charges", "CLTV (÷100)", "Add-on Count"]
    customer_vals = [c["tenure_months"], c["monthly_charges"], c["cltv"] / 100, c["addon_service_count"]]
    avg_vals = [df_avg["tenure_months"], df_avg["monthly_charges"], df_avg["cltv"] / 100, df_avg["addon_service_count"]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=customer_vals, theta=categories, fill="toself", name=customer_id, line_color=COLOR_PRIMARY))
    fig.add_trace(go.Scatterpolar(r=avg_vals, theta=categories, fill="toself", name="Company Average", line_color=COLOR_SUCCESS, opacity=0.5))
    fig.update_layout(height=350, showlegend=True, margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)


def render():
    st.title("🔍 Customer Search")
    st.caption("Search, filter, and inspect any of the 7,043 real customers in this dataset.")

    df = load_customer_data()
    filtered = _apply_filters(df)

    st.markdown(f"##### Results: {len(filtered):,} of {len(df):,} customers")

    if len(filtered) == 0:
        st.warning("No customers match your search/filter criteria. Try widening your filters.")
        return

    csv = filtered[DISPLAY_COLUMNS].to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Filtered Results (CSV)", data=csv, file_name="customer_search_results.csv", mime="text/csv")

    selected_customer_id = _render_grid(filtered[DISPLAY_COLUMNS].reset_index(drop=True))

    if selected_customer_id:
        _render_customer_detail(df, selected_customer_id)
    else:
        st.info("👆 Select a row (or choose a Customer ID) above to view a full customer profile.")

    logger.info(f"Customer Search rendered with {len(filtered)} filtered results.")
