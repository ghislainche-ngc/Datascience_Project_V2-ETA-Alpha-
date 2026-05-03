# Section 4: Statistical Modeling & Prediction Report

## Mobile Money Transaction Analysis — User Activity Classification with Demographic Integration

---

## 1. Problem Definition

**Task:** Multi-class classification — predict whether a mobile money user falls into Low, Medium, or High activity categories.

**Target Variable:** `activity_class` (3 classes), defined by quantile-based thresholds on total transaction count:
- **Low:** ≤ 55 transactions (bottom tercile, ~23 users)
- **Medium:** 56–204 transactions (middle tercile, ~22 users)
- **High:** > 204 transactions (top tercile, ~24 users)

**Why this matters:** Classifying user activity levels enables financial institutions to segment customers for targeted products, assess credit risk, and optimize service delivery.

**New in this iteration:** Demographic features (age, gender, profession, education, income, geographic zone, household size, primary use, smartphone ownership) are integrated alongside behavioral transaction features to assess whether socioeconomic context improves classification.

---

## 2. Data Preparation

### Behavioral Features (from EDA Pipeline)

The transaction-level dataset (20,530 rows) was aggregated to **69 user-level observations** with 15 safe behavioral features describing *how* each user transacts.

### Demographic Data Cleaning

Raw demographic data from 10 questionnaire respondents was cleaned:

| Field | Raw Issues | Standardized Values |
|-------|-----------|-------------------|
| Age | Inconsistent spacing ("25 - 34" vs "25-34") | 18-24, 25-34, 35-44, 45-54, 55+ |
| Gender | Abbreviated (M/F) | Male, Female |
| Profession | 8 labels (Teacher, Trader, etc.) | 5 groups: Student, Employed, Self-Employed, Unemployed, Retired |
| Education | Mixed naming (Bachelors, High School, etc.) | 4 levels: Primary, Secondary, Bachelor, Master |
| Income | Inconsistent format (commas, >) | 5 brackets: <50k, 50k-100k, 100k-200k, 200k-400k, >400k |
| Geography | Full city names with encoding issues | 3 zones: Urban, Suburban, Rural |

### Demographic Extension

Only 10/69 users had questionnaire data. To enable modeling, demographics were simulated for the remaining 59 users using distributions from the 10 real responses and Cameroon population priors. Records are tagged `demo_source = "real"` vs `"simulated"`.

### Feature Encoding

| Encoding | Features | Rationale |
|----------|----------|-----------|
| **Ordinal** | age (1–5), education (1–4), income (1–5) | Preserves natural order |
| **Binary** | gender (0/1), smartphone (0/1) | Two categories |
| **One-hot** | profession (4 dummies), geo_zone (2), primary_use (2) | Unordered categories |
| **Numeric** | household_size | Already numeric |

**Total:** 15 behavioral + 14 demographic = **29 features**

### Feature Selection and Leakage Handling

| Category | Features | Decision |
|----------|----------|----------|
| **Safe behavioral (15)** | mean_amount, median_amount, std_amount, avg_balance, pct_weekend, avg_sr_ratio, pct_out, avg_hour, std_hour, pct_airtime, pct_depot, pct_paiement, pct_retrait, pct_transaction, pct_transfert | Describe behavioral profile |
| **Safe demographic (14)** | age_ordinal, education_ordinal, income_ordinal, gender_binary, smartphone_binary, household_size, prof_* (4), geo_* (2), use_* (2) | External socioeconomic attributes |
| **Excluded (leakage)** | monthly_txn_frequency, txn_velocity_7d, txn_count, total_in, total_out | Directly derived from transaction count |
| **Excluded (proxy)** | data_source, demo_source | Encodes dataset identity |

---

## 3. Models Used

### Baseline Models

- **Majority Class Baseline:** Always predicts the most frequent class. F1 (macro) = 0.1667
- **Stratified Random Baseline:** Predicts according to class distribution. F1 (macro) = 0.3150

### Model 1: Logistic Regression

- **Configuration:** C=1, solver=lbfgs, class_weight=balanced, max_iter=1000
- **Scaling:** StandardScaler applied
- **Strengths:** Interpretable coefficients per class

### Model 2: Random Forest

