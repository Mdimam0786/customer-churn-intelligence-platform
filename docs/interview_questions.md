# Interview Questions & Answers

Author: Md Imamuddin

*These are based on real decisions made in this project, not generic interview prep.*

---

**Q: Walk me through your churn model's biggest design decision.**

A: I left out IBM's own `churn_score` and `cltv` fields from the model's inputs. Including them would let the model just copy IBM's own existing answer instead of learning from the real business data — that would boost accuracy on paper but be useless for a brand-new customer who doesn't have a vendor-assigned score yet. Leaving them out made it a harder, more honest problem to solve, and the model still reached 0.854 ROC-AUC using only real, observable business fields — something a company could actually use from day one.

**Q: Your CLTV model only reached an R² of 0.22. Why not tune it further or try a different algorithm?**

A: I compared three algorithms — Linear Regression, Random Forest, and Gradient Boosting — using cross-validation, and Random Forest came out best at 0.215. More tuning wasn't going to close that gap. The real explanation shows up in the feature importance: tenure alone accounts for 77% of what the model relies on, meaning most of what these fields can tell you about lifetime value, they tell you through tenure. IBM's real CLTV number almost certainly uses other signals this dataset doesn't include — things like usage volume or support history. Reporting an honest, modest R² with that explanation is more useful than chasing a better number that wouldn't reflect reality.

**Q: How did you test your SQL without access to a live database server?**

A: I tested the core query logic — CTEs and window functions — in SQLite, since SQLite supports the same standard SQL syntax PostgreSQL uses for these features. For PostgreSQL-only features like stored procedures and materialized views, which SQLite can't run, I tested the underlying `SELECT` logic separately to confirm it worked correctly. Every number in my SQL verification log is real output from that testing, not a guess.

**Q: Why did you use 5 customer segments when your own analysis found 2 was the statistically "best" number?**

A: The silhouette score did favor 2 segments, and I reported that honestly instead of hiding it. But a 2-group "high risk / low risk" split isn't very useful for a marketing or customer success team to act on. 5 segments was the next-best statistical option and gave a much more usable, detailed picture, so I used that instead and labeled it clearly as the practical choice rather than claiming it was the mathematically optimal one. Knowing the difference between "statistically best" and "actually useful" is exactly the kind of judgment call an analyst needs to make.

**Q: What would you do differently with more time or data?**

A: Three things: get real transaction history to build true purchase-based recommendations instead of the estimates I had to use here; get real subscription dates so I could build proper year-over-year reporting instead of tenure-based grouping; and get access to network/service-quality data to directly test whether fiber-optic churn is really about service quality rather than just price.

**Q: How do you know your revenue projections in the business recommendations aren't just made up?**

A: They're not a new model — they're simple math using real, already-tested churn rate differences (for example, month-to-month customers churn at 42.71% versus 11.27% for one-year contracts, both backed by statistical testing). I labeled every projection clearly as an estimate, not a guarantee, and included the actual calculation so it can be checked or re-run by anyone.

**Q: Your dataset is 100% California. Doesn't that limit your findings?**

A: Yes, and I call that out directly instead of letting it pass as a national analysis. I checked this directly in the data rather than assuming it, because I'd made an unverified claim earlier in the project and wanted to be more careful going forward. Every geography-based finding in this project is scoped to California, and I recommend adding a second region's data as a next step.

**Q: Why not just use XGBoost or SHAP if they're so standard?**

A: They weren't available in my development environment at the time. Rather than fake using them or pretend a substitute was identical, I used well-established alternatives — scikit-learn's Gradient Boosting and permutation importance — and documented clearly what I used and why they're solid, real tools for the job, even if they're not the exact same library.
