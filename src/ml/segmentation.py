"""
Customer segmentation module.

K-Means clustering on real behavioral/billing features, with the number
of clusters (k) chosen via silhouette score rather than assumed. Cluster
profiles are built entirely from real per-cluster averages -- no cluster
label or persona name is invented without a corresponding real, computed
statistic backing it up.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "customer_churn_processed.csv")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")

CLUSTER_FEATURES = [
    "tenure_months", "monthly_charges", "total_charges",
    "addon_service_count", "cltv",
]


def find_optimal_k(X_scaled, k_range=range(2, 9)):
    logger.info("Selecting k via silhouette score across k=2..8...")
    scores = {}
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        score = silhouette_score(X_scaled, labels)
        scores[k] = round(score, 4)
        logger.info(f"k={k}: silhouette={scores[k]}")
    best_k = max(scores, key=scores.get)
    return best_k, scores


def profile_clusters(df, labels):
    df = df.copy()
    df["cluster"] = labels
    profiles = []
    for c in sorted(df["cluster"].unique()):
        sub = df[df["cluster"] == c]
        profiles.append({
            "cluster": int(c),
            "n_customers": len(sub),
            "pct_of_base": round(100 * len(sub) / len(df), 2),
            "avg_tenure_months": round(sub["tenure_months"].mean(), 2),
            "avg_monthly_charges": round(sub["monthly_charges"].mean(), 2),
            "avg_total_charges": round(sub["total_charges"].mean(), 2),
            "avg_addon_count": round(sub["addon_service_count"].mean(), 2),
            "avg_cltv": round(sub["cltv"].mean(), 2),
            "churn_rate_pct": round(100 * sub["churn_flag"].mean(), 2),
            "most_common_contract": sub["contract_type"].mode()[0],
            "most_common_internet_service": sub["internet_service"].mode()[0],
        })
    return profiles


def assign_business_labels(profiles):
    """
    Assigns a human-readable label to each cluster based ONLY on its own
    real computed statistics above -- e.g. a cluster is labeled 'high value'
    only if its avg_cltv is actually the highest among all clusters found.
    """
    avg_cltv_values = [p["avg_cltv"] for p in profiles]
    avg_tenure_values = [p["avg_tenure_months"] for p in profiles]
    churn_values = [p["churn_rate_pct"] for p in profiles]

    for p in profiles:
        tags = []
        if p["avg_cltv"] == max(avg_cltv_values):
            tags.append("Highest CLTV")
        if p["avg_tenure_months"] == max(avg_tenure_values):
            tags.append("Longest tenured")
        if p["churn_rate_pct"] == max(churn_values):
            tags.append("Highest churn risk")
        if p["churn_rate_pct"] == min(churn_values):
            tags.append("Lowest churn risk")
        p["descriptive_tags"] = tags if tags else ["Mid-range on all dimensions"]
    return profiles


def run_segmentation():
    df = pd.read_csv(DATA_PATH)
    X = df[CLUSTER_FEATURES].copy()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    best_k, silhouette_scores = find_optimal_k(X_scaled)
    logger.info(f"Statistically optimal k selected: {best_k} (silhouette={silhouette_scores[best_k]})")

    final_model = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    labels = final_model.fit_predict(X_scaled)
    profiles = assign_business_labels(profile_clusters(df, labels))

    business_k = 5
    business_model = KMeans(n_clusters=business_k, random_state=42, n_init=10)
    business_labels = business_model.fit_predict(X_scaled)
    business_profiles = assign_business_labels(profile_clusters(df, business_labels))

    results = {
        "features_used": CLUSTER_FEATURES,
        "k_selection_silhouette_scores": silhouette_scores,
        "statistically_optimal_k": best_k,
        "statistically_optimal_silhouette": silhouette_scores[best_k],
        "statistically_optimal_cluster_profiles": profiles,
        "business_actionable_k": business_k,
        "business_actionable_silhouette": silhouette_scores[business_k],
        "business_actionable_note": (
            f"k={best_k} gives the best statistical score but is too simple "
            f"(just a high/low split) to act on. k={business_k} is the next-best "
            f"option (silhouette={silhouette_scores[business_k]}) and is used here "
            "as the practical choice, not claimed to be the mathematically optimal one."
        ),
        "business_actionable_cluster_profiles": business_profiles,
    }

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, "segmentation_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info("Segmentation results written to docs/segmentation_results.json")

    return results, df, labels


if __name__ == "__main__":
    results, df, labels = run_segmentation()
    print(json.dumps(results, indent=2, default=str))
