# Section 5: Model Interpretation, Business Insights & Recommendations

## Mobile Money Transaction Analysis — User Activity Classification

---

## 1. Key Findings from Modeling

Three classification models — Logistic Regression, Random Forest, and XGBoost — were trained to classify mobile money users into Low, Medium, or High activity levels using 29 features (15 behavioral + 14 demographic) from 69 users in Cameroon.

**Central finding:** Behavioral transaction features carry genuine predictive signal. XGBoost achieved a Test Macro F1 of 0.5702 using behavioral features alone, substantially above the majority-class baseline (0.1667) and stratified random baseline (0.3150).

**Demographic integration result:** Adding demographic features (age, gender, profession, education, income, geography) produced mixed results — Random Forest improved by +0.05 F1, while XGBoost slightly decreased by -0.04 F1. This is attributable to 59/69 demographics being simulated; with real data, demographic features would likely contribute more consistently.

**Practical implication:** A new user's first few transactions already contain signals about their likely long-term engagement level. Financial institutions can begin segmentation early, without waiting for months of transaction history.

---

## 2. Behavioral Insights from Feature Importance

### Three Distinct User Profiles

Feature importances from XGBoost and Random Forest, combined with Logistic Regression coefficients, reveal three behavioral archetypes:

**High-Activity Users (> 204 transactions)**
- Make many small-value, frequent transactions (negative LR coefficient for mean_amount)
- High send/receive ratio (avg_sr_ratio = strongest LR coefficient at +0.887) — primarily senders
- Dominated by airtime purchases and transfers
- Larger household sizes (+0.663 LR coefficient) — supporting family networks
- *Profile:* Daily mobile money power users treating the platform as an everyday financial utility

**Low-Activity Users (≤ 55 transactions)**
- Fewer but larger transactions (high avg_balance, +0.796 LR coefficient)
- Higher education levels (+0.449) — possibly salaried professionals using MoMo for specific purposes
- More transaction-type transactions (pct_transaction: +0.395)
- *Profile:* Infrequent, purpose-driven users who transact for specific needs rather than daily use

**Medium-Activity Users (56–204 transactions)**
- Moderate transaction amounts (median_amount: +0.711 LR coefficient)
- Mixed usage patterns with balanced transaction types
- Gender signal (male: +0.691) — potential business/personal split
- *Profile:* Regular but not daily users — a transitional group between casual and power users

### Top Predictive Features

| Rank | Feature | XGBoost | RF | Type |
|------|---------|---------|-----|------|
| 1 | pct_depot | 0.1035 | — | Behavioral |
| 2 | avg_sr_ratio | 0.0515 | 0.0752 | Behavioral |
| 3 | pct_transfert | 0.0550 | 0.0525 | Behavioral |
| 4 | mean_amount | 0.0505 | 0.0560 | Behavioral |
| 5 | avg_hour | — | 0.0794 | Behavioral |
| 6 | prof_Unemployed | 0.0461 | — | Demographic |
| 7 | education_ordinal | 0.0436 | — | Demographic |

Behavioral features dominate the top ranks, with demographic features providing secondary signal. The deposit percentage (pct_depot) emerged as the top XGBoost feature — users who receive deposits are behaviorally distinct from those who primarily send.

---

## 3. Why the Medium Class Is Hardest to Predict

The Medium class consistently has the lowest F1-score across all models (0.29–0.44). This is not a model failure but a fundamental characteristic of quantile-based classification:

1. **Boundary overlap:** Users near the 33rd and 66th percentile thresholds have behavioral profiles that blend with both adjacent classes. A user with 50 transactions (Low) looks nearly identical to one with 60 (Medium).

2. **Transitional behavior:** Medium users don't have a single dominant pattern — they combine elements of both Low (occasional large transactions) and High (regular smaller ones).

3. **Statistical compression:** With only ~22 Medium users in the dataset and 7 in the test set, a single misclassification shifts F1 by ~14%.

**Adjacent confusion dominates.** Misclassifications are primarily Low↔Medium and Medium↔High. The model rarely confuses Low with High, confirming that extreme classes have well-separated behavioral profiles.

---

## 4. Demographic Insights

### What Demographics Reveal

The LR coefficients and XGBoost feature importances identify demographic signals:

- **Profession matters:** Unemployed users (prof_Unemployed: 0.0461 XGBoost importance) and self-employed users (0.0454) show distinct activity patterns. Self-employed users likely use mobile money for business transactions, while unemployed users may rely on it for receiving transfers.

- **Education correlates with activity style:** Higher education (education_ordinal: 0.0436) is associated with Low activity — consistent with salaried professionals who make fewer but larger transactions.

- **Urban location:** geo_Urban (0.0398) indicates that urban users have different activity profiles, likely due to greater access to merchants and mobile money agents.

- **Household size drives High activity:** Larger households (LR coefficient +0.663 for High class) correlate with more transactions — supporting multiple family members via airtime and transfers.

### Demographic Limitations

The demographic signal is attenuated by simulation (59/69 users). Real-world deployment with genuine demographic data would likely show:
- Stronger profession-based segmentation (agents vs personal users)
- Income-based activity thresholds
- Geographic patterns tied to mobile money infrastructure density

---

## 5. Business Interpretation & Use Cases

### Use Case 1: Customer Segmentation

