"""
About page.

Says who built this project and what it's about, with links to
GitHub, LinkedIn, and a resume download.
"""

import os

import streamlit as st

from config import GITHUB_URL, LINKEDIN_URL, RESUME_PATH, APP_TITLE
from utils.data_loader import load_customer_data, get_headline_kpis
from utils.logger import get_logger

logger = get_logger(__name__)


def render():
    st.title("About the Developer")

    col_photo, col_bio = st.columns([1, 3])
    with col_photo:
        st.markdown(
            """
            <div style="width:120px; height:120px; border-radius:50%;
                        background: linear-gradient(135deg, var(--color-primary), #4A90D9);
                        display:flex; align-items:center; justify-content:center;
                        color:white; font-size:2.5rem; font-weight:700;">
                MI
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_bio:
        st.markdown("### Md Imamuddin")
        st.markdown("**Data Analyst • Data Scientist • Business Intelligence Developer**")
        st.write(
            "I enjoy transforming raw business data into actionable insights using SQL, Python, Machine Learning, Power BI, and Streamlit. I build end-to-end analytics solutions that combine data engineering, statistical analysis, predictive modeling, and interactive dashboards to support data-driven decision-making."
        )

    st.divider()

    st.markdown("### Find Me Here")
    lc1, lc2, lc3 = st.columns(3)
    with lc1:
        st.link_button("GitHub", GITHUB_URL, use_container_width=True)
    with lc2:
        st.link_button("LinkedIn", LINKEDIN_URL, use_container_width=True)
    with lc3:
        if os.path.exists(RESUME_PATH):
            with open(RESUME_PATH, "rb") as f:
                st.download_button("Download Resume", data=f.read(), file_name="resume.pdf", mime="application/pdf", use_container_width=True)
        else:
            st.button("Resume", disabled=True, use_container_width=True)

    st.divider()

    st.markdown(f"### About This Project")
    st.write(
        "This started as a churn analysis project and grew into something bigger — a full "
        "pipeline covering data engineering, SQL, statistics, machine learning, a Power BI "
        "report, and this app, all built on IBM's real Telco Customer Churn dataset "
        "(7,043 customers). Every number on this page and throughout the app is calculated "
        "from that real data — nothing here is made up."
    )

    try:
        df = load_customer_data()
        kpis = get_headline_kpis(df)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Customers Analyzed", f"{kpis['total_customers']:,}")
        c2.metric("Churn Rate", f"{kpis['churn_rate_pct']:.2f}%")
        c3.metric("Churn Model ROC-AUC", "0.854")
        c4.metric("Insights Documented", "105+")
    except Exception as e:
        logger.warning(f"Could not load live KPIs on About page: {e}")

    st.markdown("""
**What's in the full project:**
- A real database (star schema), built for PostgreSQL
- SQL work covering CTEs, window functions, views, and stored procedures
- A 9-page Power BI report with a full set of DAX measures
- Over 100 insights, each backed by a real number
- A full statistics workflow — hypothesis testing, ANOVA, regression
- Models for churn, lifetime value, customer segments, and upsell targeting
- A short list of actual business recommendations with rough revenue estimates
- This app, so you can look through all of it without needing Power BI
""")

    st.divider()
    st.caption("Author: Md Imamuddin")

    logger.info("About page rendered.")
