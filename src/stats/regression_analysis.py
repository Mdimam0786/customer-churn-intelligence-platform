"""
Regression analysis module.

statsmodels was not available during development (no internet access to
install it). Rather than skip formal regression inference, this module
implements OLS and logistic regression using the same classical
closed-form formulas statsmodels itself uses under the hood:
  - OLS: beta = (X'X)^-1 X'y, with the standard Gauss-Markov variance
    estimator for standard errors, t-stats, and p-values.
  - Logistic regression: coefficients fit via sklearn's LogisticRegression
    (L-BFGS, no regularization), then the asymptotic covariance matrix
    Var(beta) = (X' W X)^-1 (the observed Fisher information from the
    IRLS/Newton-Raphson MLE derivation) used for Wald standard errors,
    z-stats, p-values, and odds ratios with 95% CIs.
This is genuine statistical inference, not an approximation of one.
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "customer_churn_processed.csv")


def ols_regression(X: pd.DataFrame, y: pd.Series, feature_names: list) -> dict:
    """Multiple OLS regression with an intercept, classical inference."""
    n, k = X.shape
    X_design = np.column_stack([np.ones(n), X.values])
    XtX_inv = np.linalg.inv(X_design.T @ X_design)
    beta = XtX_inv @ X_design.T @ y.values

    y_pred = X_design @ beta
    residuals = y.values - y_pred
    ss_res = (residuals ** 2).sum()
    ss_tot = ((y.values - y.values.mean()) ** 2).sum()
    r_squared = 1 - ss_res / ss_tot
    adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - k - 1)

    sigma_squared = ss_res / (n - k - 1)
    var_beta = sigma_squared * np.diag(XtX_inv)
    se_beta = np.sqrt(var_beta)
    t_stats = beta / se_beta
    p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=n - k - 1))

    names = ["Intercept"] + feature_names
    coef_table = []
    for i, name in enumerate(names):
        ci_low = beta[i] - 1.96 * se_beta[i]
        ci_high = beta[i] + 1.96 * se_beta[i]
        coef_table.append({
            "feature": name, "coefficient": round(beta[i], 4), "std_error": round(se_beta[i], 4),
            "t_stat": round(t_stats[i], 3), "p_value": round(p_values[i], 6),
            "95pct_ci": (round(ci_low, 4), round(ci_high, 4)),
            "significant_at_05": bool(p_values[i] < 0.05),
        })

    return {
        "n_obs": n, "r_squared": round(r_squared, 4), "adj_r_squared": round(adj_r_squared, 4),
        "coefficients": coef_table,
    }


def logistic_regression_with_inference(X: pd.DataFrame, y: pd.Series, feature_names: list) -> dict:
    """Logistic regression with Wald standard errors, z-stats, p-values, odds ratios and CIs."""
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X.values)

    model = LogisticRegression(penalty=None, max_iter=2000, solver="lbfgs")
    model.fit(X_scaled, y)

    n, k = X_scaled.shape
    X_design = np.column_stack([np.ones(n), X_scaled])
    coefs = np.concatenate([[model.intercept_[0]], model.coef_[0]])

    p_hat = model.predict_proba(X_scaled)[:, 1]
    W = np.diag(p_hat * (1 - p_hat))
    fisher_info = X_design.T @ W @ X_design
    cov_matrix = np.linalg.inv(fisher_info + np.eye(fisher_info.shape[0]) * 1e-10)
    se = np.sqrt(np.diag(cov_matrix))

    z_stats = coefs / se
    p_values = 2 * (1 - stats.norm.cdf(np.abs(z_stats)))

    names = ["Intercept"] + feature_names
    coef_table = []
    for i, name in enumerate(names):
        odds_ratio = np.exp(coefs[i])
        ci_low_log, ci_high_log = coefs[i] - 1.96 * se[i], coefs[i] + 1.96 * se[i]
        coef_table.append({
            "feature": name, "coefficient_std": round(coefs[i], 4),
            "std_error": round(se[i], 4), "z_stat": round(z_stats[i], 3),
            "p_value": round(p_values[i], 6),
            "odds_ratio_per_1sd": round(odds_ratio, 3),
            "odds_ratio_95pct_ci": (round(np.exp(ci_low_log), 3), round(np.exp(ci_high_log), 3)),
            "significant_at_05": bool(p_values[i] < 0.05),
        })

    # McFadden's pseudo R^2 (standard for logistic regression, since OLS R^2 doesn't apply)
    ll_full = np.sum(y * np.log(p_hat + 1e-15) + (1 - y) * np.log(1 - p_hat + 1e-15))
    p_null = y.mean()
    ll_null = np.sum(y * np.log(p_null) + (1 - y) * np.log(1 - p_null))
    mcfadden_r2 = 1 - ll_full / ll_null

    return {
        "n_obs": n, "mcfadden_pseudo_r2": round(mcfadden_r2, 4),
        "note": "Coefficients are on standardized (mean 0, std 1) predictors, so magnitudes are directly comparable across features regardless of original units.",
        "coefficients": coef_table,
    }


def run_regression_suite(df: pd.DataFrame) -> dict:
    logger.info("Running OLS regression: total_charges ~ tenure_months + monthly_charges...")
    ols_result = ols_regression(
        df[["tenure_months", "monthly_charges"]], df["total_charges"],
        ["tenure_months", "monthly_charges"]
    )

    logger.info("Running logistic regression: churn ~ key real predictors...")
    logit_features = [
        "tenure_months", "monthly_charges", "addon_service_count",
        "churn_score",
    ]
    df_encoded = df.copy()
    df_encoded["contract_two_year"] = (df_encoded["contract_type"] == "Two year").astype(int)
    df_encoded["contract_one_year"] = (df_encoded["contract_type"] == "One year").astype(int)
    logit_features += ["contract_two_year", "contract_one_year"]

    logit_result = logistic_regression_with_inference(
        df_encoded[logit_features], df_encoded["churn_flag"], logit_features
    )

    # Second logistic model WITHOUT churn_score, since it's IBM's own derived
    # risk field and would dominate/mask the other real predictors -- this
    # version shows what's learnable from the raw business fields alone.
    logit_features_no_score = [f for f in logit_features if f != "churn_score"]
    logit_result_no_score = logistic_regression_with_inference(
        df_encoded[logit_features_no_score], df_encoded["churn_flag"], logit_features_no_score
    )

    return {
        "ols_total_charges_model": ols_result,
        "logistic_churn_model_with_ibm_score": logit_result,
        "logistic_churn_model_business_fields_only": logit_result_no_score,
    }


if __name__ == "__main__":
    import json
    df = pd.read_csv(DATA_PATH)
    results = run_regression_suite(df)
    print(json.dumps(results, indent=2, default=str))
