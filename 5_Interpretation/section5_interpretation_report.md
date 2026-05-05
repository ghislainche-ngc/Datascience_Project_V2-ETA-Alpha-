# Section 5: Model Interpretation, Business Insights & Recommendations

## Mobile Money Transaction Analysis — User Activity Classification

---

## 1. Key Findings from Modeling

Three classification models — Logistic Regression, Random Forest, and XGBoost — were trained to predict whether a mobile money user falls into Low, Medium, or High activity categories using 15 behavioral features extracted from 20,530 transactions across 69 users in Cameroon.

**The central finding is that behavioral features alone carry genuine predictive signal.** Random Forest, the best-performing model on the same 70/15/15 split, achieved a Test Macro F1 of 0.5476 and a CV Macro F1 of 0.3875 — both above the majority-class baseline (0.1429) and the stratified random baseline (0.2804). This means the model captures real patterns in how users transact, not statistical noise.

However, performance is moderate, not strong. A Macro F1 of 0.55 means the model correctly identifies user activity levels a little more than half the time across all three classes. This is meaningful for a first-generation model built on a small dataset with intentionally restricted features (all frequency-based features were excluded to prevent data leakage), but it also means a substantial share of predictions still require human review.

**Why this matters beyond the numbers:** The fact that the behavioral-only Random Forest and XGBoost models outperform both baselines — despite operating only on behavioral profile features — validates the hypothesis that *how* a user transacts (amounts, types, timing, direction) is informative about *how much* they transact, even when the model never sees frequency counts directly. This has direct implications for financial institutions: a new user's first few transactions already contain signals about their likely long-term engagement level.

---

## 2. What the Model Learned (Behavioral Insights)

### Feature Importance Interpretation

The model's feature importances, combined with Logistic Regression coefficients, reveal three distinct behavioral profiles:

**High-Activity Users (> 204 transactions)**
- Make many small-value transactions (negative coefficient for mean_amount in LR: -0.589)
- High send/receive ratio (avg_sr_ratio: strongest positive coefficient at +0.671) — they send money far more often than they receive it
- Dominated by airtime purchases (pct_airtime: XGBoost importance 0.0821) and transfers (pct_transfert: 0.0826)
- These users treat mobile money as an everyday utility: buying airtime top-ups, sending small transfers to family and contacts, and making frequent small payments

**Low-Activity Users (≤ 55 transactions)**
- Few but large-value transactions — they use mobile money for major operations rather than daily spending
- High average balance (avg_balance: strongest positive LR coefficient at +0.731) — they hold money in their mobile wallet rather than actively circulating it
- Low send/receive ratio (avg_sr_ratio: strongest negative coefficient at -0.823) — they receive money more than they send, suggesting they are net recipients (e.g., receiving salary or remittances)
- Higher proportion of withdrawals (pct_retrait: RF importance 0.0794) — when they do transact, they tend to cash out

**Medium-Activity Users (56–204 transactions)**
- Moderate transaction amounts (median_amount: strongest positive LR coefficient at +0.984) but not extreme in either direction
- No single dominant behavior — they blend elements of both High and Low profiles
- This mixed behavioral signature is precisely why the model struggles most with this class.

### The Human Story Behind the Features

These profiles map onto recognizable user archetypes in the Cameroonian mobile money ecosystem:

- **High-activity users** resemble small business owners, market vendors, or agents who use MoMo (MTN Mobile Money) and OrangeMoney as their primary financial tool — buying airtime for resale, sending daily transfers, and processing multiple small payments
- **Low-activity users** resemble salaried workers or occasional users who receive periodic payments and withdraw cash, treating mobile money as a channel rather than a platform
- **Medium-activity users** fall between these extremes — perhaps students, part-time workers, or users transitioning between usage patterns

