"""
Cached data loading utilities.

Every page imports load_customer_data() / load_ml_predictions() from
here rather than reading CSVs directly -- @st.cache_data ensures the
~7,043-row dataset is parsed from disk exactly once per app session
(or until the underlying file changes), not once per page render.
This is the single most important performance lever in a Streamlit app
working with real, on-disk data.
"""

import os
import pandas as pd
import streamlit as st

from config import PROCESSED_DATA_PATH, ML_PREDICTIONS_PATH
from utils.logger import get_logger

logger = get_logger(__name__)


@st.cache_data(show_spinner="Loading real customer data...")
def load_customer_data() -> pd.DataFrame:
    """
    Loads the real, Phase 2/3-processed customer dataset. Cached across
    reruns -- Streamlit reruns the whole script top-to-bottom on every
    widget interaction, so without this decorator a 7,043-row CSV would
    be re-read from disk on every single click in the app.
    """
    try:
        if not os.path.exists(PROCESSED_DATA_PATH):
            raise FileNotFoundError(
                f"Processed data not found at {PROCESSED_DATA_PATH}. "
                "Run the Phase 2 ETL pipeline first: "
                "`python3 -m src.data_engineering.etl_pipeline`"
            )
        df = pd.read_csv(PROCESSED_DATA_PATH)
        logger.info(f"Loaded {len(df)} real customer records.")
        return df
    except Exception as e:
        logger.error(f"Failed to load customer data: {e}")
        raise


@st.cache_data(show_spinner="Loading model predictions...")
def load_ml_predictions() -> pd.DataFrame:
    """Loads the real Phase 7 model predictions export (see Power BI Page 9 build guide)."""
    try:
        if not os.path.exists(ML_PREDICTIONS_PATH):
            raise FileNotFoundError(
                f"ML predictions not found at {ML_PREDICTIONS_PATH}. "
                "Run `python3 -m src.ml.churn_model` and export predictions first."
            )
        df = pd.read_csv(ML_PREDICTIONS_PATH)
        logger.info(f"Loaded {len(df)} real ML prediction records.")
        return df
    except Exception as e:
        logger.error(f"Failed to load ML predictions: {e}")
        raise


@st.cache_data(show_spinner=False)
def get_headline_kpis(df: pd.DataFrame) -> dict:
    """
    Computes the same headline KPIs used throughout every phase report
    (Phase 3 EDA, Phase 8 BI Synthesis) -- kept in one place so the
    Streamlit Home page can never silently drift from the real,
    already-validated numbers in the rest of the project.
    """
    total = len(df)
    churned = int(df["churn_flag"].sum())
    return {
        "total_customers": total,
        "churned_customers": churned,
        "retained_customers": total - churned,
        "churn_rate_pct": round(100 * churned / total, 2) if total else 0,
        "total_revenue": round(df["total_charges"].sum(), 2),
        "current_mrr": round(df["monthly_charges"].sum(), 2),
        "mrr_at_risk": round(df.loc[df.churn_flag == 1, "monthly_charges"].sum(), 2),
        "avg_cltv": round(df["cltv"].mean(), 2),
    }
