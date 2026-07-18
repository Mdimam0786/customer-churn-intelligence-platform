# Machine Learning Report — Phase 7

Author: Md Imamuddin

*All models trained and evaluated against the real 7,043-customer processed dataset. Every metric below is genuine output from `src/ml/*.py` — reproducible by re-running the scripts.*

## Library availability note

`XGBoost`, `LightGBM`, and `shap` weren't available during development. Here's what was used instead, and why the results are still genuine, not approximated:
- **Gradient boosting**: scikit-learn's `GradientBoostingClassifier`/`GradientBoostingRegressor` — a real, different gradient-boosting implementation, just without XGBoost's histogram-based training optimizations (which matter for speed at massive scale, not for correctness at 7,043 rows).
- **SHAP**: permutation importance (global) + leave-one-feature-out marginal contribution (local) — both are legitimate, well-established, model-agnostic explainability methods, clearly labeled throughout as *not* Shapley values, not presented as SHAP-equivalent.
- **statsmodels** (used in Phase 6): manually implemented via the same closed-form OLS/MLE formulas — see Phase 6 report.

---

## 1. Churn Prediction

**Critical design decision:** IBM's own `churn_score` and `cltv` fields are **excluded** from all churn model features. Including them would let the model simply memorize IBM's own derived answer — the goal here is a model useful for **new customers who won't have a vendor-provided score**.

### 5-Fold Cross-Validated Model Comparison

| Model | ROC-AUC | Precision | Recall | F1 |
|---|---|---|---|---|
| Logistic Regression | 0.8577 ± 0.0088 | 0.530 | 0.813 | 0.642 |
| Random Forest | 0.8586 ± 0.0066 | 0.545 | 0.791 | 0.646 |
| **Gradient Boosting** | **0.8621 ± 0.0062** | 0.674 | 0.556 | 0.609 |

Gradient Boosting wins on ROC-AUC and was selected for hyperparameter tuning via `GridSearchCV` (27-combination grid, 3-fold CV): best parameters `learning_rate=0.05, max_depth=2, n_estimators=200`, achieving **CV ROC-AUC = 0.8637**.

### Final Test-Set Performance (held-out 20%, n=1,409)

- **ROC-AUC: 0.854** — exceeds the Phase 1 success threshold (≥0.80)
- **Precision: 0.669**, **Recall: 0.524**, **F1: 0.589**
- **Confusion matrix:** [[938 TN, 97 FP], [178 FN, 196 TP]]

### Business Cost-Optimized Threshold

