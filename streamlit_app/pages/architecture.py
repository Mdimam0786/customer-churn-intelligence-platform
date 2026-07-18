"""
Architecture page.

Shows the end-to-end system design, tech stack, data flow, and the
real engineering trade-offs made throughout this project (no live
Postgres, no network for several ML/stats libraries, no Power BI
Desktop, etc.) -- condensed from docs/technical_design_document.md.

Includes a genuinely LIVE dependency status check (not a static claim)
so a visitor can see exactly which optional packages are actually
importable in the environment currently running this app.
"""

import importlib
import os

import streamlit as st

from config import ASSETS_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

OPTIONAL_PACKAGES = {
    "streamlit_option_menu": "Styled sidebar navigation with icons",
    "st_aggrid": "Enterprise-grade interactive data grid",
    "shap": "Genuine SHAP model explainability",
    "folium": "Rich interactive maps (streamlit-folium)",
}


def _check_package(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def render():
    st.title("🏗️ Architecture")
    st.caption("The real end-to-end system design behind this platform — and the genuine trade-offs made building it.")

    # ---------------------------------------------------------------
    # Architecture diagram
    # ---------------------------------------------------------------
    diagram_path = os.path.join(ASSETS_DIR, "architecture_diagram.png")
    if os.path.exists(diagram_path):
        st.image(diagram_path, use_container_width=True, caption="End-to-end platform architecture (Phase 9)")
    else:
        st.info("Architecture diagram not found at assets/architecture_diagram.png.")

    st.markdown("""
```
Real IBM Telco Customer Churn Data (XLSX + CSV)
            │
            ▼
   Data Engineering  →  Star Schema (6 dims + 1 fact)
            │              PostgreSQL-target / SQLite demo
     ┌──────┼──────────────┬──────────────┐
     ▼      ▼              ▼              ▼
   SQL    EDA          Statistics       Machine Learning
     │      │              │                │
     └──────┴──────┬───────┴────────────────┘
                    ▼
          Power BI  +  BI Synthesis  +  This Streamlit App
```
""")

    # ---------------------------------------------------------------
    # Tech stack
    # ---------------------------------------------------------------
    st.markdown("### Tech Stack")
    stack_cols = st.columns(4)
    stack_items = [
        ("🐍 Core", "Python, pandas, NumPy, SciPy"),
        ("🤖 ML", "scikit-learn (Gradient Boosting, Random Forest, K-Means)"),
        ("🗄️ Data", "PostgreSQL 14+ (target) / SQLite (demo)"),
        ("📊 BI & Web", "Power BI (DAX, star schema) + Streamlit (this app)"),
    ]
    for col, (label, val) in zip(stack_cols, stack_items):
        with col:
            st.markdown(f"**{label}**")
            st.caption(val)

    st.divider()

    # ---------------------------------------------------------------
    # Engineering decisions & trade-offs
    # ---------------------------------------------------------------
    st.markdown("### Key Engineering Decisions & Trade-offs")
    st.markdown("""
| Decision | Why |
|---|---|
| No fabricated calendar date dimension | Source data has no real subscription date — tenure cohorts substitute throughout SQL, Power BI, and this app rather than inventing dates |
| SQLite as a local stand-in for PostgreSQL | No live Postgres server in the build environment; every query's CTE/window-function logic verified identical on both engines |
| `churn_score`/`cltv` excluded from ML model inputs | Prevents the model from just memorizing IBM's own vendor-derived fields — keeps it useful for brand-new customers |
| Manual OLS/logistic regression inference | `statsmodels` unavailable (no network); re-implemented via the identical closed-form estimators it uses internally |
| Permutation importance + marginal contribution (not SHAP) | `shap` unavailable in the build environment for the fallback path — genuine alternative techniques, not an approximation |
| RFM **proxies**, not true RFM | No transaction/purchase-event log exists in this dataset |
| Per-service adoption classifiers instead of a market-basket recommender | Same reason — no transaction log for genuine collaborative filtering |
""")

    st.divider()

    # ---------------------------------------------------------------
    # Live dependency status
    # ---------------------------------------------------------------
    st.markdown("### Live Optional Dependency Status")
    st.caption("Checked right now, in the environment currently running this app — not a static claim.")

    cols = st.columns(len(OPTIONAL_PACKAGES))
    for col, (pkg, description) in zip(cols, OPTIONAL_PACKAGES.items()):
        with col:
            available = _check_package(pkg)
            icon = "✅" if available else "⚪"
            status_text = "Installed" if available else "Not installed (fallback active)"
            st.markdown(f"{icon} **{pkg}**")
            st.caption(f"{description}\n\n*{status_text}*")

    st.info(
        "ℹ️ Every page in this app is built to degrade gracefully when an optional package is "
        "missing — falling back to a native Streamlit equivalent (e.g. `st.dataframe` instead of "
        "AgGrid, permutation importance instead of SHAP) rather than crashing."
    )

    logger.info("Architecture page rendered.")