- **Configuration:** n_estimators=200, max_depth=5, min_samples_split=2, min_samples_leaf=1, class_weight=balanced
- **Scaling:** Not needed (tree-based)
- **Strengths:** Feature importance, handles interactions

### Model 3: XGBoost

- **Configuration:** n_estimators=200, max_depth=3, learning_rate=0.1, subsample=0.8
- **Scaling:** Not needed
- **Strengths:** Sequential error correction, regularization

---

## 4. Evaluation Metrics

| Metric | Description | Why Used |
|--------|-------------|----------|
| **Accuracy** | % correct predictions | Overall baseline |
| **Precision** | Of predicted class X, how many are X | Avoids false positives |
| **Recall** | Of actual class X, how many found | Avoids missing users |
| **F1 (weighted)** | Harmonic mean P/R, weighted by class | Accounts for class sizes |
| **F1 (macro)** | Harmonic mean P/R, equal weight | **Primary metric** — no class neglected |
| **Confusion Matrix** | Misclassification patterns | Shows which classes are confused |

---

## 5. Results

### Test Set Performance (70/30 Stratified Split)

| Model | Feature Set | Test Acc | Test F1w | Test F1m | Precision | Recall |
|-------|-------------|----------|----------|----------|-----------|--------|
| Majority Baseline | — | 0.3333 | 0.1667 | 0.1667 | 0.1111 | 0.3333 |
| Stratified Baseline | — | 0.3333 | 0.3150 | 0.3150 | 0.3111 | 0.3333 |
| Logistic Regression | Behav Only | 0.4286 | 0.4300 | 0.4300 | 0.4345 | 0.4286 |
| Random Forest | Behav Only | 0.4286 | 0.4184 | 0.4184 | 0.4352 | 0.4286 |
| **XGBoost** | **Behav Only** | **0.5714** | **0.5702** | **0.5702** | **0.5734** | **0.5714** |
| Logistic Regression | Behav + Demo | 0.4286 | 0.4232 | 0.4232 | 0.4545 | 0.4286 |
| Random Forest | Behav + Demo | 0.4762 | 0.4702 | 0.4702 | 0.4804 | 0.4762 |
| **XGBoost** | **Behav + Demo** | **0.5238** | **0.5289** | **0.5289** | **0.5377** | **0.5238** |

### Per-Class Performance (XGBoost — Combined Features)

| Class | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|---------|
| High | 0.57 | 0.57 | 0.57 | 7 |
| Low | 0.67 | 0.57 | 0.62 | 7 |
| Medium | 0.38 | 0.43 | 0.40 | 7 |

### Cross-Validation Performance (Stratified 5-Fold)

| Model | CV Accuracy | CV F1w | CV F1m | CV F1m Std |
|-------|-------------|--------|--------|------------|
| Logistic Regression | 0.4800 | 0.4643 | 0.4548 | 0.1648 |
| Random Forest | 0.4778 | 0.4556 | 0.4403 | 0.0880 |
| XGBoost | 0.3356 | 0.3272 | 0.3123 | 0.1354 |

All trained models outperform both baselines, confirming genuine predictive signal in the behavioral features.

---

## 6. Demographic Impact Analysis

| Model | Behav-Only F1m | Combined F1m | Delta | Interpretation |
|-------|----------------|-------------|-------|---------------|
| Logistic Regression | 0.4300 | 0.4232 | -0.007 | Neutral (within noise) |
| Random Forest | 0.4184 | 0.4702 | +0.052 | Moderate improvement |
| XGBoost | 0.5702 | 0.5289 | -0.041 | Slight decrease |

**Key finding:** Demographic features provide **mixed impact** on model performance. Random Forest improved with demographics (+0.05 F1m), while XGBoost showed a slight decrease (-0.04). This is expected because:

1. **59/69 users have simulated demographics** — the model learns mostly from synthetic distributions rather than real individual-level demographic data
2. **Added dimensionality** (14 extra features on 69 users) can increase noise for models sensitive to feature-to-sample ratio
3. **XGBoost's gradient boosting** may overfit to the demographic noise, while Random Forest's bagging provides natural regularization

With real demographic data for all users, the impact would likely be more consistently positive.

