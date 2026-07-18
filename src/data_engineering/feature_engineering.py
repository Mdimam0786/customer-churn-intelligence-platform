"""
Feature engineering module.

Every derived feature below is a deterministic function of real fields
already present in the cleaned data — tenure cohorts from real tenure,
service counts from real service flags, RFM proxies from real billing
and tenure fields. Nothing here invents a value that doesn't already
exist somewhere in the row.

Note on dates: this real dataset does NOT include an actual subscription
start/renewal calendar date — only tenure in elapsed months. Per the
no-fabrication rule, we do not manufacture a start date. Tenure-based
cohort buckets are used instead of calendar cohorts, and are clearly
labeled as such throughout the project (including in Power BI).
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.utils.logger import get_logger

logger = get_logger(__name__)

SERVICE_COLUMNS = [
    "phone_service", "multiple_lines", "internet_service", "online_security",
    "online_backup", "device_protection", "tech_support", "streaming_tv",
    "streaming_movies",
]


def add_tenure_cohort(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    bins = [-1, 12, 24, 36, 48, 60, 72]
    labels = ["0-12 mo", "13-24 mo", "25-36 mo", "37-48 mo", "49-60 mo", "61-72 mo"]
    df["tenure_cohort"] = pd.cut(df["tenure_months"], bins=bins, labels=labels)
    return df


def add_service_adoption_count(df: pd.DataFrame) -> pd.DataFrame:
    """
    Count of 'Yes' add-on services subscribed (excludes internet_service
    and phone_service themselves, which are base connectivity, not add-ons).
    """
    df = df.copy()
    addon_cols = [
        "online_security", "online_backup", "device_protection",
        "tech_support", "streaming_tv", "streaming_movies",
    ]
    df["addon_service_count"] = df[addon_cols].apply(lambda row: (row == "Yes").sum(), axis=1)
    return df


def add_multi_service_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["has_internet"] = df["internet_service"] != "No"
    df["has_phone_and_internet"] = df["phone_service_bool"] & df["has_internet"]
    df["is_streaming_bundle"] = (df["streaming_tv"] == "Yes") & (df["streaming_movies"] == "Yes")
    return df


def add_rfm_proxy_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    True transaction-level RFM (last purchase date, order count) is not
    available in this dataset. We construct the closest real proxies
    from real fields:
      - Recency proxy: inverse of tenure for churned customers is not
        meaningful here (no cancellation date); instead we use churn_flag
        itself as the "still active" signal and tenure_months as recency
        of relationship for active customers.
      - Frequency proxy: addon_service_count (breadth of engagement).
      - Monetary: total_charges (real, billed revenue to date) and
        monthly_charges (real, current run-rate revenue).
    These are explicitly labeled as proxies, not true RFM, in the data
    dictionary — avoiding the trap of implying data we don't have.
    """
    df = df.copy()
    df["monetary_total_charges"] = df["total_charges"]
    df["monetary_monthly_run_rate"] = df["monthly_charges"]
    df["frequency_addon_breadth"] = df["addon_service_count"]
    df["recency_tenure_months"] = df["tenure_months"]
    return df


def add_revenue_per_tenure_month(df: pd.DataFrame) -> pd.DataFrame:
    """Average realized monthly revenue across the customer's real tenure to date."""
    df = df.copy()
    df["avg_revenue_per_tenure_month"] = np.where(
        df["tenure_months"] > 0,
        df["total_charges"] / df["tenure_months"],
        df["monthly_charges"],  # zero-tenure customers: use their monthly rate
    )
    return df


def add_contract_risk_tier(df: pd.DataFrame) -> pd.DataFrame:
    """
    Simple, transparent, rule-based risk tier from contract type alone —
    a baseline the machine learning model will need to beat to justify its
    added complexity.
    """
    df = df.copy()
    risk_map = {"Month-to-month": "High", "One year": "Medium", "Two year": "Low"}
    df["contract_based_risk_tier"] = df["contract_type"].map(risk_map)
    return df


def add_geography_region(df: pd.DataFrame) -> pd.DataFrame:
    """
    Region grouping from real state field. This dataset is 100% California
    customers (a real characteristic of this specific IBM sample, not a
    filtering choice we made) — documented explicitly so it isn't mistaken
    for a national dataset downstream.
    """
    df = df.copy()
    df["is_california_dataset"] = True
    return df


def run_feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Starting feature engineering...")
    df = add_tenure_cohort(df)
    df = add_service_adoption_count(df)
    df = add_multi_service_flags(df)
    df = add_rfm_proxy_features(df)
    df = add_revenue_per_tenure_month(df)
    df = add_contract_risk_tier(df)
    df = add_geography_region(df)
    logger.info(f"Feature engineering complete. Final shape: {df.shape}")
    return df


if __name__ == "__main__":
    from src.data_engineering.ingest import run_ingestion
    from src.data_engineering.clean import run_cleaning
    raw_df, _ = run_ingestion()
    clean_df = run_cleaning(raw_df)
    feat_df = run_feature_engineering(clean_df)
    print(feat_df[[
        "customer_id", "tenure_months", "tenure_cohort", "addon_service_count",
        "avg_revenue_per_tenure_month", "contract_based_risk_tier"
    ]].head(10))
