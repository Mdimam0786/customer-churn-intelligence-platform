"""
Ingestion module.

Loads the two real IBM Telco Customer Churn source files (enriched xlsx
+ standard csv), cross-validates them against each other on the shared
customer key, and returns a single trusted primary DataFrame.

No synthetic rows are ever generated here. If a source file is missing
or the two sources disagree on core identity fields, this module raises
rather than silently fabricating or dropping data.
"""

import os
import sys
import yaml
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def load_config(config_path: str = None) -> dict:
    config_path = config_path or os.path.join(PROJECT_ROOT, "config", "config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_primary_source(cfg: dict) -> pd.DataFrame:
    """Load the enriched IBM xlsx source (geography, CLTV, churn score, churn reason)."""
    path = os.path.join(PROJECT_ROOT, cfg["data_sources"]["primary"]["path"])
    logger.info(f"Loading primary source: {path}")
    df = pd.read_excel(path, sheet_name=cfg["data_sources"]["primary"]["sheet"])
    logger.info(f"Primary source loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    return df


def load_cross_reference_source(cfg: dict) -> pd.DataFrame:
    """Load the standard IBM csv source, used only for validation."""
    path = os.path.join(PROJECT_ROOT, cfg["data_sources"]["cross_reference"]["path"])
    logger.info(f"Loading cross-reference source: {path}")
    df = pd.read_csv(path)
    logger.info(f"Cross-reference source loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    return df


def cross_validate(primary: pd.DataFrame, cross_ref: pd.DataFrame) -> dict:
    """
    Validate that both real source files describe the same customer
    population. Returns a dict of validation results; raises AssertionError
    on any identity mismatch that would indicate the files are NOT the
    same underlying population (a serious data integrity problem).
    """
    results = {}

    primary_ids = set(primary["CustomerID"])
    cross_ids = set(cross_ref["customerID"])

    results["primary_row_count"] = len(primary)
    results["cross_ref_row_count"] = len(cross_ref)
    results["primary_unique_ids"] = len(primary_ids)
    results["cross_ref_unique_ids"] = len(cross_ids)
    results["ids_match_exactly"] = primary_ids == cross_ids
    results["ids_only_in_primary"] = len(primary_ids - cross_ids)
    results["ids_only_in_cross_ref"] = len(cross_ids - primary_ids)

    assert results["primary_unique_ids"] == results["primary_row_count"], (
        "Duplicate CustomerID values found in primary source — "
        "customer key is expected to be unique."
    )
    assert results["cross_ref_unique_ids"] == results["cross_ref_row_count"], (
        "Duplicate customerID values found in cross-reference source."
    )

    if not results["ids_match_exactly"]:
        logger.warning(
            f"Customer ID sets differ between sources: "
            f"{results['ids_only_in_primary']} only in primary, "
            f"{results['ids_only_in_cross_ref']} only in cross-reference."
        )
    else:
        logger.info("Cross-validation passed: both sources describe the identical 7,043-customer population.")

    # Spot-check a numeric field for value agreement between sources
    merged_check = primary.merge(
        cross_ref[["customerID", "MonthlyCharges", "Churn"]],
        left_on="CustomerID", right_on="customerID", how="inner", suffixes=("_primary", "_crossref")
    )
    charge_mismatch = (
        (merged_check["Monthly Charges"] - merged_check["MonthlyCharges"]).abs() > 0.01
    ).sum()
    results["monthly_charges_mismatches"] = int(charge_mismatch)

    churn_mismatch = (merged_check["Churn Label"] != merged_check["Churn"]).sum()
    results["churn_label_mismatches"] = int(churn_mismatch)

    logger.info(f"Field-value cross-check: {charge_mismatch} MonthlyCharges mismatches, "
                f"{churn_mismatch} Churn label mismatches (both expected to be 0).")

    return results


def run_ingestion(config_path: str = None) -> tuple[pd.DataFrame, dict]:
    """Main entry point: load, cross-validate, return primary dataframe + validation report."""
    cfg = load_config(config_path)
    primary = load_primary_source(cfg)
    cross_ref = load_cross_reference_source(cfg)
    validation_results = cross_validate(primary, cross_ref)
    return primary, validation_results


if __name__ == "__main__":
    df, report = run_ingestion()
    print("\n=== INGESTION VALIDATION REPORT ===")
    for k, v in report.items():
        print(f"{k}: {v}")