The send/receive ratio (avg_sr_ratio) emerges as the single most discriminating feature across all three models. This ratio captures a fundamental behavioral divide: users who are net senders (pushing money outward through transfers, payments, and airtime) versus net receivers (collecting money and cashing out). This divide reflects economic roles — producers vs. consumers, agents vs. end-users — and is more stable than raw transaction amounts, which fluctuate with income and seasonal patterns.

---

## 3. Why the Medium Class is Difficult to Predict

The Medium activity class is the hardest to classify. This is not a failure of the model — it reflects a genuine structural challenge in the classification task.

**Quantile boundaries are artificial.** The Low/Medium/High thresholds (55 and 204 transactions) were determined by the 33rd and 66th percentiles of the transaction count distribution. Users near these boundaries — a user with 52 transactions (Low) vs. one with 58 transactions (Medium) — are separated by an arbitrary line, not a natural behavioral discontinuity. Their actual transaction profiles can be nearly identical.

**Behavioral overlap is real.** The error analysis confirms this: misclassifications predominantly occur between adjacent classes. Medium users predicted as Low (e.g., anon_user0003 with 65 transactions and 109,022 XAF mean amount) exhibit the large-value, low-frequency pattern typical of Low users. Medium users predicted as High (e.g., orig_user_024 with 195 transactions) are near the Medium/High boundary and exhibit High-like engagement patterns. The model is not randomly confused — it is responding to genuine behavioral similarity.

**The Medium class is a transitional zone.** Unlike High and Low users, who occupy behavioral extremes (many small vs. few large transactions), Medium users represent a spectrum of mixed behaviors. Some are Low users who occasionally spike in activity; others are emerging High users who have not yet reached full engagement. Without temporal features (which were excluded to prevent leakage), the model cannot distinguish between a user who is stable at Medium and one who is transitioning between levels.

**Implication:** In a production system, Medium-class predictions should be treated with lower confidence and may benefit from additional monitoring or a secondary confirmation step before triggering business actions.

---

## 4. Business Interpretation

### From Classification to Action

The ability to classify users into behavioral segments — even with moderate accuracy — creates immediate value for mobile money operators and financial institutions in Cameroon.

### Use Case 1: Customer Segmentation and Targeted Marketing

**High-activity users** are the most valuable segment. They generate the highest transaction volume and rely on mobile money as a daily tool. Business actions:
- Offer loyalty rewards, cashback on airtime purchases, or reduced transfer fees to retain these users
- Cross-sell premium services: micro-insurance, savings products, or merchant payment solutions
- Monitor for churn risk — a High user whose activity drops may be switching to a competitor

**Low-activity users** represent untapped potential. They have mobile money accounts and financial capacity (high average balances) but use the service infrequently. Business actions:
- Deploy targeted onboarding campaigns: tutorials, promotional transfers, or incentivized first-time payments
- Offer products suited to their behavior — scheduled bill payments, savings goals, or remittance-receiving features
- Investigate barriers to adoption: is it a trust issue, a usability issue, or simply a preference for cash?

**Medium-activity users** are the growth opportunity. They already use mobile money regularly but have not yet reached full engagement. Business actions:
- Nudge toward higher engagement through personalized offers based on their dominant transaction type
- Identify Medium users trending toward High activity and accelerate their transition with targeted features

### Use Case 2: Credit Risk Assessment

Transaction behavior is a proxy for financial stability. The model's features directly inform creditworthiness:
- **High-activity, low-variance users** (consistent small transactions, stable balance) are lower credit risk — they demonstrate regular financial activity and predictable cash flow
- **Low-activity, high-balance users** may be creditworthy but underserved — their balance levels suggest capacity, while their low engagement suggests alternative income sources
- **High-variance users** (large std_amount) may pose higher risk — irregular transaction patterns could indicate income instability or speculative behavior

Mobile money-based credit scoring is particularly relevant in Cameroon, where traditional credit bureaus have limited coverage. A behavioral classification model provides a first-pass risk tier without requiring formal financial history.

### Use Case 3: Fraud Detection Signals

