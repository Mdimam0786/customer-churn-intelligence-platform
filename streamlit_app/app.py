"""
Main entry point for the Customer Subscription & Churn Intelligence
Platform Streamlit application.

Author: Md Imamuddin

Run with: streamlit run app.py

Architecture note: this app uses a single-file router (app.py imports
and calls a render() function from each page module in pages/) instead
of Streamlit's built-in multi-page folder convention. This is on
purpose — it lets the custom sidebar (built with streamlit-option-menu,
with icons and grouped sections) control navigation, instead of
Streamlit's plain default page list. Each page still lives in its own
file in `pages/` and exposes one `render()` function, so the code stays
just as organized as Streamlit's native multi-page setup.
"""

import streamlit as st

from config import APP_TITLE, APP_ICON, APP_SUBTITLE, GITHUB_URL, LINKEDIN_URL
from utils.theme import init_theme_state, inject_global_css, toggle_theme, render_footer
from utils.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

init_theme_state()
inject_global_css()

# -----------------------------------------------------------------
# Error boundary: any unhandled exception anywhere in a page render
# shows a clean message instead of a raw Streamlit traceback -- a
# production app should never show an end user a Python stack trace.
# -----------------------------------------------------------------
def safe_render(render_fn, page_name: str):
    try:
        render_fn()
    except FileNotFoundError as e:
        logger.error(f"Data file missing while rendering '{page_name}': {e}")
        st.error(
            f"⚠️ This page needs a data file that isn't present yet.\n\n"
            f"**Details:** {e}"
        )
    except Exception as e:
        logger.exception(f"Unhandled error rendering page '{page_name}'")
        st.error(
            "⚠️ Something went wrong loading this page. "
            "This has been logged. Please try refreshing, or pick a different page from the sidebar."
        )
        with st.expander("Technical details (for debugging)"):
            st.exception(e)


# -----------------------------------------------------------------
# Sidebar navigation
# -----------------------------------------------------------------
def render_sidebar() -> str:
    with st.sidebar:
        st.markdown(
            f"""
            <div style="padding: 0.5rem 0 1rem 0;">
                <div style="font-size:1.4rem; font-weight:700; line-height:1.2;">📊 Churn Intelligence</div>
                <div style="font-size:0.82rem; color: var(--text-secondary);">{APP_SUBTITLE}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        try:
            from streamlit_option_menu import option_menu

            selected = option_menu(
                menu_title=None,
                options=[
                    "Home",
                    "Exploratory Data Analysis",
                    "Statistics",
                    "SQL Insights",
                    "Customer Search",
                    "Segment Search",
                    "Geography Search",
                    "Plan & Contract Search",
                    "Churn & LTV Prediction",
                    "Model Explainability (SHAP)",
                    "Architecture",
                    "Documentation",
                    "About",
                ],
                icons=[
                    "house", "bar-chart", "calculator", "database",
                    "person-lines-fill", "people", "geo-alt", "file-earmark-text",
                    "cpu", "diagram-3",
                    "diagram-2", "book", "info-circle",
                ],
                menu_icon="cast",
                default_index=0,
                styles={
                    "container": {"padding": "0!important", "background-color": "transparent"},
                    "icon": {"font-size": "16px"},
                    "nav-link": {"font-size": "14px", "text-align": "left", "margin": "2px 0", "border-radius": "8px"},
                    "nav-link-selected": {"background-color": "var(--color-primary)"},
                },
            )
        except ImportError:
            # streamlit-option-menu isn't installed -- fall back to a plain
            # native radio so the app still runs, just with a plainer sidebar.
            logger.warning("streamlit-option-menu not installed; falling back to st.radio navigation.")
            selected = st.radio(
                "Navigate",
                [
                    "Home", "Exploratory Data Analysis", "Statistics", "SQL Insights",
                    "Customer Search", "Segment Search", "Geography Search", "Plan & Contract Search",
                    "Churn & LTV Prediction", "Model Explainability (SHAP)",
                    "Architecture", "Documentation", "About",
                ],
                label_visibility="collapsed",
            )

        st.divider()

        # Dark/Light mode toggle
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption("Appearance")
        with col2:
            is_dark = st.session_state.theme_mode == "dark"
            new_val = st.toggle("🌙", value=is_dark, key="theme_toggle_widget", label_visibility="collapsed")
            if new_val != is_dark:
                toggle_theme()
                st.rerun()

        st.divider()
        st.caption("Links")
        st.markdown(
            f"[GitHub ↗]({GITHUB_URL}) &nbsp;|&nbsp; [LinkedIn ↗]({LINKEDIN_URL})",
            unsafe_allow_html=True,
        )
        st.caption("Built on real IBM Telco Customer Churn data — no synthetic records anywhere in this app.")

    return selected


# -----------------------------------------------------------------
# Router
# -----------------------------------------------------------------
def main():
    selected_page = render_sidebar()

    if selected_page == "Home":
        from pages import home
        safe_render(home.render, "Home")

    elif selected_page == "Exploratory Data Analysis":
        from pages import eda
        safe_render(eda.render, "Exploratory Data Analysis")

    elif selected_page == "Statistics":
        from pages import statistics
        safe_render(statistics.render, "Statistics")

    elif selected_page == "SQL Insights":
        from pages import sql_insights
        safe_render(sql_insights.render, "SQL Insights")

    elif selected_page == "Customer Search":
        from pages import customer_search
        safe_render(customer_search.render, "Customer Search")

    elif selected_page == "Segment Search":
        from pages import segment_search
        safe_render(segment_search.render, "Segment Search")

    elif selected_page == "Geography Search":
        from pages import geography_search
        safe_render(geography_search.render, "Geography Search")

    elif selected_page == "Plan & Contract Search":
        from pages import plan_contract_search
        safe_render(plan_contract_search.render, "Plan & Contract Search")

    elif selected_page == "Churn & LTV Prediction":
        from pages import churn_ltv_prediction
        safe_render(churn_ltv_prediction.render, "Churn & LTV Prediction")

    elif selected_page == "Model Explainability (SHAP)":
        from pages import explainability
        safe_render(explainability.render, "Model Explainability (SHAP)")

    elif selected_page == "Architecture":
        from pages import architecture
        safe_render(architecture.render, "Architecture")

    elif selected_page == "Documentation":
        from pages import documentation
        safe_render(documentation.render, "Documentation")

    elif selected_page == "About":
        from pages import about
        safe_render(about.render, "About")

    render_footer()


if __name__ == "__main__":
    main()
