"""
Validation module.

Runs schema, type, range, and business-rule checks against the raw
ingested DataFrame BEFORE any cleaning happens, so we have a clear
"before" picture for the Data Quality Report. Nothing here silently
fixes anything — it only detects and reports.
"""

import os
import sys
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.utils.logger import get_logger

logger = get_logger(__name__)

EXPECTED_COLUMNS = [
    "CustomerID", "Count", "Country", "State", "City", "Zip Code", "Lat Long",
    "Latitude", "Longitude", "Gender", "Senior Citizen", "Partner", "Dependents",
    "Tenure Months", "Phone Service", "Multiple Lines", "Internet Service",
    "Online Security", "Online Backup", "Device Protection", "Tech Support",
    "Streaming TV", "Streaming Movies", "Contract", "Paperless Billing",
    "Payment Method", "Monthly Charges", "Total Charges", "Churn Label",
    "Churn Value", "Churn Score", "CLTV", "Churn Reason",
]

CATEGORICAL_DOMAINS = {
    "Gender": {"Male", "Female"},
    "Senior Citizen": {"Yes", "No"},
    "Partner": {"Yes", "No"},
    "Dependents": {"Yes", "No"},
    "Phone Service": {"Yes", "No"},
    "Internet Service": {"DSL", "Fiber optic", "No"},
    "Contract": {"Month-to-month", "One year", "Two year"},
    "Paperless Billing": {"Yes", "No"},
    "Churn Label": {"Yes", "No"},
}


def check_schema(df: pd.DataFrame) -> dict:
    missing_cols = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    extra_cols = [c for c in df.columns if c not in EXPECTED_COLUMNS]
    return {
        "missing_expected_columns": missing_cols,
        "unexpected_extra_columns": extra_cols,
        "schema_ok": len(missing_cols) == 0,
    }


def check_nulls(df: pd.DataFrame) -> pd.DataFrame:
    null_counts = df.isnull().sum()
    null_pct = (null_counts / len(df) * 100).round(2)
    out = pd.DataFrame({"null_count": null_counts, "null_pct": null_pct})
    return out[out["null_count"] > 0].sort_values("null_count", ascending=False)


def check_duplicates(df: pd.DataFrame) -> dict:
    full_row_dupes = df.duplicated().sum()
    key_dupes = df.duplicated(subset=["CustomerID"]).sum()
    return {"full_row_duplicates": int(full_row_dupes), "customer_id_duplicates": int(key_dupes)}


def check_categorical_domains(df: pd.DataFrame) -> dict:
    violations = {}
    for col, allowed in CATEGORICAL_DOMAINS.items():
        if col not in df.columns:
            continue
        actual = set(df[col].dropna().unique())
        unexpected = actual - allowed
        if unexpected:
            violations[col] = list(unexpected)
    return violations


def check_totalcharges_blank_quirk(df: pd.DataFrame) -> pd.DataFrame:
    """The documented real-world quirk: tenure=0 customers with blank TotalCharges."""
    tc = df["Total Charges"].astype(str).str.strip()
    mask = tc.eq("") | tc.eq("nan")
    return df.loc[mask, ["CustomerID", "Tenure Months", "Monthly Charges", "Total Charges"]]


def check_numeric_ranges(df: pd.DataFrame) -> dict:
    issues = {}
    if (df["Monthly Charges"] < 0).any():
        issues["negative_monthly_charges"] = int((df["Monthly Charges"] < 0).sum())
    if (df["Tenure Months"] < 0).any():
        issues["negative_tenure"] = int((df["Tenure Months"] < 0).sum())
    if (df["Churn Score"] < 0).any() or (df["Churn Score"] > 100).any():
        issues["churn_score_out_of_0_100_range"] = int(
            ((df["Churn Score"] < 0) | (df["Churn Score"] > 100)).sum()
        )
    if (df["CLTV"] < 0).any():
        issues["negative_cltv"] = int((df["CLTV"] < 0).sum())
    return issues


def check_referential_consistency(df: pd.DataFrame) -> dict:
    """Business-rule check: Churn Value (0/1) must agree with Churn Label (No/Yes)."""
    expected = df["Churn Label"].map({"Yes": 1, "No": 0})
    mismatches = (df["Churn Value"] != expected).sum()
    return {"churn_value_label_mismatches": int(mismatches)}


def run_validation(df: pd.DataFrame) -> dict:
    logger.info("Running validation suite on raw ingested data...")
    report = {
        "row_count": len(df),
        "column_count": df.shape[1],
        "schema": check_schema(df),
        "duplicates": check_duplicates(df),
        "categorical_domain_violations": check_categorical_domains(df),
        "numeric_range_issues": check_numeric_ranges(df),
        "referential_consistency": check_referential_consistency(df),
    }
    null_report = check_nulls(df)
    report["fields_with_nulls"] = null_report.to_dict(orient="index")

    quirk_df = check_totalcharges_blank_quirk(df)
    report["totalcharges_blank_quirk_rows"] = len(quirk_df)
    report["totalcharges_blank_quirk_customer_ids"] = quirk_df["CustomerID"].tolist()

    logger.info(f"Validation complete. Schema OK: {report['schema']['schema_ok']}, "
                f"Duplicates: {report['duplicates']}, "
                f"TotalCharges blank quirk rows: {report['totalcharges_blank_quirk_rows']}")
    return report


if __name__ == "__main__":
    from src.data_engineering.ingest import run_ingestion
    df, _ = run_ingestion()
    report = run_validation(df)
    import json
    print(json.dumps(report, indent=2, default=str))