**Application:** Automatically classify new users into activity tiers within their first month of transactions.

| Segment | Typical User | Business Action |
|---------|-------------|----------------|
| **High** | Daily user, small transfers, airtime | Premium features, loyalty rewards, transaction fee discounts |
| **Medium** | Regular user, mixed patterns | Upgrade campaigns, personalized product suggestions |
| **Low** | Infrequent, large transactions | Re-engagement campaigns, simplified UX, education on more features |

### Use Case 2: Credit Risk Scoring

High-activity users demonstrate consistent financial engagement — a positive signal for micro-lending. The model's behavioral features (send/receive ratio, transaction diversity) provide complementary data to traditional credit scores.

### Use Case 3: Churn and Fraud Detection

- Low-activity users with declining transaction velocity may signal churn risk
- Sudden shifts between predicted and actual activity class can flag anomalous behavior
- Users misclassified by the model (e.g., predicted High but actually Low) may represent atypical behavior worth investigating

### Use Case 4: Targeted Marketing

The demographic–behavioral intersection enables precision marketing:
- Young, urban, self-employed High-activity users → business account products
- Older, educated Low-activity users → savings and investment products
- Students with moderate activity → airtime bundles and peer transfer promotions

---

## 6. Model Reliability Assessment

### Confidence Assessment

| Criterion | Assessment |
|-----------|-----------|
| Baseline exceeded | All 3 models beat both baselines |
| No data leakage | Frequency features excluded, verified |
| CV stability (LR) | F1m std = 0.165 — moderate |
| CV stability (RF) | F1m std = 0.088 — acceptable |
| CV stability (XGB) | F1m std = 0.135 — moderate |
| Test-CV gap | LR: -0.04 (stable), RF: +0.01 (stable), XGB: +0.20 (large) |

**Verdict:** The model is reliable enough for population-level segmentation and trend analysis. It is NOT reliable enough for individual-level decisions without human review. The XGBoost overfitting gap suggests results should be interpreted as directional rather than precise.

---

## 7. Limitations

1. **69-user dataset:** The fundamental constraint. Model reliability would improve substantially with 200+ users.

2. **Simulated demographics (85%):** Only 10/69 users have real questionnaire data. Demographic insights should be validated with complete survey data.

3. **Feature exclusion tradeoff:** Removing frequency-based features prevents leakage but limits maximum achievable performance. A temporal split approach could safely include these features.

4. **Quantile-based classes:** Thresholds are data-driven, not business-validated. In production, domain experts should define meaningful activity levels.

5. **No temporal validation:** Random train-test split doesn't reflect real-world deployment where the model predicts future behavior from historical data.

6. **Single-country context:** Patterns may not generalize beyond Cameroon's mobile money ecosystem.

---

## 8. Recommendations

### Data Collection (High Priority)
1. **Collect real demographics for all 69 users** via questionnaire completion
2. **Expand to 200+ users** to stabilize model performance
3. **Include temporal metadata** — user registration date, first/last transaction date

### Modeling Improvements
4. **Implement temporal split** — train on months 1-N, predict month N+1 activity class
5. **Explore feature engineering** — rolling averages, transaction diversity indices, time-between-transactions
6. **Consider binary classification** (Active vs Inactive) as a simpler, more robust alternative for small datasets

### Deployment Considerations
7. **Batch scoring** — classify users weekly or monthly, not per-transaction
8. **Human-in-the-loop** — flag uncertain predictions (Medium class) for manual review
9. **Model retraining** — retrain quarterly as user population grows and patterns evolve

---

## 9. Ethical Considerations

### Proxy Discrimination Risk
Demographic features (gender, geography, profession) can encode socioeconomic biases. A model that predicts "Low activity" for rural, unemployed users could lead to denial of financial products — reinforcing existing inequalities rather than expanding financial inclusion.

**Mitigation:** Use the model for *enhancing* service (offering tailored products to all segments) rather than *restricting* access (denying services to Low-activity users).

### Misclassification Impact
- Classifying a High-activity user as Low could result in inadequate service capacity
- Classifying a Low-activity user as High could lead to inappropriate product offers
- Medium-class misclassifications are least consequential due to the transitional nature of this segment

### Data Privacy
Demographic data (age, income, profession) is sensitive. Storage, processing, and model training must comply with Cameroon's data protection regulations and informed consent requirements.

### Responsible Use Guidelines
1. Never use activity classification as the sole basis for denying financial services
2. Ensure demographic features don't disproportionately disadvantage vulnerable populations
3. Provide transparency to users about how their transaction data informs service delivery
4. Regular fairness audits across demographic groups

---

## 10. Conclusion

This analysis demonstrates that mobile money transaction behavior carries genuine predictive signal for user activity classification. Behavioral features — particularly deposit frequency, send/receive ratio, transfer patterns, and transaction amounts — are the primary drivers, with demographic features providing secondary context.

The model achieves meaningful performance above baselines (XGBoost F1m = 0.57 vs baseline 0.17) but is limited by the 69-user dataset. The three identified user profiles (daily power users, purpose-driven occasional users, and transitional regular users) align with expected mobile money usage patterns in Cameroon and provide actionable segmentation for financial institutions.

**Next steps:** Expanding the dataset to 200+ users with complete real demographics would be the single highest-impact improvement, enabling both more reliable behavioral classification and genuine demographic-based insights.
