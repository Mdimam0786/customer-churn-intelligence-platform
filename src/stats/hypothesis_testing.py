"""
Hypothesis testing module.

Extends the earlier chi-square and t-test findings with formal effect
sizes (Cramer's V, Cohen's d) and confidence intervals, since a p-value
alone doesn't tell a business stakeholder how BIG or how CERTAIN an
effect is. All computed against the real, processed customer dataset.
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy import stats

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "customer_churn_processed.csv")


def cramers_v(confusion_matrix: np.ndarray) -> float:
    """Effect size for chi-square test of independence. 0=no association, 1=perfect."""
    chi2 = stats.chi2_contingency(confusion_matrix)[0]
    n = confusion_matrix.sum()
    r, k = confusion_matrix.shape
    return np.sqrt((chi2 / n) / (min(r - 1, k - 1)))


def cohens_d(group1: pd.Series, group2: pd.Series) -> float:
    """Effect size for a two-group mean difference. 0.2=small, 0.5=medium, 0.8=large (Cohen's convention)."""
    n1, n2 = len(group1), len(group2)
    pooled_std = np.sqrt(((n1 - 1) * group1.var() + (n2 - 1) * group2.var()) / (n1 + n2 - 2))
    return (group1.mean() - group2.mean()) / pooled_std


def wilson_ci(successes: int, n: int, confidence: float = 0.95) -> tuple:
    """Wilson score confidence interval for a proportion — more accurate than the
    normal approximation at extreme proportions or smaller sample sizes."""
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    p_hat = successes / n
    denom = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denom
    margin = (z * np.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4 * n**2))) / denom
    return (round(center - margin, 4), round(center + margin, 4))


def chi_square_with_effect_size(df: pd.DataFrame, col: str) -> dict:
    ct = pd.crosstab(df[col], df["churn_label"])
    chi2, p, dof, expected = stats.chi2_contingency(ct)
    v = cramers_v(ct.values)
    effect_label = "negligible" if v < 0.1 else "small" if v < 0.2 else "medium" if v < 0.4 else "large"
    return {
        "variable": col, "chi2": round(chi2, 2), "dof": int(dof), "p_value": round(p, 8),
        "cramers_v": round(v, 4), "effect_size": effect_label,
        "significant_at_05": bool(p < 0.05),
    }


def ttest_with_effect_size_and_ci(df: pd.DataFrame, col: str) -> dict:
    churned = df.loc[df.churn_flag == 1, col].dropna()
    retained = df.loc[df.churn_flag == 0, col].dropna()
    t, p = stats.ttest_ind(churned, retained, equal_var=False)
    d = cohens_d(churned, retained)
    d_label = "negligible" if abs(d) < 0.2 else "small" if abs(d) < 0.5 else "medium" if abs(d) < 0.8 else "large"

    diff = churned.mean() - retained.mean()
    se_diff = np.sqrt(churned.var() / len(churned) + retained.var() / len(retained))
    ci_low, ci_high = diff - 1.96 * se_diff, diff + 1.96 * se_diff

    return {
        "variable": col,
        "mean_churned": round(churned.mean(), 2), "mean_retained": round(retained.mean(), 2),
        "mean_difference": round(diff, 2),
        "diff_95pct_ci": (round(ci_low, 2), round(ci_high, 2)),
        "t_stat": round(t, 3), "p_value": round(p, 8),
        "cohens_d": round(d, 3), "effect_size": d_label,
        "significant_at_05": bool(p < 0.05),
    }


def one_way_anova(df: pd.DataFrame, group_col: str, value_col: str) -> dict:
    groups = [g[value_col].dropna().values for _, g in df.groupby(group_col, observed=True)]
    f_stat, p = stats.f_oneway(*groups)

    grand_mean = df[value_col].mean()
    ss_between = sum(len(g) * (g.mean() - grand_mean) ** 2 for g in groups)
    ss_total = ((df[value_col] - grand_mean) ** 2).sum()
    eta_squared = ss_between / ss_total  # effect size for ANOVA

    return {
        "group_variable": group_col, "value_variable": value_col,
        "f_stat": round(f_stat, 2), "p_value": round(p, 8),
        "eta_squared": round(eta_squared, 4),
        "significant_at_05": bool(p < 0.05),
    }


def proportion_ci_by_group(df: pd.DataFrame, group_col: str) -> list:
    results = []
    for val, g in df.groupby(group_col, observed=True):
        n = len(g)
        successes = int(g["churn_flag"].sum())
        ci = wilson_ci(successes, n)
        results.append({
            group_col: val, "n": n, "churn_rate_pct": round(100 * successes / n, 2),
            "wilson_95pct_ci_pct": (round(ci[0] * 100, 2), round(ci[1] * 100, 2)),
        })
    return results


def run_all_hypothesis_tests(df: pd.DataFrame) -> dict:
    logger.info("Running full hypothesis-testing suite with effect sizes and CIs...")
    categorical_vars = [
        "contract_type", "internet_service", "payment_method", "gender",
        "senior_citizen", "has_partner", "has_dependents", "paperless_billing",
        "tenure_cohort", "online_security", "tech_support", "streaming_tv",
        "streaming_movies", "multiple_lines",
    ]
    numeric_vars = [
        "tenure_months", "monthly_charges", "total_charges", "churn_score",
        "cltv", "addon_service_count", "avg_revenue_per_tenure_month",
    ]

    results = {
        "chi_square_tests": [chi_square_with_effect_size(df, c) for c in categorical_vars],
        "t_tests": [ttest_with_effect_size_and_ci(df, c) for c in numeric_vars],
        "anova_monthly_charges_by_contract": one_way_anova(df, "contract_type", "monthly_charges"),
        "anova_cltv_by_internet_service": one_way_anova(df, "internet_service", "cltv"),
        "anova_tenure_by_payment_method": one_way_anova(df, "payment_method", "tenure_months"),
        "churn_rate_ci_overall": wilson_ci(int(df["churn_flag"].sum()), len(df)),
        "churn_rate_ci_by_contract": proportion_ci_by_group(df, "contract_type"),
        "churn_rate_ci_by_internet_service": proportion_ci_by_group(df, "internet_service"),
    }
    logger.info("Hypothesis testing suite complete.")
    return results


if __name__ == "__main__":
    import json
    df = pd.read_csv(DATA_PATH)
    results = run_all_hypothesis_tests(df)
    print(json.dumps(results, indent=2, default=str))
