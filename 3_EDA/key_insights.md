# EDA Key Insights

## Main Patterns

- Transaction amounts are strongly right-skewed, which means the dataset is dominated by micro-transactions rather than large-value transfers.
- Outbound transactions make up the majority of activity, so spending behavior is more informative than purely inflow behavior.
- Transaction volume peaks in the evening, especially around 17:00-20:00, with a smaller morning peak.
- The original and anonymized user groups show noticeably different amount scales, suggesting distinct user populations or usage contexts.
- Time-based and ratio-based features separate user activity patterns better than raw totals alone.

## Hypotheses About Transaction Behavior

- Users with higher transaction counts likely perform smaller-value, more frequent transfers and airtime purchases.
- Profession and geographic zone likely influence transaction behavior through income access, business use, and service availability.
- Send/receive ratio and weekend activity are likely stronger predictors of user class than raw balances.
- Large-value users may be less frequent transactors but more likely to cluster in the Low or Medium class depending on count-based activity.

## Potential Predictive Features

- `txn_count`
- `mean_amount`
- `median_amount`
- `std_amount`
- `avg_balance`
- `avg_sr_ratio`
- `pct_airtime`
- `pct_depot`
- `pct_paiement`
- `pct_retrait`
- `pct_transfert`
- `avg_hour`
- `pct_weekend`
- `profession`
- `geo_zone`

## Why These Matter for Modeling

- These features capture how users transact, when they transact, and what type of transactions they prefer.
- They provide a strong basis for predicting the user activity class while avoiding direct leakage from target-defining frequency variables.
- They support the modeling goal by linking EDA patterns directly to classification features.