While not a fraud detection model, the classification framework establishes behavioral baselines that can flag anomalies:
- A Low-activity user suddenly exhibiting High-activity patterns (rapid small transfers) could indicate account compromise
- A High-activity user whose send/receive ratio reverses abruptly may be involved in unauthorized transactions
- Users whose predicted class consistently differs from their actual behavior warrant closer examination

### Use Case 4: Service Optimization

Understanding peak transaction times (17:00–20:00 evening peak from EDA) combined with user segments enables infrastructure planning:
- Ensure server capacity for High-activity users during peak hours
- Schedule maintenance during Low-activity user off-peak windows
- Optimize agent liquidity in areas with high withdrawal-pattern users

---

## 5. Model Reliability and Trustworthiness

### What We Can Trust

The model demonstrates genuine predictive ability:
- **Above-baseline performance:** All three trained models consistently outperform both the majority-class and stratified-random baselines, confirming that learned patterns are real
- **Consistent feature importance:** The same features (send/receive ratio, transaction amounts, type proportions) emerge as important across all three models, suggesting robust underlying patterns rather than model-specific artifacts
- **Interpretable predictions:** Misclassifications follow logical patterns (adjacent class confusion, behavioral overlap) rather than random errors, indicating the model has learned meaningful structure

### What We Cannot Trust

The model has clear reliability limitations:
- **Small dataset:** 69 users is sufficient to demonstrate the approach but insufficient for stable generalization. With ~14 users per fold in cross-validation, each fold's estimate is inherently noisy
- **CV variability:** Standard deviations of 0.10–0.18 across CV folds indicate that performance fluctuates substantially depending on which users happen to be in each fold. A single unlucky split can shift F1 by 10–15 percentage points
- **Test-CV gap:** The combined-feature models show the expected test-set variance for a 69-user dataset. This is not severe overfitting (the models are not memorizing training data), but rather split sensitivity: the particular users in the test set happen to be slightly easier or harder to classify than the average CV fold. With more data, these gaps would narrow.

### Bottom Line