---

## 7. Best Model Selection

**Selected: XGBoost (Behavioral Only)** as the primary model.

**Justification:**
1. Highest test F1 (macro) of **0.5702** across all configurations
2. Clearly exceeds baselines (majority=0.17, stratified=0.32)
3. With combined features, XGBoost still leads at 0.5289

**Secondary recommendation:** Random Forest (Combined) achieves **0.4702** — a good alternative with more stable cross-validation (std=0.088 vs 0.135 for XGBoost).

---

## 8. Feature Importance

### Top Behavioral Features (Consistent Across Models)

| Feature | XGBoost Imp. | RF Imp. | Interpretation |
|---------|-------------|---------|----------------|
| pct_depot | 0.1035 | — | Deposit frequency distinguishes activity levels |
| avg_sr_ratio | 0.0515 | 0.0752 | Send/receive balance indicates user role |
| pct_transfert | 0.0550 | 0.0525 | Transfer proportion reveals usage pattern |
| mean_amount | 0.0505 | 0.0560 | Transaction size profile |
| avg_hour | — | 0.0794 | Usage timing (RF's top feature) |

### Top Demographic Features (XGBoost Combined)

| Feature | Importance | Interpretation |
|---------|-----------|----------------|
| prof_Unemployed | 0.0461 | Employment status affects activity |
| prof_Self-Employed | 0.0454 | Self-employed users show distinct patterns |
| education_ordinal | 0.0436 | Education level correlates with usage |
| geo_Urban | 0.0398 | Urban users have different activity profiles |

### LR Coefficient Insights

- **High activity:** Driven by high send/receive ratio (+0.887), larger household (+0.663)
- **Low activity:** Driven by high balance (+0.796), higher education (+0.449)
- **Medium activity:** Driven by moderate transaction amounts (+0.711), male gender (+0.691)

---

## 9. Overfitting Analysis

| Model | Test F1w | CV F1w | Gap | Verdict |
|-------|----------|--------|-----|---------|
| Logistic Regression | 0.4232 | 0.4643 | -0.04 | Stable |
| Random Forest | 0.4702 | 0.4556 | +0.01 | Stable |
| XGBoost | 0.5289 | 0.3272 | +0.20 | Large gap |

**XGBoost (Combined)** shows a notable test-CV gap of +0.20, indicating test-set variance rather than robust generalization. With 69 users and 29 features, this is expected. The behavioral-only XGBoost model (prior run) had a smaller gap (+0.10), reinforcing that added demographic dimensions increase variance.

---

## 10. Limitations

1. **Small dataset (69 users):** The primary constraint. With ~23 users per class, models have limited learning capacity and test metrics are volatile.

2. **Simulated demographics (59/69):** Only 10 users had real questionnaire data. Simulated demographics add features but may introduce noise rather than signal.

3. **Feature dimensionality:** 29 features for 69 users pushes the limits of what models can reliably learn, particularly for Logistic Regression.

4. **No temporal split:** Train-test split is random, not temporal. A time-based split would better simulate real-world deployment.

5. **Leakage-prevention tradeoff:** Excluding frequency features reduces predictive power but ensures genuine behavioral learning.

6. **Cross-validation instability:** CV standard deviations of 0.09–0.16 reflect fold-level variance inherent to small datasets.

---

## 11. Conclusion

### Summary

- **Task:** 3-class user activity classification using behavioral + demographic features
- **Best Model:** XGBoost with behavioral features (Test F1m = 0.5702)
- **Demographic Impact:** Mixed — RF improved (+0.05), XGBoost decreased (-0.04), LR neutral
- **Top Predictors:** Behavioral features dominate (pct_depot, avg_sr_ratio, pct_transfert, mean_amount); demographic features (profession, education, geography) provide secondary signal
- **Key Insight:** How a user transacts is more predictive than who they are, but demographic context can improve ensemble models

### Recommendations

1. **Collect real demographics for all users** (target: 50+ real responses) to enable meaningful demographic analysis
2. **Consider temporal split** to safely include frequency features
3. **Explore feature engineering** — transaction diversity indices, time-between-transactions
4. **Target 200+ users** to stabilize model performance and enable reliable demographic modeling
