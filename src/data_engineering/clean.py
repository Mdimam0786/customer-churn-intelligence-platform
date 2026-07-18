"""
Cleaning module.

Applies deterministic, documented fixes to the two known real-world data
quality issues found during validation. No values are invented — every
imputation rule below is derived from other REAL fields already present
on the same row (e.g., TotalCharges for a zero-tenure customer is set
equal to that customer's own MonthlyCharges, not a synthetic average).
"""

import os
import sys
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.utils.logger import get_logger

logger = get_logger(__name__)


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """snake_case for programmatic use; original labels preserved in data dictionary."""
    rename_map = {
        "CustomerID": "customer_id",
        "Count": "row_count_flag",
        "Country": "country",
        "State": "state",
        "City": "city",
        "Zip Code": "zip_code",
        "Lat Long": "lat_long_raw",
        "Latitude": "latitude",
        "Longitude": "longitude",
        "Gender": "gender",
        "Senior Citizen": "senior_citizen",
        "Partner": "has_partner",
        "Dependents": "has_dependents",
        "Tenure Months": "tenure_months",
        "Phone Service": "phone_service",
        "Multiple Lines": "multiple_lines",
        "Internet Service": "internet_service",
        "Online Security": "online_security",
        "Online Backup": "online_backup",
        "Device Protection": "device_protection",
        "Tech Support": "tech_support",
        "Streaming TV": "streaming_tv",
        "Streaming Movies": "streaming_movies",
        "Contract": "contract_type",
        "Paperless Billing": "paperless_billing",
        "Payment Method": "payment_method",
        "Monthly Charges": "monthly_charges",
        "Total Charges": "total_charges",
        "Churn Label": "churn_label",
        "Churn Value": "churn_flag",
        "Churn Score": "churn_score",
        "CLTV": "cltv",
        "Churn Reason": "churn_reason",
    }
    return df.rename(columns=rename_map)


def fix_total_charges(df: pd.DataFrame) -> pd.DataFrame:
    """
    Documented quirk: 11 rows have tenure_months == 0 and a blank
    total_charges string (brand-new customers who haven't been billed
    beyond signup yet). Coerce to numeric, then impute ONLY those rows
    using that same customer's own monthly_charges as the logical total
    for zero elapsed months. Flag every imputed row for transparency.
    """
    df = df.copy()
    df["total_charges_raw"] = df["total_charges"]
    df["total_charges"] = pd.to_numeric(df["total_charges"], errors="coerce")

    zero_tenure_blank_mask = df["total_charges"].isna() & (df["tenure_months"] == 0)
    n_fixed = int(zero_tenure_blank_mask.sum())

    df["is_new_customer_imputed_charges"] = zero_tenure_blank_mask
    df.loc[zero_tenure_blank_mask, "total_charges"] = df.loc[zero_tenure_blank_mask, "monthly_charges"]

    remaining_na = df["total_charges"].isna().sum()
    if remaining_na > 0:
        logger.warning(f"{remaining_na} total_charges values remain null after the known-quirk fix — "
                        f"these are NOT covered by the documented pattern and are left null rather than guessed.")

    logger.info(f"Fixed {n_fixed} total_charges blanks (zero-tenure new customers); "
                f"{remaining_na} unexplained nulls remain (left as-is).")
    return df


def fix_churn_reason(df: pd.DataFrame) -> pd.DataFrame:
    """
    Churn Reason is null-by-design for the 5,174 customers who never
    churned. Replace with an explicit category so the field is safe to
    group/filter on in SQL and Power BI without null-handling surprises.
    """
    df = df.copy()
    before_na = df["churn_reason"].isna().sum()
    df["churn_reason"] = df["churn_reason"].fillna("Not Applicable - Active Customer")
    logger.info(f"Filled {before_na} null churn_reason values with explicit 'Not Applicable' category.")
    return df


def standardize_binary_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Convert Yes/No text fields to boolean flags for modeling convenience, keeping originals."""
    df = df.copy()
    yes_no_cols = [
        "senior_citizen", "has_partner", "has_dependents", "phone_service",
        "paperless_billing", "churn_label",
    ]
    for col in yes_no_cols:
        df[f"{col}_bool"] = df[col].map({"Yes": True, "No": False})
    return df


def drop_redundant_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    'row_count_flag' is always 1 for every row in the source (an IBM
    export artifact, not a real measure) and lat_long_raw duplicates
    latitude/longitude already split into their own columns.
    """
    df = df.copy()
    always_one = (df["row_count_flag"] == 1).all()
    if always_one:
        df = df.drop(columns=["row_count_flag"])
        logger.info("Dropped 'row_count_flag' — confirmed constant (=1) across all rows, an export artifact.")
    df = df.drop(columns=["lat_long_raw"])
    logger.info("Dropped 'lat_long_raw' — redundant with separate latitude/longitude columns.")
    return df


def run_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Starting cleaning pipeline...")
    df = standardize_column_names(df)
    df = fix_total_charges(df)
    df = fix_churn_reason(df)
    df = standardize_binary_flags(df)
    df = drop_redundant_columns(df)
    logger.info(f"Cleaning complete. Final shape: {df.shape}")
    return df


if __name__ == "__main__":
    from src.data_engineering.ingest import run_ingestion
    raw_df, _ = run_ingestion()
    clean_df = run_cleaning(raw_df)
    print(clean_df.head(3).T)
    print("\nDtypes:")
    print(clean_df.dtypes)