Using an illustrative cost matrix (false negative = $200 lost-customer cost, false positive = $30 wasted-outreach cost — **placeholder values; replace with your company's real unit economics before production use**), the cost-minimizing probability threshold is **0.10**, not the default 0.5. At this threshold, total assumed cost drops from $38,510 (default) to **$17,720** — a 54% reduction, because missing a churner is assumed far more expensive than a wasted retention offer.

### Feature Importance (Gradient Boosting, built-in)

| Rank | Feature | Importance |
|---|---|---|
| 1 | tenure_months | 0.247 |
| 2 | internet_service = Fiber optic | 0.203 |
| 3 | payment_method = Electronic check | 0.103 |
| 4 | contract_type = Two year | 0.098 |
| 5 | has_dependents = Yes | 0.096 |
| 6 | contract_type = One year | 0.070 |
| 7 | total_charges | 0.057 |

### Permutation Importance (model-agnostic cross-check)

| Rank | Feature | Importance (ROC-AUC drop) |
|---|---|---|
| 1 | tenure_months | 0.0661 |
| 2 | has_dependents | 0.0333 |
| 3 | contract_type | 0.0316 |
| 4 | internet_service | 0.0197 |
| 5 | monthly_charges | 0.0056 |

Both methods agree on the top driver (tenure) and largely agree on the top 4 — a good robustness signal that these aren't artifacts of one importance-calculation method.

### Local Explanation Example (highest-risk real customer in test set)

Predicted churn probability: **0.908**. Leave-one-feature-out analysis shows tenure is overwhelmingly the dominant individual driver for this specific customer: resetting their tenure (1 month) to the population average (32.4 months) alone would drop their predicted probability by **-0.236** — nearly 4x the next-largest single-feature effect (monthly_charges, -0.034).

---

## 2. Customer Segmentation (K-Means)

- **Statistically best fit: k = 2** (silhouette score = 0.390) — a simple high-risk / low-risk split. This is the mathematically strongest result, but it's too basic to be useful for a marketing or customer success team.
- **Practical choice: k = 5** (silhouette score = 0.329) — the next-best statistical option, and a far more usable, detailed segmentation. This is the version used going forward, and it's labeled clearly as the practical choice rather than the "optimal" one.

### 5-Segment Profiles (all real, computed averages)

| Segment | Size | Avg Tenure | Avg CLTV | Churn Rate | Tags |
|---|---|---|---|---|---|
| 0 | 1,350 (19.2%) | 13.7 mo | $5,080 | **47.63%** | Highest churn risk |
| 1 | 1,861 (26.4%) | 60.8 mo | $5,178 | 13.06% | Longest tenured |
| 2 | 840 (11.9%) | 54.8 mo | **$5,224** | **3.69%** | Highest CLTV, lowest churn |
| 3 | 1,583 (22.5%) | 11.4 mo | $3,683 | 26.22% | Mid-range |
| 4 | 1,409 (20.0%) | 22.9 mo | $3,036 | 38.11% | Mid-range, high risk |

Segment 2 is the clear "model customer" profile: long-tenured, no-internet or low-service customers on 2-year contracts with the highest CLTV and lowest churn — a useful retention benchmark to aspire toward for other segments.

---

## 3. Customer Lifetime Value (CLTV) Prediction

Predicting IBM's real, provided CLTV field from independently observable business features (not from churn_score, to keep it usable pre-churn-scoring).

| Model | CV R² | CV MAE |
|---|---|---|
| Linear Regression | 0.157 | $914.16 |
| **Random Forest** | **0.215** | **$888.32** |
| Gradient Boosting | 0.204 | $891.54 |

**Test-set: R²=0.220, MAE=$876.03, RMSE=$1,029.50** (CLTV range in data: $2,003–$6,500, mean $4,400.30).

**Honest limitation:** R²≈0.22 is modest. `tenure_months` alone drives 77% of the Random Forest's feature importance — meaning most of what these business fields can tell us about CLTV, they tell us through tenure. IBM's real CLTV field very likely incorporates proprietary signals (e.g. actual usage volume, support interaction history, network cost-to-serve) not present in this dataset, which caps how well it can be reconstructed from billing/contract fields alone. This is reported as-is rather than oversold.

---

## 4. Upsell Recommendation

No real transaction/purchase-event log exists in this dataset, so a genuine collaborative-filtering recommender isn't possible without fabricating interaction data. Instead: **for each of the 6 real add-on services, a classifier predicts which non-adopting customers most resemble current adopters** — a real, defensible targeting signal, not a market-basket recommendation.

| Service | Current Adoption | CV ROC-AUC |
|---|---|---|
| streaming_tv | 49.07% | 0.889 |
| streaming_movies | 49.52% | 0.889 |
| tech_support | 37.05% | 0.829 |
| device_protection | 43.90% | 0.806 |
| online_security | 36.60% | 0.798 |
| online_backup | 44.03% | 0.774 |

All 6 models show strong discrimination (ROC-AUC 0.77–0.89). **5,233 real customers** received a specific top-recommendation (highest-probability service they don't yet have) — e.g., customer `9225-BZLNZ` has a 92.9% modeled fit for `tech_support`. Recommendation volume skews toward `online_backup` (1,527 customers) and `online_security` (1,035) — both also flagged in Phase 3/6 as having the strongest retention association, meaning upsell targeting here has a plausible dual payoff (revenue + retention).

---

## 5. Renewal Probability & Cancellation Risk Scoring

Per the Phase 1 scope, these are listed as separate deliverables from "churn prediction." In this dataset, they are **the same underlying signal viewed from two business angles**, not three independent models:
- **Cancellation risk score** = the churn model's `predict_proba()` output directly (Section 1).
- **Renewal probability** = `1 − cancellation risk score`.

Building three separate models for this would mean training near-identical models on the same target with no real business or statistical reason to do so. `fn_get_high_risk_customers()` (see the SQL work in Phase 4) and this churn model together already cover all three use cases.

---

## Supporting Charts

- `docs/ml_charts/roc_curve.png` — Churn model ROC curve
- `docs/ml_charts/model_comparison.png` — 3-model CV comparison
- `docs/ml_charts/feature_importance.png` — Top 12 churn predictors
- `docs/ml_charts/silhouette_by_k.png` — K-Means k-selection
- `docs/ml_charts/segment_profiles.png` — 5-segment churn rate & CLTV profiles

## Files Produced

```
src/ml/churn_model.py
src/ml/explainability.py
src/ml/segmentation.py
src/ml/ltv_model.py
src/ml/upsell_model.py
docs/churn_model_results.json
docs/explainability_results.json
docs/segmentation_results.json
docs/ltv_model_results.json
docs/upsell_recommendation_results.json
docs/ml_report.md (this file)
docs/ml_charts/*.png
```

### Next Step

Ready for **Phase 8: Business Intelligence Synthesis** (executive KPIs, retention strategy, revenue optimization, customer health score, risk analysis, prioritized recommendations) whenever you confirm.
