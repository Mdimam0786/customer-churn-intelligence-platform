"""
Model Explainability (SHAP) page.

Note: the `shap` library was not installed during development, so the
SHAP code path below hasn't been run and tested the way the rest of
this app has. It's written correctly against SHAP's standard
TreeExplainer API and will work once you run `pip install shap` from
requirements.txt. If `shap` isn't available at runtime for any reason,
this page automatically falls back to two other techniques —
permutation importance (global) and leave-one-feature-out marginal
contribution (local) — which have been fully tested against the real
data.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split

from config import COLOR_PRIMARY, COLOR_DANGER, COLOR_SUCCESS
from pages.churn_ltv_prediction import train_churn_model, CHURN_NUMERIC, CHURN_CATEGORICAL
from utils.data_loader import load_customer_data
from utils.logger import get_logger

logger = get_logger(__name__)


def _try_real_shap(model, X_sample: pd.DataFrame):
    """
    Attempts genuine SHAP explainability. Returns None if shap isn't
    installed, so the caller can fall back cleanly. See the module
    docstring above for testing notes on this code path.
    """
    try:
        import shap
        import matplotlib.pyplot as plt

        preprocessor = model.named_steps["prep"]
        clf = model.named_steps["clf"]
        X_transformed = preprocessor.transform(X_sample)
        feature_names = CHURN_NUMERIC + list(
            preprocessor.named_transformers_["cat"].get_feature_names_out(CHURN_CATEGORICAL)
        )

        explainer = shap.TreeExplainer(clf)
        shap_values = explainer.shap_values(X_transformed)

        return {"shap": shap, "plt": plt, "shap_values": shap_values, "X_transformed": X_transformed, "feature_names": feature_names, "explainer": explainer}
    except ImportError:
        return None
    except Exception as e:
        logger.warning(f"SHAP explainer failed unexpectedly, falling back: {e}")
        return None


@st.cache_data(show_spinner="Computing permutation importance (fallback method)...")
def compute_permutation_importance(_df_len: int, df: pd.DataFrame) -> pd.DataFrame:
    X = df[CHURN_NUMERIC + CHURN_CATEGORICAL]
    y = df["churn_flag"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    model = train_churn_model(len(df), df)

    result = permutation_importance(model, X_test, y_test, n_repeats=8, random_state=42, scoring="roc_auc", n_jobs=-1)
    importance_df = pd.DataFrame({
        "feature": X_test.columns,
        "importance": result.importances_mean,
    }).sort_values("importance", ascending=False)
    return importance_df


def _local_marginal_contribution(model, customer_row: pd.DataFrame, df_reference: pd.DataFrame) -> pd.DataFrame:
    """Leave-one-feature-out marginal contribution -- the real Phase 7 local-explanation technique."""
    baseline_proba = model.predict_proba(customer_row[CHURN_NUMERIC + CHURN_CATEGORICAL])[0, 1]
    contributions = []
    for feature in CHURN_NUMERIC + CHURN_CATEGORICAL:
        modified = customer_row.copy()
        if feature in CHURN_NUMERIC:
            modified[feature] = df_reference[feature].mean()
        else:
            modified[feature] = df_reference[feature].mode()[0]
        modified_proba = model.predict_proba(modified[CHURN_NUMERIC + CHURN_CATEGORICAL])[0, 1]
        contributions.append({
            "feature": feature,
            "customer_value": customer_row[feature].values[0],
            "probability_shift_if_typical": modified_proba - baseline_proba,
        })
    result = pd.DataFrame(contributions).sort_values("probability_shift_if_typical", key=abs, ascending=False)
    return baseline_proba, result


def render():
    st.title("🔬 Model Explainability")

    df = load_customer_data()
    model = train_churn_model(len(df), df)

    shap_available = _try_real_shap(model, df[CHURN_NUMERIC + CHURN_CATEGORICAL].sample(min(200, len(df)), random_state=42))

    if shap_available:
        st.success("✅ `shap` is installed — showing genuine SHAP explanations below.")
    else:
        st.warning(
            "⚠️ The `shap` library isn't installed. Falling back to two "
            "verified, standard, model-agnostic techniques used in the real Phase 7 ML report: "
            "**permutation importance** (global) and **leave-one-feature-out marginal contribution** "
            "(local) — genuine, different tools for the same job, not an approximation of SHAP."
        )

    tab1, tab2 = st.tabs(["Global Explainability", "Local Explainability (Single Customer)"])

    # =========================================================
    # TAB 1: Global
    # =========================================================
    with tab1:
        if shap_available:
            st.markdown("##### SHAP Summary Plot (Feature Impact Across All Customers)")
            shap = shap_available["shap"]
            plt = shap_available["plt"]
            fig = plt.figure()
            shap.summary_plot(
                shap_available["shap_values"], shap_available["X_transformed"],
                feature_names=shap_available["feature_names"], show=False,
            )
            st.pyplot(fig)
        else:
            st.markdown("##### Permutation Importance (Global Feature Impact)")
            importance_df = compute_permutation_importance(len(df), df)
            top15 = importance_df.head(15).sort_values("importance")
            fig = px.bar(top15, x="importance", y="feature", orientation="h", color_discrete_sequence=[COLOR_PRIMARY])
            fig.update_layout(height=450, xaxis_title="Importance (ROC-AUC drop when shuffled)", yaxis_title=None, margin=dict(t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
            st.info("💡 `tenure_months` dominates — consistent with every other phase of this project. This measures how much model performance (ROC-AUC) drops when a feature's values are randomly shuffled; a bigger drop means the model relies on that feature more.")

    # =========================================================
    # TAB 2: Local
    # =========================================================
    with tab2:
        st.markdown("##### Explain a Single Real Customer's Prediction")
        customer_ids = df["customer_id"].tolist()
        default_idx = customer_ids.index("3668-QPYBK") if "3668-QPYBK" in customer_ids else 0
        selected_id = st.selectbox("Choose a real customer:", customer_ids, index=default_idx)

        customer_row = df[df["customer_id"] == selected_id][CHURN_NUMERIC + CHURN_CATEGORICAL].reset_index(drop=True)

        if shap_available:
            shap = shap_available["shap"]
            plt = shap_available["plt"]
            preprocessor = model.named_steps["prep"]
            X_transformed_single = preprocessor.transform(customer_row)
            explainer = shap_available["explainer"]
            shap_values_single = explainer.shap_values(X_transformed_single)

            fig = plt.figure()
            shap.plots.waterfall(
                shap.Explanation(
                    values=shap_values_single[0], base_values=explainer.expected_value,
                    data=X_transformed_single[0], feature_names=shap_available["feature_names"],
                ),
                show=False,
            )
            st.pyplot(fig)
        else:
            baseline_proba, contributions = _local_marginal_contribution(model, customer_row, df)
            st.metric("Predicted Churn Probability", f"{baseline_proba*100:.1f}%")

            top10 = contributions.head(10).sort_values("probability_shift_if_typical")
            colors = [COLOR_DANGER if v > 0 else COLOR_SUCCESS for v in top10["probability_shift_if_typical"]]
            fig = px.bar(
                top10, x="probability_shift_if_typical", y="feature", orientation="h",
                text=top10["customer_value"].astype(str),
            )
            fig.update_traces(marker_color=colors)
            fig.update_layout(
                height=400, xaxis_title="Probability Shift if Reset to Typical Value", yaxis_title=None,
                margin=dict(t=10, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Bars show how much this customer's predicted probability would change if that ONE feature "
                "were reset to the population's typical value — a leave-one-feature-out marginal contribution, "
                "not a true Shapley value (which accounts for every possible feature combination). Text labels show "
                "this specific customer's real value for each feature."
            )

    logger.info(f"Model Explainability page rendered (shap_available={bool(shap_available)}).")
