"""
Explainability module.

The `shap` library was not available during development. This module
does not try to reproduce SHAP's results — instead it uses two
genuine, well-established, model-agnostic techniques that do the same
job in a different way:

1. Permutation importance (via scikit-learn) — a global explainability
   method that measures how much model performance drops when a
   feature's values are randomly shuffled. This works with any model
   and holds up well even when features are correlated with each other.

2. Local marginal-contribution explanation — for a single prediction,
   this measures how much the model's predicted probability changes
   when each feature is individually reset to the population's average
   or most common value. This is a simpler, "leave-one-feature-out"
   effect. It's not the same as a Shapley value (which SHAP calculates
   by averaging over every possible combination of features), but it
   does), and is labeled as such throughout rather than presented as
   equivalent to SHAP.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.utils.logger import get_logger
from src.ml.churn_model import (
    load_data, run_full_churn_pipeline, NUMERIC_FEATURES, CATEGORICAL_FEATURES
)

logger = get_logger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")


def compute_permutation_importance(model, X_test, y_test, n_repeats=10):
    logger.info(f"Computing permutation importance ({n_repeats} repeats)...")
    result = permutation_importance(
        model, X_test, y_test, n_repeats=n_repeats, random_state=42, scoring="roc_auc", n_jobs=-1
    )
    importances = []
    for i, feature in enumerate(X_test.columns):
        importances.append({
            "feature": feature,
            "importance_mean": round(float(result.importances_mean[i]), 5),
            "importance_std": round(float(result.importances_std[i]), 5),
        })
    importances.sort(key=lambda x: x["importance_mean"], reverse=True)
    return importances


def local_marginal_explanation(model, X_test, customer_idx, X_train_reference):
    """
    For one specific real customer, shows how much the predicted churn
    probability shifts when each feature is individually replaced with
    the training population's typical value (mean for numeric, mode for
    categorical) -- clearly labeled as an approximation, not a SHAP value.
    """
    customer_row = X_test.iloc[[customer_idx]].copy()
    baseline_proba = model.predict_proba(customer_row)[0, 1]

    contributions = []
    for feature in NUMERIC_FEATURES + CATEGORICAL_FEATURES:
        modified_row = customer_row.copy()
        if feature in NUMERIC_FEATURES:
            modified_row[feature] = X_train_reference[feature].mean()
        else:
            modified_row[feature] = X_train_reference[feature].mode()[0]
        modified_proba = model.predict_proba(modified_row)[0, 1]
        contributions.append({
            "feature": feature,
            "customer_value": customer_row[feature].values[0],
            "typical_value": modified_row[feature].values[0],
            "probability_shift_if_typical": round(float(modified_proba - baseline_proba), 4),
        })
    contributions.sort(key=lambda x: abs(x["probability_shift_if_typical"]), reverse=True)

    return {
        "predicted_churn_probability": round(float(baseline_proba), 4),
        "feature_contributions_vs_typical_customer": contributions,
    }


def run_explainability_suite():
    summary, model, X_test, y_test = run_full_churn_pipeline()
    _, X_full, _ = load_data()

    perm_importance = compute_permutation_importance(model, X_test, y_test)

    # Local explanations for 3 real customers: one clearly high-risk, one
    # clearly low-risk, one borderline -- picked from actual test-set predictions
    y_proba = model.predict_proba(X_test)[:, 1]
    high_risk_idx = int(np.argmax(y_proba))
    low_risk_idx = int(np.argmin(y_proba))
    borderline_idx = int(np.argmin(np.abs(y_proba - 0.5)))

    local_explanations = {
        "highest_predicted_risk_customer": local_marginal_explanation(model, X_test, high_risk_idx, X_full),
        "lowest_predicted_risk_customer": local_marginal_explanation(model, X_test, low_risk_idx, X_full),
        "borderline_customer": local_marginal_explanation(model, X_test, borderline_idx, X_full),
    }

    results = {
        "permutation_importance": perm_importance,
        "local_explanations": local_explanations,
        "methodology_note": (
            "The shap library was not available during development. "
            "Permutation importance (global) and leave-one-feature-out marginal "
            "contribution (local) are used instead -- genuine, standard, "
            "model-agnostic techniques, not the same as Shapley values."
        ),
    }

    with open(os.path.join(DOCS_DIR, "explainability_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info("Explainability results written to docs/explainability_results.json")

    return results


if __name__ == "__main__":
    results = run_explainability_suite()
    print("\n=== TOP 10 PERMUTATION IMPORTANCE ===")
    for f in results["permutation_importance"][:10]:
        print(f)
    print("\n=== HIGHEST RISK CUSTOMER EXPLANATION ===")
    print(f"Predicted probability: {results['local_explanations']['highest_predicted_risk_customer']['predicted_churn_probability']}")
    for c in results["local_explanations"]["highest_predicted_risk_customer"]["feature_contributions_vs_typical_customer"][:5]:
        print(c)
