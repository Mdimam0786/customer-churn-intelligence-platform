# Exploratory Data Analysis — Phase 3

Author: Md Imamuddin
## 100+ Business Insights, All Computed From Real Data

*Source: `data/processed/customer_churn_processed.csv` (7,043 real customers, IBM Telco Customer Churn dataset). Every figure below is computed directly by `src/eda/eda_analysis.py` and stored in `docs/insights_data.json` — none are estimated or invented.*

---

## Executive Summary

Of **7,043 real customers**, **1,869 (26.54%) have churned**, representing **$139,130.85 in monthly recurring revenue currently at risk** on top of already-lost lifetime billings. Churn is not random: it concentrates overwhelmingly in month-to-month contracts, low-tenure customers, fiber-optic subscribers, and electronic-check payers — and IBM's own `Churn Score` field is a well-calibrated predictor of these same patterns (Decile 10 customers churned at 100%; Deciles 1–4 churned at 0%). The single highest-leverage retention lever is **contract migration**: two-year contract customers churn at 2.83% versus 42.71% for month-to-month — a 15x difference.

---

## Section A — Overview & Financial Impact (Insights 1–12)

1. The dataset contains **7,043 real customers**, of whom **1,869 have churned (26.54%)** and **5,174 remain active (73.46%)**.
2. Total historical billed revenue across all customers is **$16,056,624.30**.
3. Current monthly recurring revenue (MRR) across the active + churned base is **$456,116.60**.
4. Churned customers alone represent **$139,130.85 in monthly recurring revenue** that has already stopped or is stopping — a real, quantifiable revenue-at-risk figure, not an estimate.
5. Average monthly charge across all customers is **$64.76**; average real tenure is **32.37 months** (median 29 months).
6. Average CLTV (IBM-provided) across all customers is **4,400.3**.
7. Counter-intuitively, **churned customers have a slightly *lower* average CLTV (4,149.41) than retained customers (4,490.92)** — churn is not concentrated in the company's highest-value accounts, which is a mildly reassuring financial signal.
8. The top 10% of customers by CLTV account for **17.2% of total revenue**; the top 20% account for **28.22%**; the top 50% account for **63.51%** — revenue is meaningfully concentrated but not extremely top-heavy (no "whale" dependency risk).
9. Contract mix is **55.0% month-to-month, 24.1% two-year, 20.9% one-year** — the majority of the base sits in the highest-churn-risk contract type.
10. Fiber optic is the single largest internet segment (**3,096 customers, 43.9% of base**) and also the highest-revenue internet tier (**$9.92M in total billed revenue**, more than DSL and No-Internet combined).
11. Electronic check is the most common payment method (**2,365 customers, 33.6% of base**) and also the highest-churn payment method.
12. The dataset is **100% California** (verified, not assumed) across 1,129 distinct real cities — any "national" framing of these results would be incorrect.

---

## Section B — Contract Type: The Single Strongest Churn Driver (Insights 13–20)

13. Month-to-month customers churn at **42.71%** — more than **15x** the rate of two-year contract customers (**2.83%**).
14. One-year contract customers churn at **11.27%**, roughly 4x the two-year rate but a third of the month-to-month rate — contract length has a clear dose-response relationship with retention.
15. A chi-square test confirms `contract_type` is a highly significant predictor of churn (χ²=1184.6, p<0.001) — this is the strongest categorical association found anywhere in the dataset.
16. Despite having the fewest customers, two-year contracts generate the **most total revenue of any contract tier ($6.28M)** — longer commitments are also more valuable, not just more stable.
17. Month-to-month customers have the shortest average real tenure (**18.04 months**) versus 42.04 months (one-year) and 56.74 months (two-year).
18. Month-to-month average CLTV ($4,136.71) is lower than one-year ($4,529.96) and two-year ($4,890.21) — contract length correlates with customer value as well as loyalty.
19. **Business implication:** converting even a modest share of month-to-month customers to annual contracts (via incentivized upgrade offers) is the highest-leverage retention lever available in this dataset, given the 15x churn-rate gap.
20. Month-to-month customers' average monthly charge ($66.40) is actually *higher* than one-year ($65.05) — these customers are not churning due to being lower-value or discount-seeking; the lack of commitment itself is the risk factor.

---

## Section C — Tenure Cohorts: Early Life Is Where Churn Happens (Insights 21–30)

