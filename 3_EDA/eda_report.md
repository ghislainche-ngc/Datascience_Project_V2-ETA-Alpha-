# Section 3: Exploratory Data Analysis (EDA) Report

## Mobile Money Transaction Analysis — User Classification

---

## 1. Dataset Overview

| Metric | Value |
|--------|-------|
| Total transactions | 20,530 |
| Unique users | 69 (51 original + 18 anonymized) |
| Date range | 2023-03-10 to 2026-03-28 |
| Operators | MobileMoney (96.3%), OrangeMoney (3.7%) |
| Features | 24 columns (13 base + 11 engineered) |
| Missing values | New_balance: 57 (0.3%), days_since_last_txn: 69 (0.3%) |

The dataset was produced by the Section 2 cleaning pipeline from 51 original raw SMS export files and 18 pre-collected anonymized files. All transactions are classified into 6 types with 0 unclassified records.

---

## 2. Descriptive Statistics

### Numerical Variables

| Variable | Mean | Median | Std Dev | Skewness |
|----------|------|--------|---------|----------|
| Amount (XAF) | 7,454 | 500 | 33,702 | 12.7 |
| New_balance (XAF) | 20,362 | 2,653 | 59,199 | 6.4 |
| net_amount (XAF) | -4,148 | -300 | 30,038 | -8.7 |
| days_since_last_txn | 0.67 | 0.08 | 3.55 | 13.8 |
| monthly_txn_frequency | 35.5 | 22.8 | 54.2 | 5.1 |
| send_receive_ratio | 4.62 | 3.24 | 5.79 | 2.6 |
| txn_velocity_7d | 10.3 | 5.0 | 14.9 | 3.9 |

**Key observation:** All financial variables exhibit strong positive skewness, indicating the dataset is dominated by small, frequent transactions with a long tail of large-value operations.

### Categorical Distributions

| Transaction Type | Count | % |
|-----------------|-------|---|
| transfert | 6,592 | 32.1% |
| transaction | 5,104 | 24.9% |
| airtime | 3,502 | 17.1% |
| paiement | 2,637 | 12.8% |
| retrait | 2,487 | 12.1% |
| depot | 208 | 1.0% |

| Direction | Count | % |
|-----------|-------|---|
| OUT | 15,920 | 77.5% |
| IN | 4,610 | 22.5% |

---

## 3. Visualizations Summary

11 publication-quality visualizations were generated, exceeding the minimum requirement of 8:

| # | Visualization | Type | File |
|---|--------------|------|------|
| 1 | Distribution of Key Financial Variables | Histogram + KDE | `01_amount_distributions.png` |
| 2 | Box Plots of Transaction Amounts | Box plot | `02_amount_boxplots.png` |
| 3 | Monthly Transaction Volume Over Time | Time series (bar + line) | `03_monthly_time_series.png` |
| 4 | Hourly Transaction Distribution | Bar + area chart | `04_hourly_distribution.png` |
| 5 | Correlation Heatmap | Heatmap | `05_correlation_heatmap.png` |
| 6 | Categorical Variable Distributions | Bar charts (2x2) | `06_categorical_barcharts.png` |
| 7 | User-Level Relationship Exploration | Scatter plots | `07_scatter_relationships.png` |
| 8 | Grouped Comparisons | Grouped bar charts (2x2) | `08_grouped_comparisons.png` |
| 9 | Activity Heatmap (Hour x Day) | **Advanced**: Heatmap | `09_activity_heatmap.png` |
| 10 | User Classification Distribution | Bar + histogram + violin | `10_user_classification.png` |
| 11 | Class Balance & Per-Class Profile | Bar + grouped bar | `11_class_balance_check.png` |

All visualizations include proper titles, axis labels, legends, and formatted tick marks.

---

## 4. Key Insights (5 Patterns Identified)

### Insight 1: Predominantly Micro-Transactions with Extreme Skewness

The median transaction amount (500 XAF ~ $0.80 USD) is 15x smaller than the mean (7,454 XAF). With skewness > 12, the dataset is dominated by small airtime purchases and transfers, while a small number of large deposits and payments create the long tail. **Implication:** Transaction frequency is a more stable classification feature than raw amount.

### Insight 2: Spending-Dominant Behavior (77.5% Outbound)

Over three-quarters of all transactions are outgoing, driven by transfers (32%), bundle purchases (25%), and airtime (17%). Deposits account for only 1% of transactions. **Implication:** The send/receive ratio captures fundamental behavioral differences between net-senders and net-receivers.

### Insight 3: Strong Evening Peak (17:00-20:00) Across All Days

The activity heatmap reveals consistent peak transaction volume during post-work evening hours (17:00-20:00), with a secondary morning peak (09:00-12:00). Weekend activity accounts for ~29% of total volume. **Implication:** Temporal features (hour, weekday, is_weekend) carry meaningful behavioral signal.

### Insight 4: Distinct User Populations Between Data Sources

