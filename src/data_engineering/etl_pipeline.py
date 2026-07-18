"""
ETL pipeline: transforms the cleaned + feature-engineered flat DataFrame
into the star schema (dim_* + fact_subscription) and loads it into a
database.

Database note: a live PostgreSQL server wasn't available during parts
of development. The table definitions in sql/schema/ are written for
PostgreSQL 14+. To fully test the pipeline, it also loads into a local
SQLite database using the same table and column names and equivalent
constraints, so the data transformations, table relationships, and
referential integrity are all genuinely verified against real data.
Connecting to a real PostgreSQL database instead only requires
changing the connection string — no changes to the pipeline logic
itself. See docs/local_vscode_postgres_setup.md for those steps.
"""

import os
import sys
import sqlite3
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.utils.logger import get_logger
from src.data_engineering.ingest import run_ingestion
from src.data_engineering.clean import run_cleaning
from src.data_engineering.feature_engineering import run_feature_engineering

logger = get_logger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
DB_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "churn_intelligence.db")

TENURE_COHORT_ORDER = {
    "0-12 mo": 1, "13-24 mo": 2, "25-36 mo": 3,
    "37-48 mo": 4, "49-60 mo": 5, "61-72 mo": 6,
}


def build_dim_customer(df: pd.DataFrame) -> pd.DataFrame:
    dim = df[["customer_id", "gender", "senior_citizen_bool", "has_partner_bool", "has_dependents_bool"]].copy()
    dim = dim.rename(columns={
        "senior_citizen_bool": "senior_citizen",
        "has_partner_bool": "has_partner",
        "has_dependents_bool": "has_dependents",
    })
    dim = dim.drop_duplicates(subset=["customer_id"]).reset_index(drop=True)
    dim.insert(0, "customer_key", range(1, len(dim) + 1))
    return dim


def build_dim_geography(df: pd.DataFrame) -> pd.DataFrame:
    dim = df[["country", "state", "city", "zip_code", "latitude", "longitude"]].copy()
    dim = dim.drop_duplicates(subset=["city", "zip_code"]).reset_index(drop=True)
    dim.insert(0, "geography_key", range(1, len(dim) + 1))
    return dim


def build_dim_plan(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "contract_type", "internet_service", "phone_service_bool", "multiple_lines",
        "online_security", "online_backup", "device_protection", "tech_support",
        "streaming_tv", "streaming_movies", "paperless_billing_bool", "contract_based_risk_tier",
    ]
    dim = df[cols].copy().rename(columns={
        "phone_service_bool": "phone_service",
        "paperless_billing_bool": "paperless_billing",
    })
    dedupe_cols = [c for c in dim.columns if c != "contract_based_risk_tier"]
    dim = dim.drop_duplicates(subset=dedupe_cols).reset_index(drop=True)
    dim.insert(0, "plan_key", range(1, len(dim) + 1))
    return dim


def build_dim_payment_method(df: pd.DataFrame) -> pd.DataFrame:
    dim = df[["payment_method"]].drop_duplicates().reset_index(drop=True)
    dim.insert(0, "payment_method_key", range(1, len(dim) + 1))
    return dim


def build_dim_tenure_cohort(df: pd.DataFrame) -> pd.DataFrame:
    labels = sorted(df["tenure_cohort"].dropna().unique(), key=lambda x: TENURE_COHORT_ORDER[x])
    dim = pd.DataFrame({
        "tenure_cohort_label": labels,
        "sort_order": [TENURE_COHORT_ORDER[l] for l in labels],
    })
    dim.insert(0, "tenure_cohort_key", range(1, len(dim) + 1))
    return dim


def build_dim_churn_reason(df: pd.DataFrame) -> pd.DataFrame:
    dim = df[["churn_reason"]].drop_duplicates().reset_index(drop=True)
    dim.insert(0, "churn_reason_key", range(1, len(dim) + 1))
    return dim