21. The 0–12 month cohort has by far the highest churn rate (**47.44%**) — nearly half of brand-new customers churn within their first year.
22. Churn rate drops monotonically with tenure cohort: 47.44% (0–12mo) → 28.71% (13–24mo) → 21.63% (25–36mo) → 19.03% (37–48mo) → 14.42% (49–60mo) → 6.61% (61–72mo).
23. The 0–12 month cohort is also the **largest single cohort (2,186 customers, 31.0% of the base)** — the highest-risk segment is also the largest, compounding its business impact.
24. A chi-square test confirms tenure cohort is highly significant against churn (χ²=873.9, p<0.001).
25. The 61–72 month (longest-tenured) cohort generates the most total revenue of any cohort (**$7.29M**) despite having fewer customers (1,407) than the 0–12 month cohort — loyalty compounds into revenue.
26. Average CLTV is *not* strictly monotonic with tenure: it dips slightly in the middle cohorts (37–48mo: $3,945.86) before rising again in the 49–60mo ($5,236.89) and 61–72mo ($5,214.58) cohorts — worth further segmentation in Phase 5/7 rather than assuming a simple linear relationship.
27. A t-test on raw tenure confirms churned customers have dramatically shorter average tenure (17.98 months) than retained customers (37.57 months) — a >2x gap, highly significant (p<0.001).
28. **Business implication:** the first 12 months is the critical retention window; onboarding quality, early support experience, and proactive check-ins in months 1–12 likely have outsized ROI versus later-life retention spend.
29. Average monthly charges rise with tenure cohort (from $56.10 in 0–12mo to $75.95 in 61–72mo) — long-tenured customers are paying more per month on average, not receiving discounts that erode revenue.
30. The tenure-churn relationship, combined with the contract-churn relationship, suggests these two variables are related but not identical drivers — both should be modeled together in Phase 7 rather than treated as redundant.

---

## Section D — Internet Service & Add-on Adoption (Insights 31–45)

31. Fiber optic customers churn at **41.89%**, more than double DSL (18.96%) and nearly 6x "No Internet" customers (7.4%).
32. A chi-square test confirms internet service type is highly significant against churn (χ²=732.3, p<0.001).
33. Fiber optic is also the most expensive tier by far (**$91.50 avg monthly charge** vs. $58.10 for DSL) — price sensitivity is a plausible contributing factor worth testing statistically alongside service-quality complaints.
34. Customers with **zero add-on services** churn at 21.41% — lower than several higher-addon-count segments, meaning "no add-ons" is not the highest-risk profile as might be assumed.
35. Customers with exactly **1 add-on service** churn at the *highest* rate of any add-on tier (**45.76%**) — this is a non-monotonic, non-intuitive real pattern worth flagging for the ML feature-importance analysis in Phase 7 rather than assuming "more add-ons always help."
36. Churn rate then falls steadily from 2 add-ons (35.82%) through 6 add-ons (5.28%) — once a customer has 2+ services, further adoption strongly correlates with retention.
37. Customers with the **full 6-service bundle** churn at just **5.28%** — the lowest churn rate of any add-on segment.
38. Average monthly charges rise steadily with add-on count, from $32.79 (0 add-ons) to $99.37 (6 add-ons) — full-bundle customers pay ~3x more per month yet churn far less, making bundle upsell a strong retention *and* revenue lever simultaneously.
39. A t-test confirms add-on service count is significantly lower among churned customers (mean 1.77) than retained customers (mean 2.14, p<0.001).
40. `online_security` is a highly significant churn predictor on its own (χ²=850.0, p<0.001) — among the strongest individual service-level signals in the dataset.
41. `tech_support` is similarly highly significant (χ²=828.2, p<0.001) — customers without tech support churn measurably more.
42. `streaming_tv` and `streaming_movies` are both significant (χ²=374.2 and 375.7 respectively, p<0.001) but noticeably weaker predictors than online_security or tech_support — entertainment add-ons matter less to retention than security/support add-ons.
43. `multiple_lines` is the *weakest* significant service predictor found (χ²=11.3, p=0.0035) — still statistically significant at n=7,043 but with far less practical effect size than the others.
44. Only **4.03% of customers (284)** hold the complete 6-service add-on bundle — a large, largely untapped upsell population given how strongly bundling correlates with retention.
45. **Business implication:** online_security and tech_support are the two individual add-ons with the strongest retention association — bundling promotions should prioritize these two services first if forced to sequence a rollout.

---

## Section E — Payment Method (Insights 46–53)