Anonymized users (18 users) transact with 25x higher mean amounts (110,932 XAF vs 4,431 XAF) but at lower frequency. Original users (51 users) show high-frequency, low-value patterns typical of personal mobile money use. **Modeling safeguard:** The `data_source` feature will be **excluded** from the classification model to ensure the classifier learns behavioral patterns rather than memorizing dataset identity. This prevents a shortcut that would not generalize to new users.

### Insight 5: Transaction Velocity Strongly Separates Activity Classes

High-activity users show dramatically higher 7-day rolling transaction velocity and monthly frequency compared to Low-activity users. These temporal activity metrics directly align with the classification target. **Note:** Because these features overlap with the target variable (total transaction count), they require careful handling during modeling to avoid data leakage (see Section 5 below).

---

## 5. User Classification Definition

### Methodology

Users were classified into three behavioral segments using **quantile-based thresholds** on total transaction count (per-user aggregation):

| Class | Threshold | Users | Avg Txn Count | Avg Monthly Freq |
|-------|-----------|-------|---------------|-----------------|
| **Low** | <= 33rd percentile (~55 txns) | ~23 | ~22 | ~8 |
| **Medium** | 34th-66th percentile (~55-204 txns) | ~23 | ~118 | ~24 |
| **High** | > 66th percentile (>204 txns) | ~23 | ~753 | ~83 |

### Why 3 Classes (Not 2 or 4)?

- **Business relevance:** Financial service providers typically segment users into casual, regular, and power tiers for marketing, credit scoring, and product design
- **Statistical balance:** Tercile-based splits produce approximately equal class sizes (~23 users each), avoiding class imbalance that would penalize minority-class prediction
- **2 classes** would lose the distinction between occasional and regular users; **4+ classes** would create groups too small (< 18 users) for reliable modeling with only 69 users

### Class Balance Verification

The class balance was explicitly verified (see Visualization 11):
- All three classes contain approximately equal numbers of users
- The per-class feature profiles show clear separation: High-activity users have higher monthly frequency but lower mean transaction amounts, while Low-activity users show higher individual transaction values but infrequent use

### Data Leakage Awareness

> **Important:** The classification target is based on total transaction count. Features like `monthly_txn_frequency` and `txn_velocity_7d` are derived from the same underlying quantity. In Section 4 (Modeling), this will be addressed by either:
> 1. Using a **temporal split** — train on historical data, predict future activity class
> 2. **Excluding direct leakage features** and using only behavioral profile features (mean_amount, send_receive_ratio, pct_weekend, etc.) that describe *how* a user transacts, not *how much*

---

## 6. Connection to Prediction Goal & Feature Recommendations

### Prediction Target

**User Activity Classification**: Predict whether a user falls into the Low, Medium, or High activity category based on their transaction history and behavioral features.

### Recommended Features (by priority, with leakage assessment)

| Priority | Feature | Rationale | Leakage Risk |
|----------|---------|-----------|--------------|
| High | mean_amount / median_amount | Transaction size profile | None |
| High | send_receive_ratio | Behavioral pattern indicator | None |
| High | avg_balance (New_balance) | Financial capacity proxy | None |
| Medium | pct_weekend | Lifestyle/usage pattern | None |
| Medium | std_amount | Transaction variability | None |
| Caution | monthly_txn_frequency | Activity level (overlaps target) | High — temporal split only |
| Caution | txn_velocity_7d | Recent intensity (overlaps target) | High — temporal split only |
| Exclude | data_source | Proxy for dataset identity | Shortcut — always exclude |
| Low | Operator | Limited signal (96% MobileMoney) | None |

### Hypotheses to Test in Modeling

1. Behavioral features (mean_amount, send_receive_ratio, pct_weekend) can classify users without frequency-based leakage features
2. Mean transaction amount alone is insufficient — it needs combination with other behavioral features
3. Send/receive ratio separates agents/merchants from personal users
4. Weekend activity proportion captures business vs personal use patterns

---

## 7. EDA Limitations

1. **No demographic data in current analysis.** The assessment requires demographic/contextual data (age, profession, zone, income) collected via questionnaire. Once Section 1 questionnaire responses are available, additional analyses should include activity by profession, zone, income range, and smartphone ownership.

2. **Skewed financial data.** All financial variables are heavily right-skewed (skewness > 10 for Amount). Log-transformations or robust scaling should be applied before modeling.

3. **Imbalanced data source representation.** Original data (51 users, 19,261 txns) vastly outweighs anonymized data (18 users, 1,269 txns). Per-user aggregation mitigates this, but transaction-level analyses are dominated by original-dataset patterns.

4. **Temporal coverage varies by user.** Some users have 3 months of data while others have up to 36 months. Features like `monthly_txn_frequency` partially normalize this, but users with short histories may have less stable profiles.

5. **Data leakage potential.** The classification target (total transaction count) overlaps with frequency-based features. Section 4 must address this through temporal splits or feature exclusion.
