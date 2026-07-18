"""
Churn prediction module.

Note on libraries: XGBoost and LightGBM were not available during
development, so scikit-learn's GradientBoostingClassifier is used as
the gradient-boosting model instead. It's a genuine, different
gradient-boosting implementation (not a stand-in), just without
XGBoost's specific speed optimizations. Logistic Regression and Random
Forest are included alongside it for a proper 3-model comparison.

IMPORTANT: the IBM-provided `churn_score` and `cltv` fields are left
OUT of the model's features on purpose. Including them would let the
model simply copy IBM's own existing answer instead of learning from
the real, independent business data — the goal here is a model that's
genuinely useful for a NEW customer who doesn't have an IBM-provided
score yet.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate, GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    roc_auc_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_curve, classification_report
)

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "customer_churn_processed.csv")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")

NUMERIC_FEATURES = ["tenure_months", "monthly_charges", "total_charges", "addon_service_count"]
CATEGORICAL_FEATURES = [
    "contract_type", "internet_service", "payment_method", "gender",
    "senior_citizen", "has_partner", "has_dependents", "paperless_billing",
    "multiple_lines", "online_security", "online_backup", "device_protection",
    "tech_support", "streaming_tv", "streaming_movies",
]


def build_preprocessor():
    return ColumnTransformer([
        ("num", StandardScaler(), NUMERIC_FEATURES),
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="first"), CATEGORICAL_FEATURES),
    ])


def load_data():
    df = pd.read_csv(DATA_PATH)
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()
    y = df["churn_flag"].copy()
    return df, X, y


def cross_validate_models(X, y):
    """5-fold stratified CV comparison of 3 models -- the actual 'model comparison' deliverable."""
    logger.info("Running 5-fold stratified cross-validation across 3 candidate models...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scoring = ["roc_auc", "precision", "recall", "f1"]

    models = {
        "Logistic Regression": Pipeline([
            ("prep", build_preprocessor()),
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced")),
        ]),
        "Random Forest": Pipeline([
            ("prep", build_preprocessor()),
            ("clf", RandomForestClassifier(n_estimators=200, max_depth=8, class_weight="balanced", random_state=42)),
        ]),
        "Gradient Boosting": Pipeline([
            ("prep", build_preprocessor()),
            ("clf", GradientBoostingClassifier(n_estimators=150, max_depth=3, learning_rate=0.1, random_state=42)),
        ]),
    }

    results = {}
    for name, pipe in models.items():
        cv_results = cross_validate(pipe, X, y, cv=cv, scoring=scoring, n_jobs=-1)
        results[name] = {
            "roc_auc_mean": round(cv_results["test_roc_auc"].mean(), 4),
            "roc_auc_std": round(cv_results["test_roc_auc"].std(), 4),
            "precision_mean": round(cv_results["test_precision"].mean(), 4),
            "recall_mean": round(cv_results["test_recall"].mean(), 4),
            "f1_mean": round(cv_results["test_f1"].mean(), 4),
        }
        logger.info(f"{name}: ROC-AUC={results[name]['roc_auc_mean']} (+/-{results[name]['roc_auc_std']})")

    return results


def tune_best_model(X_train, y_train):
    """Hyperparameter tuning via GridSearchCV on Gradient Boosting (the CV winner)."""
    logger.info("Running GridSearchCV hyperparameter tuning on Gradient Boosting...")
    pipe = Pipeline([
        ("prep", build_preprocessor()),
        ("clf", GradientBoostingClassifier(random_state=42)),
    ])
    param_grid = {
        "clf__n_estimators": [100, 150, 200],
        "clf__max_depth": [2, 3, 4],
        "clf__learning_rate": [0.05, 0.1, 0.2],
    }
    grid = GridSearchCV(pipe, param_grid, cv=3, scoring="roc_auc", n_jobs=-1)
    grid.fit(X_train, y_train)
    logger.info(f"Best params: {grid.best_params_}, Best CV ROC-AUC: {round(grid.best_score_, 4)}")
    return grid.best_estimator_, grid.best_params_, grid.best_score_


def business_cost_threshold_analysis(y_test, y_proba, cost_fn=200, cost_fp=30):
    """
    Find the probability threshold that minimizes real business cost, using
    an assumed cost matrix: missing a churner (false negative) costs the
    average customer's lost monthly revenue over a retention window (~$200
    assumed placeholder, should be replaced with the company's real figure);
    a wasted retention offer to a customer who wouldn't have churned (false
    positive) costs a smaller assumed outreach/discount cost (~$30). These
    are ILLUSTRATIVE placeholder costs -- swap in real unit economics before
    using this in production.
    """
    thresholds = np.arange(0.1, 0.9, 0.02)
    costs = []
    for t in thresholds:
        preds = (y_proba >= t).astype(int)
        fn = ((preds == 0) & (y_test == 1)).sum()
        fp = ((preds == 1) & (y_test == 0)).sum()
        total_cost = fn * cost_fn + fp * cost_fp
        costs.append(total_cost)
    best_idx = np.argmin(costs)
    return {
        "assumed_cost_per_false_negative": cost_fn,
        "assumed_cost_per_false_positive": cost_fp,
        "optimal_threshold": round(float(thresholds[best_idx]), 2),
        "min_total_cost": int(costs[best_idx]),
        "cost_at_default_threshold_0.5": int(costs[np.argmin(np.abs(thresholds - 0.5))]),
    }


def evaluate_final_model(model, X_test, y_test):
    y_proba = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)

    roc_auc = roc_auc_score(y_test, y_proba)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)
    fpr, tpr, _ = roc_curve(y_test, y_proba)

    cost_analysis = business_cost_threshold_analysis(y_test.values, y_proba)

    return {
        "roc_auc": round(roc_auc, 4), "precision": round(precision, 4),
        "recall": round(recall, 4), "f1": round(f1, 4),
        "confusion_matrix": cm.tolist(),
        "classification_report": classification_report(y_test, y_pred, output_dict=True),
        "cost_threshold_analysis": cost_analysis,
        "roc_curve": {"fpr": fpr.tolist(), "tpr": tpr.tolist()},
    }


def get_feature_importance(model, feature_names_out):
    clf = model.named_steps["clf"]
    importances = clf.feature_importances_
    idx = np.argsort(importances)[::-1]
    return [
        {"feature": feature_names_out[i], "importance": round(float(importances[i]), 4)}
        for i in idx
    ]


def run_full_churn_pipeline():
    df, X, y = load_data()
    logger.info(f"Loaded {len(df)} real customers for churn modeling. Churn rate: {y.mean():.4f}")

    cv_comparison = cross_validate_models(X, y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    best_model, best_params, best_cv_score = tune_best_model(X_train, y_train)
    eval_results = evaluate_final_model(best_model, X_test, y_test)

    preprocessor = best_model.named_steps["prep"]
    cat_encoder = preprocessor.named_transformers_["cat"]
    feature_names_out = NUMERIC_FEATURES + list(cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES))
    feature_importance = get_feature_importance(best_model, feature_names_out)

    summary = {
        "n_customers": len(df),
        "churn_rate": round(y.mean(), 4),
        "features_used": NUMERIC_FEATURES + CATEGORICAL_FEATURES,
        "excluded_fields_note": "churn_score and cltv (IBM-provided) deliberately excluded -- model must work for new customers without a vendor score.",
        "cv_model_comparison": cv_comparison,
        "best_model": "Gradient Boosting (tuned)",
        "best_hyperparameters": best_params,
        "best_cv_roc_auc": round(best_cv_score, 4),
        "test_set_evaluation": eval_results,
        "feature_importance": feature_importance,
    }

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, "churn_model_results.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)
    logger.info("Churn model results written to docs/churn_model_results.json")

    return summary, best_model, X_test, y_test


if __name__ == "__main__":
    summary, model, X_test, y_test = run_full_churn_pipeline()
    print(json.dumps({k: v for k, v in summary.items() if k != "test_set_evaluation"}, indent=2, default=str))
    print("\nTest ROC-AUC:", summary["test_set_evaluation"]["roc_auc"])
    print("Test Precision:", summary["test_set_evaluation"]["precision"])
    print("Test Recall:", summary["test_set_evaluation"]["recall"])
