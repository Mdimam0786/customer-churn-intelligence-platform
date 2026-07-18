"""
LTV (CLTV) prediction module.

Predicts IBM's real, provided CLTV field from independently observable
business features (tenure, billing, contract, services) -- letting a
company estimate the expected lifetime value of a NEW customer who
doesn't have a vendor-assigned CLTV yet. Uses a Random Forest Regressor
with cross-validation and a train/test evaluation.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_validate, KFold
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "customer_churn_processed.csv")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")

NUMERIC_FEATURES = ["tenure_months", "monthly_charges", "total_charges", "addon_service_count"]
CATEGORICAL_FEATURES = ["contract_type", "internet_service", "payment_method", "senior_citizen", "has_dependents"]


def build_preprocessor():
    return ColumnTransformer([
        ("num", StandardScaler(), NUMERIC_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), CATEGORICAL_FEATURES),
    ])


def run_ltv_model():
    df = pd.read_csv(DATA_PATH)
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()
    y = df["cltv"].copy()

    logger.info(f"Training LTV regression models on {len(df)} real customers. Target: IBM-provided CLTV.")

    models = {
        "Linear Regression": Pipeline([("prep", build_preprocessor()), ("reg", LinearRegression())]),
        "Random Forest": Pipeline([("prep", build_preprocessor()),
                                     ("reg", RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42))]),
        "Gradient Boosting": Pipeline([("prep", build_preprocessor()),
                                         ("reg", GradientBoostingRegressor(n_estimators=150, max_depth=3, random_state=42))]),
    }

    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    cv_comparison = {}
    for name, pipe in models.items():
        cv_results = cross_validate(pipe, X, y, cv=cv, scoring=["r2", "neg_mean_absolute_error"], n_jobs=-1)
        cv_comparison[name] = {
            "r2_mean": round(cv_results["test_r2"].mean(), 4),
            "r2_std": round(cv_results["test_r2"].std(), 4),
            "mae_mean": round(-cv_results["test_neg_mean_absolute_error"].mean(), 2),
        }
        logger.info(f"{name}: R2={cv_comparison[name]['r2_mean']}, MAE={cv_comparison[name]['mae_mean']}")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    best_pipe = models["Random Forest"]
    best_pipe.fit(X_train, y_train)
    y_pred = best_pipe.predict(X_test)

    test_metrics = {
        "r2": round(r2_score(y_test, y_pred), 4),
        "mae": round(mean_absolute_error(y_test, y_pred), 2),
        "rmse": round(np.sqrt(mean_squared_error(y_test, y_pred)), 2),
        "cltv_range_in_data": [int(y.min()), int(y.max())],
        "cltv_mean_in_data": round(y.mean(), 2),
    }

    preprocessor = best_pipe.named_steps["prep"]
    cat_encoder = preprocessor.named_transformers_["cat"]
    feature_names_out = NUMERIC_FEATURES + list(cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES))
    importances = best_pipe.named_steps["reg"].feature_importances_
    idx = np.argsort(importances)[::-1]
    feature_importance = [
        {"feature": feature_names_out[i], "importance": round(float(importances[i]), 4)} for i in idx
    ]

    results = {
        "target": "cltv (IBM-provided real field)",
        "features_used": NUMERIC_FEATURES + CATEGORICAL_FEATURES,
        "cv_model_comparison": cv_comparison,
        "best_model": "Random Forest",
        "test_set_metrics": test_metrics,
        "feature_importance": feature_importance,
    }

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, "ltv_model_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info("LTV model results written to docs/ltv_model_results.json")

    return results


if __name__ == "__main__":
    results = run_ltv_model()
    print(json.dumps(results, indent=2, default=str))