46. Electronic check payers churn at **45.29%** — nearly 3x the rate of any other payment method.
47. Mailed check payers churn at 19.11%; bank transfer (automatic) at 16.71%; credit card (automatic) at 15.24% — all three non-electronic-check methods cluster tightly together, well below electronic check.
48. A chi-square test confirms payment method is highly significant (χ²=648.1, p<0.001) — one of the strongest single categorical predictors in the dataset, on par with internet service type.
49. Electronic check customers also have the highest average monthly charge ($76.26) among payment methods, yet the lowest average tenure (25.17 months) — high-value customers churning fastest via this specific payment channel.
50. Automatic payment methods (bank transfer and credit card) both show the **longest average tenures** (43.66 and 43.27 months respectively) — auto-pay itself may be acting as a soft retention mechanism by removing a monthly point of re-decision.
51. Electronic check generates the second-highest total revenue ($4.94M) despite its poor retention — meaning this channel carries meaningful revenue-at-risk exposure, not just a marginal segment.
52. **Business implication:** migrating electronic-check customers to automatic payment methods (bank transfer or credit card) is a concrete, low-cost intervention with a real, quantifiable historical association with better retention.
53. `paperless_billing` is also significant against churn (χ²=258.3, p<0.001) — worth testing jointly with payment method in Phase 7, as these two billing-experience variables likely interact.

---

## Section F — Demographics (Insights 54–63)

54. **Gender shows no significant association with churn** (χ²=0.484, p=0.487) — Female churn (26.92%) and Male churn (26.16%) are statistically indistinguishable. Any gender-targeted retention strategy would be unsupported by this data.
55. Senior citizens churn at **41.68%**, versus 23.61% for non-seniors — a highly significant difference (χ²=159.4, p<0.001).
56. Senior citizens also pay more per month on average ($79.82 vs $61.85) — higher bills alongside higher churn is worth investigating as a price-sensitivity signal for this segment specifically.
57. Customers without a partner churn at **32.96%**, nearly double those with a partner (**19.66%**) — highly significant (χ²=158.7, p<0.001).
58. Customers without dependents churn at **32.55%**, nearly 5x those with dependents (**6.52%**) — the strongest demographic effect found in the dataset (χ²=433.7, p<0.001).
59. Customers with dependents have both the lowest churn rate (6.52%) and among the highest CLTV ($4,525.96) — combined with having-a-partner, household stability signals are strong, real retention predictors.
60. Customers without a partner also show shorter average tenure (23.36 months) versus 42.02 months for partnered customers.
61. Combining Insights 57 and 58: household structure (partner + dependents) appears to be a genuinely powerful, non-obvious churn signal — worth constructing a combined "household stability" feature in Phase 7 modeling.
62. Senior citizens represent only **16.2% of the base (1,142 customers)** but their elevated churn rate (41.68%) means they contribute disproportionately to total churn volume relative to their population share.
63. **Business implication:** demographic-based retention targeting should focus on household structure and senior-citizen status — not gender, which has no supported effect in this data.

---

## Section G — Churn Score Calibration (IBM-Provided Predictive Field) (Insights 64–72)

64. IBM's own `Churn Score` field is remarkably well-calibrated against actual outcomes: **Decile 10 (highest risk) churned at exactly 100%**, and **Deciles 1–4 (lowest risk) churned at exactly 0%**.
65. The score shows a clean, near-monotonic decline from Decile 10 (100% actual churn) down through Decile 6 (25.16%) before flattening to 0% at Decile 5 and below.
66. Decile 9 churned at 74.4% and Decile 8 at 37.0% — a steep drop-off between deciles 9 and 8, suggesting the score's discrimination is sharpest at the very top of the risk range.
67. Deciles 7 and 8 show almost identical actual churn rates (37.77% vs 37.0%) despite different average scores (71.0 vs 76.1) — a minor non-monotonicity worth noting for anyone building a churn-score-based alert threshold.
68. Total monthly revenue is roughly evenly distributed across deciles (ranging $38,822–$51,674 per decile) — risk is not concentrated in a narrow revenue band, meaning intervention resources can't rely on revenue-size alone to triage risk.
69. Average CLTV does **not** decline monotonically with churn-risk decile (Decile 10 avg CLTV $4,171 vs Decile 5 avg CLTV $4,603) — high risk-score customers are not necessarily the lowest-value customers, reinforcing Insight 7.
70. Because Deciles 1–5 (top half of the base, ~3,545 customers) show **essentially zero actual churn**, retention spend targeting this half of the base would very likely be wasted — the risk score alone already does the job of triage.
71. **Business implication:** IBM's Churn Score is production-ready as a triage signal; a company adopting this data does not need to wait for the ML model in Phase 7 to start prioritizing outreach — Deciles 8–10 alone (2,008 customers, ~28.5% of base) capture the vast majority of realized churn.
72. The Phase 7 ML model's job is not to "discover" churn risk from scratch — it's to (a) validate/replicate this score with transparent, explainable features, and (b) extend prediction to new customers who won't have an IBM-provided score.

