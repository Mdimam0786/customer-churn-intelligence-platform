"""
PostgreSQL loader.

This is the REAL production loader this project has targeted since
the data pipeline design (see docs/technical_design_document.md Section 2.2) -- until
now it only had a SQLite stand-in because no live Postgres server was
available while developing this project. This script:

  1. Reads real connection details from your local .env file (never
     hardcoded, never committed to git).
  2. Executes the real DDL files in sql/schema/ against your database.
  3. Loads the same cleaned/feature-engineered data used everywhere
     else in this project into real Postgres tables.

Run with: python3 -m src.data_engineering.load_to_postgres
"""

import os
import sys

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.utils.logger import get_logger
from src.data_engineering.ingest import run_ingestion
from src.data_engineering.clean import run_cleaning
from src.data_engineering.feature_engineering import run_feature_engineering
from src.data_engineering.etl_pipeline import (
    build_dim_customer, build_dim_geography, build_dim_plan,
    build_dim_payment_method, build_dim_tenure_cohort, build_dim_churn_reason,
    build_fact_subscription, validate_referential_integrity,
)

logger = get_logger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SQL_SCHEMA_DIR = os.path.join(PROJECT_ROOT, "sql", "schema")


def get_engine():
    """
    Builds a SQLAlchemy engine from DATABASE_URL in your local .env file.
    Loads .env via python-dotenv so the real password is never printed,
    logged, or hardcoded anywhere in this file.
    """
    load_dotenv()  # reads .env in the project root, if present
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise EnvironmentError(
            "DATABASE_URL not found. Copy .env.example to .env and fill in your "
            "real local PostgreSQL connection string first -- see the setup guide."
        )
    return create_engine(database_url)


def run_schema_files(engine):
    """Executes the real DDL files, in order, against your real Postgres database."""
    schema_files = ["01_dimensions.sql", "02_fact.sql", "03_indexes_optimization.sql"]
    with engine.connect() as conn:
        for filename in schema_files:
            path = os.path.join(SQL_SCHEMA_DIR, filename)
            if not os.path.exists(path):
                logger.warning(f"Schema file not found, skipping: {path}")
                continue
            with open(path, "r") as f:
                sql_text = f.read()
            logger.info(f"Executing {filename} against your PostgreSQL database...")
            # Split on semicolons naively is unsafe for complex SQL; psycopg2/SQLAlchemy
            # can execute a full multi-statement script via a raw connection instead.
            raw_conn = conn.connection
            with raw_conn.cursor() as cur:
                cur.execute(sql_text)
            raw_conn.commit()
    logger.info("All schema files executed successfully.")


def load_dataframe(engine, df: pd.DataFrame, table_name: str):
    df.to_sql(table_name, engine, if_exists="append", index=False, method="multi", chunksize=500)
    logger.info(f"Loaded {len(df)} rows into real PostgreSQL table '{table_name}'.")


def run_full_postgres_load():
    logger.info("=== Starting REAL PostgreSQL load ===")
    engine = get_engine()

    logger.info("Running schema DDL against your database (safe to re-run — uses IF NOT EXISTS)...")
    run_schema_files(engine)

    logger.info("Re-running the same real ETL logic used throughout this project...")
    raw_df, _ = run_ingestion()
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
    assert ri_report["all_foreign_keys_resolved"], "Unresolved foreign keys — aborting Postgres load."
    logger.info(f"Referential integrity check passed: {ri_report}")

    # Truncate first so this script is safely re-runnable without duplicating rows
    with engine.connect() as conn:
        for table in ["fact_subscription", "dim_customer", "dim_geography", "dim_plan",
                      "dim_payment_method", "dim_tenure_cohort", "dim_churn_reason"]:
            conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
        conn.commit()

    load_dataframe(engine, dims["customer"], "dim_customer")
    load_dataframe(engine, dims["geography"], "dim_geography")
    load_dataframe(engine, dims["plan"], "dim_plan")
    load_dataframe(engine, dims["payment_method"], "dim_payment_method")
    load_dataframe(engine, dims["tenure_cohort"], "dim_tenure_cohort")
    load_dataframe(engine, dims["churn_reason"], "dim_churn_reason")
    load_dataframe(engine, fact, "fact_subscription")

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) AS total_customers,
                   ROUND(100.0 * SUM(churn_flag) / COUNT(*), 2) AS churn_rate_pct
            FROM fact_subscription;
        """))
        row = result.fetchone()
        logger.info(f"VERIFICATION QUERY against your real Postgres database: "
                    f"total_customers={row[0]}, churn_rate_pct={row[1]}")

    logger.info("=== Real PostgreSQL load complete ===")


if __name__ == "__main__":
    run_full_postgres_load()
