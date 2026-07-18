# Business Intelligence Synthesis — Phase 8

Author: Md Imamuddin

*This report synthesizes findings from Phases 2–7 into a single, prioritized business narrative. Every recommendation below is traceable to a specific, real, previously-computed statistic — no recommendation here introduces a new claim without a data citation. Illustrative "what-if" impact estimates are explicitly labeled as projections based on historical rates, not guarantees.*

---

## 1. Executive KPI Summary

| KPI | Value | Source |
|---|---|---|
| Total customers | 7,043 | Phase 2 |
| Overall churn rate | 26.54% (95% CI: 25.52–27.58%) | Phase 3/6 |
| Total billed revenue | $16,056,624.30 | Phase 2 |
| Current MRR | $456,116.60 | Phase 3 |
| MRR at risk (already churned) | $139,130.85 | Phase 3 |
| Churn model test ROC-AUC | 0.854 | Phase 7 |
| Highest-effect-size churn driver | Contract type (Cramér's V = 0.41) | Phase 6 |
| Statistically supported non-driver | Gender (p = 0.487) | Phase 6 |

---

## 2. Customer Health Score (Recap)

Defined in Phase 4 (`vw_customer_health_score`) and operationalized in Phase 5/7: a transparent, weighted composite —
**40% inverse churn-risk score + 25% tenure + 20% add-on adoption + 15% contract commitment.**

This rule-based score is intentionally simple and auditable, in contrast to the Phase 7 ML model. Comparing the two: the rule-based score and the ML model's `predict_proba()` agree strongly at the extremes (both flag the same highest-risk, lowest-tenure, month-to-month customers), giving CS teams a defensible score even before ML model deployment, and a natural check on the ML model once it's live (large disagreements between the two are worth manual review).

---

## 3. Risk Analysis — Who Is Actually at Risk

Combining Phase 3 (EDA), Phase 6 (statistics), and Phase 7 (segmentation + ML):

**The compounding risk profile** (each factor independently significant, per Phase 6 §1–2):
1. Month-to-month contract (42.71% churn vs. 2.83% for two-year)
2. Tenure under 12 months (47.44% churn vs. 6.61% for 61–72 months)
3. Fiber optic internet (41.89% churn vs. 7.40% for no internet)
4. Electronic check payment (45.29% churn vs. ~16% for automatic methods)
5. No dependents (32.55% churn vs. 6.52% with dependents)

**Segment-level risk** (Phase 7 K-Means, k=5): Segment 0 (19.2% of base, 47.63% churn rate) and Segment 4 (20.0% of base, 38.11% churn rate) together represent **39.2% of the customer base at substantially elevated risk** — the two segments Customer Success should prioritize first.

**Model-based risk (Phase 7):** the tuned Gradient Boosting model (ROC-AUC 0.854) plus IBM's own `churn_score` decile calibration (Phase 3/4 — Decile 10 = 100% actual churn) together mean a company can triage outreach **today**, without waiting on further model development — Deciles 8–10 alone (Phase 3 Insight 71) capture the large majority of realized churn.

**Root cause, not just risk factors** (Phase 3 §H): 33.23% of churn is competitor-driven (harder to control directly), but **24.34% is service/support-experience-driven** ("Attitude of support person" is the single most common documented reason at 10.27%) — this is the most directly *controllable* share of churn found in the entire analysis.

---

## 4. Retention Strategy — Prioritized, Quantified

*All "what-if" figures below are illustrative projections computed from real historical churn-rate differences (see `docs/business_impact_analysis.py`), assuming the converted subgroup behaves like the current comparison group on average. They are directional planning inputs, not guarantees — real pilot results should replace these estimates once available.*

### Priority 1 — Contract migration (Month-to-month → One-year)
Largest, single highest-confidence lever (Phase 6 §1, largest effect size in the dataset).

| Conversion Rate | Customers Converted | Est. Fewer Churns/Year | Est. MRR Protected |
|---|---|---|---|
| 10% | 387 | ~122 | ~$8,079 |
| 20% | 775 | ~244 | ~$16,179 |
| 30% | 1,162 | ~365 | ~$24,258 |

### Priority 2 — Payment method migration (Electronic check → Autopay)
Second-largest ANOVA effect size found in Phase 6 (η²=0.16 for tenure by payment method).

| Migration Rate | Customers Migrated | Est. Fewer Churns/Year | Est. MRR Protected |
|---|---|---|---|
| 20% | 473 | ~139 | ~$10,570 |
| 30% | 709 | ~208 | ~$15,843 |
| 50% | 1,182 | ~346 | ~$26,413 |

### Priority 3 — Service bundle upsell (1–2 add-ons → 3+ add-ons)
Directly supported by Phase 7's upsell models (ROC-AUC 0.77–0.89) — this isn't just a churn lever, it's simultaneously a revenue lever.

| Upgrade Rate | Customers Upgraded | Est. Fewer Churns/Year | Est. Extra MRR |
|---|---|---|---|
| 10% | 199 | ~40 | ~$3,519 |
| 20% | 399 | ~80 | ~$7,056 |
| 30% | 599 | ~120 | ~$10,593 |

### Priority 4 — First-12-months onboarding investment
Not independently quantifiable the same way (no controlled comparison group exists for "improved onboarding"), but justified by the single largest raw churn-rate cliff in the entire dataset: 47.44% (0–12mo) vs. 28.71% (13–24mo) — a bigger single-step drop than any other cohort transition (Phase 3 Insight 21–22).

### Priority 5 — Service/support quality initiatives
Justified by Phase 3 §H: 24.34% of churn is service/support-attributable, and it skews toward early-tenure customers (Insight 80) — meaning this priority directly reinforces Priority 4, not a separate initiative competing for resources.

---

## 5. Revenue Optimization

- **Two-year contracts generate the most total revenue ($6.28M) despite having the fewest customers** (Phase 3 Insight 16) — revenue optimization and retention optimization point in the same direction here, not in tension.
- **Full-bundle customers (all 6 add-ons) churn at just 5.28% and pay ~3x more per month** than zero-add-on customers (Phase 3 Insight 38) — bundle upsell is a rare "both/and," not "either/or," lever.
- **Revenue concentration is moderate, not extreme:** top 20% of customers by CLTV generate 28.22% of revenue (Phase 3 Insight 8) — there's no single "whale" dependency risk to manage around, but there is a real B2B-style opportunity to build a dedicated high-CLTV retention motion for the ~1,409 customers in that top quintile.
- **Caution flagged from Phase 6 §3:** CLTV does **not** differ significantly by internet service type — fiber customers pay more monthly but are not proven to be more valuable over their lifetime. Revenue strategy should not assume fiber-optic upsell automatically improves long-term value without also addressing fiber's much higher churn rate (41.89%).

---

## 6. Marketing Recommendations

1. **Do not build gender-targeted campaigns** — Phase 6 confirms no statistically significant churn difference by gender (p=0.487). This is a real, evidence-based "don't do this" recommendation, not just an omission.
2. **Target retention messaging by household structure**: customers without dependents (32.55% churn) and without partners (32.96% churn) are both significantly higher-risk (Phase 3 Insight 57–61) — household-stability segments are a legitimate, real targeting axis marketing doesn't typically consider.
3. **Use the Phase 7 segmentation (k=5) for lifecycle-stage messaging**: Segment 2 (long-tenured, low-churn, highest-CLTV) is the "aspirational" customer profile — marketing can use its real profile (2-year contract, no/low internet service, 54.8 mo avg tenure) as the target state for retention nudges aimed at Segments 0 and 4.
4. **Electronic-check payers are a distinct, targetable audience** for autopay-migration campaigns — not a demographic segment, a behavioral one, and one of the strongest levers found (Section 4, Priority 2).

## 7. Product Recommendations

1. **Prioritize `online_security` and `tech_support` in any bundling redesign** — both are individually the strongest add-on-level churn predictors (Phase 3 Insight 40–41), stronger than the entertainment add-ons.
2. **Investigate the non-monotonic 1-add-on churn spike** (Phase 3 Insight 35: customers with exactly 1 add-on churn at 45.76%, higher than 0-add-on customers) before designing a "just add more services" default upsell flow — the data suggests a single add-on alone may create cost without perceived value, and product should understand why before scaling a fix.
3. **Fiber optic service quality deserves product/network-team attention independent of pricing** — fiber customers pay the most and churn the most (Phase 3 Insight 31, 33); Phase 3 §H shows service/support-attitude issues are a large share of churn, and fiber is disproportionately represented in complaints about download speed relative to competitors (Insight 74).
4. **Use the Phase 7 upsell model output operationally**: 5,233 real customers already have a specific, ranked next-best-service recommendation (e.g. customer `9225-BZLNZ` at 92.9% fit for `tech_support`) — this is ready to feed a CS/marketing outreach list today, not a future research item.

## 8. Business Recommendations — Consolidated Action Plan

| Priority | Action | Primary Data Justification | Owner |
|---|---|---|---|
| 1 | Launch a month-to-month → annual contract incentive program | Cramér's V=0.41 (largest effect size, Phase 6) | RevOps / CS |
| 2 | Launch an electronic-check → autopay migration campaign | η²=0.16 tenure-by-payment-method (Phase 6) | Finance / Marketing |
| 3 | Build a 0–12-month onboarding intervention program | 47.44%→28.71% single largest cohort-transition drop (Phase 3) | Customer Success |
| 4 | Operationalize the Phase 7 upsell model as a live CS/marketing outreach list | 5,233 real customers with ranked recommendations, ROC-AUC 0.77–0.89 (Phase 7) | Product / Marketing |
| 5 | Investigate service/support-attitude churn root causes | 24.34% of churn service-attributable, most controllable category (Phase 3 §H) | Customer Success / Training |
| 6 | Deploy the Phase 7 churn model with the 0.10 cost-optimized threshold (adjust to real unit economics first) | 54% assumed cost reduction vs. default threshold (Phase 7) | Data/Analytics + CS |
| 7 | Investigate fiber-optic network/service quality independent of pricing | Highest churn + highest complaint share + no CLTV benefit found for fiber (Phase 3, Phase 6 §3) | Product / Network Ops |

---

## Methodology Transparency Note

This synthesis draws exclusively on statistics and model outputs already computed and documented in Phases 2–7. The "what-if" revenue/churn impact projections in Section 4 are the only *new* calculations in this phase — computed via `src/analysis/business_impact_analysis.py` (output saved to `docs/business_impact_analysis.json`), using simple, transparent historical-rate-difference arithmetic (not a new model), and explicitly labeled as directional estimates rather than forecasts.