---

## Section H — Churn Reason Analysis (Insights 73–86)

*(Based on the 1,869 churned customers who have a documented, real churn reason — not inferred.)*

73. The single most common documented churn reason is **"Attitude of support person" (192 customers, 10.27% of all churn)** — a service-experience issue, not a price or competitor issue.
74. Competitor-related reasons collectively are large: "Competitor offered higher download speeds" (10.11%), "Competitor offered more data" (8.67%), "Competitor made better offer" (7.49%), and "Competitor had better devices" (6.96%) sum to **33.23% of all churn** — competitive pressure is the single largest reason category when grouped.
75. Attitude/service-quality reasons ("Attitude of support person" 10.27% + "Attitude of service provider" 7.22% + "Service dissatisfaction" 4.76% + "Poor expertise of phone support" 1.07% + "Poor expertise of online support" 1.02%) sum to **24.34% of all churn** — nearly a quarter of churn is attributable to service/support experience, not product or price.
76. Price-related reasons ("Price too high" 5.24% + "Extra data charges" 3.05% + "Long distance charges" 2.35%) sum to just **10.64% of all churn** — pricing is a real but comparatively minor driver versus competitive pressure and service experience.
77. "Don't know" accounts for 8.24% of churn — a meaningful data-quality/exit-survey gap where root cause was never captured; improving exit-interview processes would sharpen future root-cause analysis.
78. "Moved" (a non-controllable, non-competitive reason) accounts for only 2.84% of churn — voluntary/controllable churn dominates over relocation-driven churn.
79. "Deceased" accounts for 0.32% of churn (6 customers) — a real but negligible share, included here only for completeness and data-integrity transparency.
80. Customers who churned due to "Attitude of support person" have a below-average tenure (18.09 months) — service-quality failures are hitting relatively early-tenure customers, compounding the Section C early-life risk finding.
81. Customers who churned due to competitor offers have the shortest average tenure among major reason categories (as low as 15.86–19.82 months) — competitive switching risk is concentrated in the same early-tenure window as overall churn risk.
82. The costliest single reason category by lost monthly revenue is **"Competitor offered higher download speeds" ($14,144.60/month lost)**, narrowly ahead of "Attitude of support person" ($13,980.85/month).
83. Combined, the top 5 reason categories (Attitude of support person, Competitor offered higher speeds, Competitor offered more data, Don't know, Competitor made better offer) account for **44.78% of all churned customers** — a small set of root causes drives nearly half of churn.
84. Customers citing "Extra data charges" as their churn reason have the highest average monthly charge among reason categories ($79.71) — a plausible direct link between this specific reason and this specific customer's actual bill level.
85. "Limited range of services" churners have the shortest average tenure of any reason category (12.57 months) — customers leaving due to feature gaps do so unusually early in the relationship.
86. **Business implication:** service-quality/support-attitude issues (24.34% of churn) are the most directly controllable churn driver identified in this dataset — more addressable through internal training/process fixes than competitor pricing or network capability, which require product/infrastructure investment.

---

## Section I — Geographic Analysis (Insights 87–94)

87. Los Angeles is the largest single city by customer count (305) and by total revenue ($647,771.10) — unsurprising given it's by far the largest California metro area in this sample.
88. Los Angeles churn rate (29.51%) is close to but slightly above the dataset-wide average (26.54%) — the largest market is not meaningfully safer or riskier than the base rate.
89. San Diego (150 customers) shows the highest churn rate among the top-10-revenue cities at **33.33%**, notably above the base rate.
90. Bakersfield, among the top-10-revenue cities, shows the lowest churn rate at **7.5%** — a real, notable outlier worth a follow-up look at what's different about this specific market (contract mix, service type, demographics).
91. Several small cities (5–10 customers each: Seeley, Indian Wells, San Dimas, Panorama City, La Puente, Daly City, Lompoc) show churn rates of 60–80%, but these are **too small a sample (n=5–10) to treat as reliable geographic signals** — flagged explicitly here to avoid the classic small-sample-size trap of over-interpreting a noisy city-level rate.
92. No consistent geographic churn "hot zone" pattern emerges among the larger, statistically meaningful cities (customers ≥ 30) beyond San Diego's elevated rate — geography appears to be a much weaker churn driver than contract type, tenure, or service type in this dataset.
93. Because this dataset is 100% California, no cross-state or cross-region comparison is possible here — any future expansion of this analysis with a second geographic market would meaningfully increase its business value.
94. **Business implication:** geographic targeting should be treated as a secondary, exploratory lever (worth a follow-up investigation into San Diego and Bakersfield specifically) rather than a primary retention strategy, given the weak overall geographic signal relative to contract/tenure/service drivers.

---

## Section J — Service Adoption Funnel (Insights 95–100)

*(A service-adoption funnel built from real service flags — not a session/event funnel, since no clickstream or signup-event data exists in this dataset.)*

95. **90.32%** of customers have phone service; **78.33%** have internet service; **68.65%** have both — the "full connectivity" customer is common but not universal.
96. **68.49%** of customers have adopted at least one add-on service — meaning roughly **31.5% of the base has zero add-ons**, a sizeable pure-upsell opportunity.
97. Adoption drops off sharply at higher engagement tiers: 68.49% have 1+ add-ons, but only **40.11%** have 3+ add-ons, and just **4.03%** have the full 6-service bundle — a classic steep funnel drop-off.
98. Given Section D's finding that full-bundle customers churn at just 5.28% versus 45.76% for single-add-on customers, closing the gap between the 40.11% (3+ addons) and 4.03% (full bundle) tiers represents the funnel's single highest-value target segment.
99. The jump from "1+ addons" (68.49%) to "3+ addons" (40.11%) represents the funnel's steepest drop (28.4 percentage points) — this is the specific transition point where upsell/bundling campaigns would have the most room to convert customers.
100. **Business implication:** rather than a generic "upsell more," the funnel data points to a specific, actionable target — moving customers from 1–2 add-ons into the 3+ tier, where churn risk drops substantially and revenue per customer rises materially (Insight 38).

---

## Section K — Correlation Structure (Insights 101–105)

101. `churn_score` correlates most strongly with `churn_flag` of any numeric field (as expected, since IBM derived it partly from outcome-related behavior) — confirmed via both the correlation matrix and the decile calibration in Section G.
102. `tenure_months` shows a clear negative correlation with `churn_flag` — consistent with every cohort-level finding in Section C.
103. `monthly_charges` shows a positive correlation with `churn_flag` — higher-paying customers churn somewhat more, consistent with the fiber-optic and senior-citizen findings above.
104. `total_charges` (a function of both tenure and monthly rate) shows a negative correlation with churn, dominated by the tenure effect — new, high-paying customers (high monthly charge, low total charge) are the highest-risk combination.
105. `addon_service_count` shows a negative correlation with churn, consistent with Section D's bundling findings, though the relationship is non-monotonic at the lowest counts (Insight 35) and a simple linear correlation understates that nuance — full detail should be read from Section D, not the correlation coefficient alone.

---

## Methodology Notes

- All statistical tests (chi-square for categorical variables, Welch's t-test for numeric variables) were run against the real 7,043-row processed dataset with no sampling.
- All insights above are traceable to `docs/insights_data.json`, itself generated by `src/eda/eda_analysis.py` — re-running that script against the same input data reproduces every number in this report exactly.
- Small-sample findings (e.g., city-level churn rates below n=30) are explicitly flagged as directional rather than reliable, rather than presented with false precision.
- No insight in this report references a field, date, or value that does not exist in the real source data.

---

### Supporting Charts

See `docs/charts/`:
- `churn_by_contract.png` — Churn rate by contract type
- `churn_by_tenure_cohort.png` — Churn rate by tenure cohort
- `revenue_by_contract.png` — Total revenue by contract type
- `churn_score_calibration.png` — Predicted risk decile vs. actual churn rate
- `churn_by_addon_count.png` — Churn rate by add-on service count

---

### Next Step

Ready to proceed to **Phase 4: Advanced SQL** (CTEs, window functions, views, materialized views, stored procedures, and business KPI queries built on the Phase 2 star schema) whenever you confirm.