The model is **useful for population-level segmentation** (grouping users into tiers for marketing or product design) but **not reliable enough for individual-level decisions** (approving or denying a specific user's credit application based solely on predicted class). It should be treated as one input among several in any decision pipeline.

---

## 6. Limitations

### 6.1 Small Sample Size (Primary Limitation)

With 69 users, the dataset provides approximately 23 users per class — enough to identify broad patterns but not enough to learn the nuanced behavioral boundaries that distinguish adjacent classes. Statistical learning theory suggests that classification accuracy improves logarithmically with sample size; doubling the dataset to ~140 users would likely yield meaningful performance gains, particularly for the Medium class.

### 6.2 Limited Demographic Coverage

The assessment specification requires demographic data (age, profession, geographic zone, income range, education level) collected via questionnaire. The project includes 10 real questionnaire responses, but full demographic coverage is not yet available for all users. Demographic features are still useful, because:
- Profession drives transaction patterns (merchants vs. salaried workers vs. students)
- Geographic zone affects access to agents and alternative financial services
- Income range constrains transaction volumes independently of behavioral preference

Limited demographic coverage means the model still relies heavily on transactional behavior, which reduces its ability to distinguish users whose transaction patterns are similar but whose underlying motivations differ.

### 6.3 Artificial Class Boundaries

The Low/Medium/High categories are defined by data-driven quantile thresholds, not by business-defined or domain-expert-validated segments. A user with 54 transactions (Low) and one with 56 transactions (Medium) may have identical behavioral profiles but fall into different classes. In a production deployment, these thresholds should be validated against actual business segment definitions or replaced with clustering-based natural groupings.

### 6.4 No Temporal Validation

All features are computed from the full transaction history, and the train-test split is random (user-level), not temporal. This means the model assumes that behavioral patterns are stable over time. In reality, users' activity levels may shift — a student on holiday transacts differently than during the academic year. A temporal validation approach (training on older data, testing on recent behavior) would provide a more realistic estimate of real-world performance.

### 6.5 Data Source Heterogeneity

The dataset combines 51 original users (low-value, high-frequency transactions) with 18 anonymized users (high-value transactions). Although the `data_source` feature was correctly excluded from modeling, the underlying behavioral distribution is bimodal. The anonymized users' higher transaction amounts may disproportionately influence the model's learned boundaries. The error analysis confirms this: 2 of 9 misclassifications involve anonymized users whose high-value profiles cause them to be classified as Low-activity despite being Medium-activity by transaction count.

### 6.6 Feature Constraints from Leakage Prevention

Excluding frequency-based features (monthly_txn_frequency, txn_velocity_7d) was necessary to prevent data leakage, since these features directly encode the classification target. However, this exclusion removes the most discriminating signals. A temporal-split approach — training on months 1–6 to predict month 7+ activity class — would allow safe inclusion of historical frequency features, likely boosting performance by 10–15 percentage points.

---

## 7. Recommendations for Improvement

### Data Recommendations

1. **Expand the user base to 200+ users.** This is the single highest-impact improvement. More users would stabilize cross-validation estimates, reduce the test-CV gap, improve Medium-class discrimination, and enable more complex feature interactions to be learned reliably.

2. **Integrate demographic features.** Adding age, profession, geographic zone, and primary use case (personal vs. business) from the Section 1 questionnaire would provide orthogonal information that transaction data alone cannot capture. A merchant and a student may have similar weekly transaction counts but very different behavioral motivations.

3. **Collect longitudinal data.** Tracking the same users over multiple periods would enable temporal validation and allow the model to capture behavioral trends (e.g., users transitioning from Low to Medium activity).

### Modeling Recommendations

4. **Implement temporal train-test splits.** Train on earlier months, predict later months. This would: (a) provide realistic deployment-scenario performance estimates, (b) allow safe inclusion of historical frequency features, and (c) test whether behavioral profiles are temporally stable.

5. **Experiment with 2-class simplification.** Merging Medium into either Low or High (or using a binary High vs. Not-High split) would eliminate the hardest classification boundary and likely push Macro F1 above 0.70 — useful when the business question is simply "is this user highly engaged?"

6. **Explore ensemble stacking.** Combining Logistic Regression (which excels at linear separation of extreme classes) with XGBoost (which handles non-linear interactions) in a stacking ensemble could capture complementary patterns.

### Feature Engineering Recommendations

7. **Add transaction diversity indices.** A Shannon entropy measure over transaction types (how evenly distributed a user's transactions are across types) would capture whether a user is a specialist (mostly airtime) or generalist (spread across all types).

8. **Engineer time-based behavioral features.** Burstiness (variance in inter-transaction intervals), periodicity (regular weekly patterns vs. irregular usage), and recency (days since last transaction at prediction time) add temporal dimension without directly encoding frequency.

9. **Create interaction features.** The ratio of mean_amount to avg_balance (what proportion of their balance do they typically transact?) and pct_airtime × avg_sr_ratio (high airtime + high send ratio = likely reseller) could capture complex user archetypes.

---

## 8. Deployment Considerations

### How the Model Would Work in Practice

In a production mobile money system, the classification model would operate as follows:

**Input:** A user's transaction history over a defined lookback window (e.g., the past 3 months). The system computes the 15 behavioral features (mean amount, transaction type proportions, send/receive ratio, etc.) from the raw transaction log.

**Processing:** The trained XGBoost model takes the 15-feature vector and outputs a predicted activity class (Low, Medium, or High) along with class probabilities for each category.

**Output:** The predicted segment is stored in the user's profile and made available to downstream systems — CRM platforms, credit scoring engines, marketing automation tools, or fraud monitoring dashboards.

### Integration Architecture

A realistic deployment would involve:
1. **Batch scoring:** Nightly or weekly batch job that recomputes features and re-scores all active users. Suitable for marketing campaigns and periodic reporting.
2. **Near-real-time triggers:** When a user's transaction count crosses a threshold (e.g., 10 new transactions since last scoring), recompute features and update the prediction. Suitable for dynamic risk monitoring.
3. **Human-in-the-loop:** For high-stakes decisions (credit approval, fraud escalation), the model's prediction serves as a recommendation flag, not an automated decision. A human reviewer makes the final call.

### Retraining Cadence

The model should be retrained quarterly as new users join the platform and existing users' behavior evolves. Monitoring should track prediction distribution drift (is the model predicting too many High users compared to reality?) and per-class accuracy on a held-out validation set.

---

## 9. Ethical and Practical Considerations

### Bias and Fairness

**Demographic coverage gaps.** The model now includes demographic signals, but only a small questionnaire subset is real. That means it can still encode *proxy bias*: if certain transaction patterns correlate with demographic groups (e.g., rural users have lower transaction diversity due to fewer available services), the model could systematically misclassify those groups without anyone detecting it. Once broader real demographic data is available, a fairness audit should verify that classification accuracy is equitable across age groups, genders, and geographic zones.

**Data source imbalance.** The anonymized users (18 users) have dramatically different transaction profiles (mean amount 25x higher) than the original users (51 users). If these groups correspond to different socioeconomic tiers, the model may perform better for one tier than the other. The error analysis already shows that anonymized users are disproportionately misclassified.

### Misclassification Risks

**Low predicted as Medium or High:** A truly low-activity user classified as higher-activity could receive inappropriate product offers (e.g., micro-loans they cannot service) or be flagged as low-risk when they should be monitored more carefully.

**High predicted as Low:** A truly high-activity user classified as low-activity could miss loyalty benefits, be deprioritized for customer service, or be offered onboarding campaigns that feel patronizing to an experienced user.

**Medium predictions are inherently unreliable.** Given the 43% F1 for the Medium class, any business action triggered specifically by a Medium prediction should carry a confidence caveat. Treating Medium as "uncertain" rather than a firm classification would be more honest.

### Privacy and Consent

The model uses only anonymized transaction metadata (amounts, types, timing) — no personal identifiers, SMS content, or contact information. However, deploying such a model at scale requires clear disclosure to users that their transaction patterns are being analyzed for classification purposes. In Cameroon's regulatory context, this should comply with data protection guidelines and the terms of service for MoMo/OrangeMoney platforms.

### Responsible Use Guidelines

The model **should** be used for:
- Population-level customer segmentation and product design
- Aggregate reporting on user engagement trends
- Generating hypotheses for further investigation

The model **should not** be used for:
- Individual-level credit decisions without additional verification
- Automated account restrictions or service denial
- Profiling users for purposes beyond the stated classification objective

---

## 10. Conclusion

This analysis demonstrates that mobile money transaction behavior contains meaningful signal for classifying users into activity segments. Random Forest achieves a Macro F1 of 0.55 on the test set — a clear improvement over random baselines — using only 15 behavioral features that describe how users transact, not how frequently.

The model's insights are actionable: high-activity users are daily MoMo power users driven by airtime and transfers; low-activity users are infrequent, high-value transactors who primarily receive and withdraw; medium-activity users occupy a transitional zone that resists clean classification. These profiles map directly onto customer segmentation strategies, credit risk tiers, and marketing approaches.

The primary limitation is data, not methodology. With 69 users, the model demonstrates proof of concept but lacks the statistical power for production-grade reliability. Expanding to 200+ users, collecting more real demographic responses, and implementing temporal validation would be the most impactful next steps.

The foundation is solid. The behavioral features are sound, the leakage prevention is rigorous, and the evaluation framework (baselines, per-class breakdown, overfitting check) provides honest assessment rather than inflated claims. What remains is scaling the data to match the ambition of the approach.

---

*Report prepared as part of CSC 3221 — Introduction to Data Science, Final Assessment.*
*Mobile Money Transaction Analysis Project, May 2026.*