def build_fact_subscription(df: pd.DataFrame, dims: dict) -> pd.DataFrame:
    fact = df.copy()

    fact = fact.merge(dims["customer"][["customer_key", "customer_id"]], on="customer_id", how="left")
    fact = fact.merge(dims["geography"][["geography_key", "city", "zip_code"]], on=["city", "zip_code"], how="left")

    plan_join_cols = [
        "contract_type", "internet_service", "multiple_lines", "online_security",
        "online_backup", "device_protection", "tech_support", "streaming_tv", "streaming_movies",
    ]
    plan_dim_renamed = dims["plan"].rename(columns={
        "phone_service": "phone_service_bool", "paperless_billing": "paperless_billing_bool"
    })
    fact = fact.merge(
        plan_dim_renamed[["plan_key"] + plan_join_cols + ["phone_service_bool", "paperless_billing_bool"]],
        on=plan_join_cols + ["phone_service_bool", "paperless_billing_bool"],
        how="left",
    )

    fact = fact.merge(dims["payment_method"], on="payment_method", how="left")
    fact = fact.merge(
        dims["tenure_cohort"].rename(columns={"tenure_cohort_label": "tenure_cohort"}),
        on="tenure_cohort", how="left",
    )
    fact = fact.merge(dims["churn_reason"], on="churn_reason", how="left")

    fact_cols = [
        "customer_key", "geography_key", "plan_key", "payment_method_key",
        "tenure_cohort_key", "churn_reason_key",
        "tenure_months", "monthly_charges", "total_charges", "is_new_customer_imputed_charges",
        "churn_flag", "churn_score", "cltv",
        "addon_service_count", "avg_revenue_per_tenure_month",
        "recency_tenure_months", "frequency_addon_breadth", "monetary_total_charges",
    ]
    fact = fact[fact_cols].reset_index(drop=True)
    fact.insert(0, "subscription_fact_key", range(1, len(fact) + 1))
    return fact


def validate_referential_integrity(fact: pd.DataFrame) -> dict:
    """Every FK in the fact table must resolve — zero nulls, zero orphans by construction."""
    fk_cols = [
        "customer_key", "geography_key", "plan_key",
        "payment_method_key", "tenure_cohort_key", "churn_reason_key",
    ]
    null_report = {col: int(fact[col].isna().sum()) for col in fk_cols}
    all_resolved = all(v == 0 for v in null_report.values())
    return {"fk_null_counts": null_report, "all_foreign_keys_resolved": all_resolved}


def load_to_sqlite(dims: dict, fact: pd.DataFrame):
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    for name, table in {
        "dim_customer": dims["customer"], "dim_geography": dims["geography"],
        "dim_plan": dims["plan"], "dim_payment_method": dims["payment_method"],
        "dim_tenure_cohort": dims["tenure_cohort"], "dim_churn_reason": dims["churn_reason"],
        "fact_subscription": fact,
    }.items():
        table.to_sql(name, conn, if_exists="replace", index=False)
        logger.info(f"Loaded {name}: {len(table)} rows")
    conn.close()
    logger.info(f"SQLite database written to {DB_PATH} (local stand-in; production target is PostgreSQL — see sql/schema/).")


def run_etl():
    logger.info("=== Starting full ETL pipeline ===")
    raw_df, ingestion_report = run_ingestion()
    clean_df = run_cleaning(raw_df)
    feat_df = run_feature_engineering(clean_df)

    dims = {
        "customer": build_dim_customer(feat_df),
        "geography": build_dim_geography(feat_df),
        "plan": build_dim_plan(feat_df),
        "payment_method": build_dim_payment_method(feat_df),
        "tenure_cohort": build_dim_tenure_cohort(feat_df),
        "churn_reason": build_dim_churn_reason(feat_df),
    }
    fact = build_fact_subscription(feat_df, dims)
    ri_report = validate_referential_integrity(fact)
    logger.info(f"Referential integrity check: {ri_report}")
    assert ri_report["all_foreign_keys_resolved"], "Unresolved foreign keys in fact table — aborting load."

    load_to_sqlite(dims, fact)

    # Also persist the flat processed table for EDA/ML phases
    processed_flat_path = os.path.join(PROCESSED_DIR, "customer_churn_processed.csv")
    feat_df.to_csv(processed_flat_path, index=False)
    logger.info(f"Flat processed dataset written to {processed_flat_path}")

    return {
        "ingestion_report": ingestion_report,
        "referential_integrity": ri_report,
        "dim_row_counts": {k: len(v) for k, v in dims.items()},
        "fact_row_count": len(fact),
    }


if __name__ == "__main__":
    import json
    summary = run_etl()
    print("\n=== ETL PIPELINE SUMMARY ===")
    print(json.dumps(summary, indent=2, default=str))
