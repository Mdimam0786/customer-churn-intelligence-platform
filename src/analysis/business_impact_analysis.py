"""
Business impact what-if analysis.

Computes illustrative revenue/churn impact projections for the Phase 8
BI synthesis report, using simple, transparent historical-rate-difference
arithmetic against the real Phase 2 processed dataset -- NOT a new
predictive model, and explicitly not a guarantee of future results.
Each projection assumes the converted/upgraded subgroup would come to
behave like the real comparison group used, on average.
"""

import os
import sys
import json
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "customer_churn_processed.csv")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")


def contract_migration_scenarios(df):
    mtm = df[df.contract_type == "Month-to-month"]
    mtm_churn_rate = mtm.churn_flag.mean()
    one_yr_churn_rate = df[df.contract_type == "One year"].churn_flag.mean()
    avg_charge = mtm.monthly_charges.mean()

    scenarios = []
    for pct in [0.10, 0.20, 0.30]:
        n_converted = int(len(mtm) * pct)
        churn_avoided = n_converted * (mtm_churn_rate - one_yr_churn_rate)
        mrr_protected = churn_avoided * avg_charge
        scenarios.append({
            "conversion_rate_pct": int(pct * 100), "customers_converted": n_converted,
            "est_fewer_churns_per_year": round(churn_avoided, 0),
            "est_mrr_protected": round(mrr_protected, 2),
        })
    return {
        "mtm_customers": len(mtm), "mtm_mrr": round(mtm.monthly_charges.sum(), 2),
        "mtm_churn_rate_pct": round(mtm_churn_rate * 100, 2),
        "one_year_churn_rate_pct": round(one_yr_churn_rate * 100, 2),
        "scenarios": scenarios,
    }


def payment_migration_scenarios(df):
    ec = df[df.payment_method == "Electronic check"]
    auto = df[df.payment_method.isin(["Bank transfer (automatic)", "Credit card (automatic)"])]
    ec_churn = ec.churn_flag.mean()
    auto_churn = auto.churn_flag.mean()
    avg_charge_ec = ec.monthly_charges.mean()

    scenarios = []
    for pct in [0.20, 0.30, 0.50]:
        n_migrated = int(len(ec) * pct)
        churn_avoided = n_migrated * (ec_churn - auto_churn)
        mrr_protected = churn_avoided * avg_charge_ec
        scenarios.append({
            "migration_rate_pct": int(pct * 100), "customers_migrated": n_migrated,
            "est_fewer_churns_per_year": round(churn_avoided, 0),
            "est_mrr_protected": round(mrr_protected, 2),
        })
    return {
        "electronic_check_customers": len(ec),
        "electronic_check_churn_rate_pct": round(ec_churn * 100, 2),
        "autopay_churn_rate_pct": round(auto_churn * 100, 2),
        "scenarios": scenarios,
    }


def addon_upgrade_scenarios(df):
    low_addon = df[df.addon_service_count.isin([1, 2])]
    high_addon = df[df.addon_service_count >= 3]
    churn_low = low_addon.churn_flag.mean()
    churn_high = high_addon.churn_flag.mean()
    avg_charge_diff = high_addon.monthly_charges.mean() - low_addon.monthly_charges.mean()

    scenarios = []
    for pct in [0.10, 0.20, 0.30]:
        n_upgraded = int(len(low_addon) * pct)
        churn_avoided = n_upgraded * (churn_low - churn_high)
        extra_mrr = n_upgraded * avg_charge_diff
        scenarios.append({
            "upgrade_rate_pct": int(pct * 100), "customers_upgraded": n_upgraded,
            "est_fewer_churns_per_year": round(churn_avoided, 0),
            "est_extra_mrr": round(extra_mrr, 2),
        })
    return {
        "customers_with_1_2_addons": len(low_addon),
        "churn_rate_1_2_addons_pct": round(churn_low * 100, 2),
        "churn_rate_3plus_addons_pct": round(churn_high * 100, 2),
        "avg_monthly_charge_diff": round(avg_charge_diff, 2),
        "scenarios": scenarios,
    }


def run_business_impact_analysis():
    df = pd.read_csv(DATA_PATH)
    logger.info("Computing business impact what-if scenarios from real historical rates...")

    results = {
        "methodology_note": (
            "Illustrative projections using real historical churn-rate and "
            "revenue differences already found in Phases 3/6. NOT a new "
            "predictive model -- simple, transparent arithmetic, assuming "
            "the converted subgroup comes to resemble the real comparison "
            "group on average. Directional planning inputs, not guarantees."
        ),
        "contract_migration": contract_migration_scenarios(df),
        "payment_method_migration": payment_migration_scenarios(df),
        "addon_bundle_upgrade": addon_upgrade_scenarios(df),
    }

    with open(os.path.join(DOCS_DIR, "business_impact_analysis.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info("Business impact analysis written to docs/business_impact_analysis.json")

    return results


if __name__ == "__main__":
    results = run_business_impact_analysis()
    print(json.dumps(results, indent=2, default=str))
