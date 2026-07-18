"""
Upsell recommendation module.

This dataset has no real transaction/purchase-event log, so a genuine
market-basket ("customers who bought X also bought Y") recommender
isn't possible without fabricating interaction data. Instead, this
module builds a real, defensible substitute: for each of the 6 real
add-on services, a binary classifier predicts P(customer currently has
this service | their other real attributes) using customers who DON'T
have that service as the prediction population. For an active,
non-adopting customer, a high predicted probability means "customers
who look like this one usually have this service" -- a legitimate,
data-grounded signal for which specific add-on to offer them next.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "customer_churn_processed.csv")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")

ADDON_SERVICES = [
    "online_security", "online_backup", "device_protection",
    "tech_support", "streaming_tv", "streaming_movies",
]

BASE_FEATURES_NUMERIC = ["tenure_months", "monthly_charges", "addon_service_count"]
BASE_FEATURES_CATEGORICAL = ["contract_type", "internet_service", "has_dependents", "senior_citizen"]


def build_preprocessor():
    return ColumnTransformer([
        ("num", StandardScaler(), BASE_FEATURES_NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), BASE_FEATURES_CATEGORICAL),
    ])


def train_addon_model(df, target_service):
    """
    Trains a model to predict whether a customer has `target_service`,
    using only customers where the service is technically APPLICABLE
    (i.e. excludes 'No internet service' rows for internet-dependent
    add-ons, since those customers were never eligible in the first place).
    """
    applicable = df[df[target_service] != "No internet service"].copy()
    applicable["target"] = (applicable[target_service] == "Yes").astype(int)

    # Exclude addon_service_count from features here since it's partly
    # derived from the target itself -- would leak information.
    numeric_feats = [f for f in BASE_FEATURES_NUMERIC if f != "addon_service_count"]
    X = applicable[numeric_feats + BASE_FEATURES_CATEGORICAL]
    y = applicable["target"]

    pipe = Pipeline([
        ("prep", ColumnTransformer([
            ("num", StandardScaler(), numeric_feats),
            ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), BASE_FEATURES_CATEGORICAL),
        ])),
        ("clf", RandomForestClassifier(n_estimators=150, max_depth=6, class_weight="balanced", random_state=42)),
    ])

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(pipe, X, y, cv=cv, scoring="roc_auc", n_jobs=-1)

    pipe.fit(X, y)

    return {
        "service": target_service,
        "n_eligible_customers": len(applicable),
        "current_adoption_rate_pct": round(100 * y.mean(), 2),
        "cv_roc_auc_mean": round(cv_scores.mean(), 4),
        "cv_roc_auc_std": round(cv_scores.std(), 4),
    }, pipe, numeric_feats


def generate_recommendations(df, models_and_feats):
    """
    For each real customer who does NOT already have a given service (and
    is eligible for it), score their probability of being a 'natural fit'
    -- i.e. what the model would predict for a similar customer who does
    have it. Returns the top opportunity per customer (highest-probability
    service they don't yet have).
    """
    all_recommendations = []
    for service, (metrics, pipe, numeric_feats) in models_and_feats.items():
        non_adopters = df[(df[service] == "No") & (df[service] != "No internet service")].copy()
        if len(non_adopters) == 0:
            continue
        X_candidates = non_adopters[numeric_feats + BASE_FEATURES_CATEGORICAL]
        probas = pipe.predict_proba(X_candidates)[:, 1]
        for cid, p in zip(non_adopters["customer_id"], probas):
            all_recommendations.append({"customer_id": cid, "recommended_service": service, "fit_probability": round(float(p), 4)})

    rec_df = pd.DataFrame(all_recommendations)
    top_per_customer = rec_df.sort_values("fit_probability", ascending=False).groupby("customer_id").first().reset_index()
    return top_per_customer


def run_upsell_pipeline():
    df = pd.read_csv(DATA_PATH)
    logger.info(f"Training per-service upsell models on {len(df)} real customers...")

    models_and_feats = {}
    service_metrics = []
    for service in ADDON_SERVICES:
        metrics, pipe, numeric_feats = train_addon_model(df, service)
        service_metrics.append(metrics)
        models_and_feats[service] = (metrics, pipe, numeric_feats)
        logger.info(f"{service}: CV ROC-AUC={metrics['cv_roc_auc_mean']}, adoption={metrics['current_adoption_rate_pct']}%")

    recommendations = generate_recommendations(df, models_and_feats)

    rec_summary = recommendations["recommended_service"].value_counts().to_dict()
    top_10_highest_confidence = recommendations.sort_values("fit_probability", ascending=False).head(10).to_dict(orient="records")

    results = {
        "methodology_note": (
            "No real transaction/purchase log exists in this dataset, so a "
            "collaborative-filtering recommender isn't possible without "
            "fabricating interaction data. Instead, per-service classifiers "
            "predict which non-adopting customers most resemble current "
            "adopters -- a real, defensible upsell-targeting signal."
        ),
        "per_service_model_metrics": service_metrics,
        "total_customers_with_a_recommendation": len(recommendations),
        "recommended_service_distribution": rec_summary,
        "top_10_highest_confidence_recommendations": top_10_highest_confidence,
    }

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, "upsell_recommendation_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info("Upsell recommendation results written to docs/upsell_recommendation_results.json")

    return results


if __name__ == "__main__":
    results = run_upsell_pipeline()
    print(json.dumps({k: v for k, v in results.items() if k != "top_10_highest_confidence_recommendations"}, indent=2, default=str))
    print("\nTop 10 highest-confidence recommendations:")
    for r in results["top_10_highest_confidence_recommendations"]:
        print(r)
