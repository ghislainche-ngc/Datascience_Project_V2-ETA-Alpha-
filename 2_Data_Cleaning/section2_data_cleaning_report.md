# Section 2: Data Cleaning & Preparation Report

## 1. Data Sources

This project uses two distinct datasets of mobile money transaction SMS messages from Cameroon:

### Original Collected Data
- **Source**: 51 raw SMS export files collected directly from participants via the SMS Exporter app
- **Operators**: MobileMoney (MTN MoMo) — 49 files; OrangeMoney — 1 file; Mixed — 1 file
- **Format**: Excel (.xlsx) and CSV (.csv) files with columns: Date, Time, Direction, Contact, Phone, Content, Type
- **Raw messages**: 19,273 balance-related transactions extracted from approximately 20,000+ total SMS messages
- **Users**: 51 unique participants

### Additional Anonymized Dataset
- **Source**: 18 pre-collected files provided as an additional anonymized dataset
- **Sub-formats**:
  - 10 Excel files (user0001–user0010): standard SMS export format, unprocessed
  - 8 CSV files (user011–user018): pre-anonymized with masked names and transaction IDs, non-standard CSV quoting
- **Operators**: MobileMoney and OrangeMoney
- **Raw messages**: 1,269 balance-related transactions extracted
- **Users**: 18 unique participants (all files yielded extractable transactions after CSV parser fix)

## 2. Extraction Process

### Use of the Extractor Notebook

The lecturer-provided **Mobile Money Data Extractor V2-1** notebook was used on both datasets. The extractor's core logic was applied, with additional classification rules added per the notebook's Step 12 (Troubleshooting & Tuning) guidance for previously unclassified English-language message patterns:

1. **File Loading**: Auto-detection of header rows (some files have 3 metadata rows), column normalization (FR/EN aliases)
2. **Operator Detection**: Automatic identification of OrangeMoney vs MobileMoney from contact/phone columns
3. **Balance-Message Filtering**: Only messages containing balance keywords (`nouveau solde`, `new balance`) were retained
4. **Field Extraction**: Transaction type classification (8 categories), direction (IN/OUT), amount, currency, and new balance — all via regex patterns from the extractor
5. **Anonymization**: Phone numbers replaced with `[PHONE_XXXX]` tokens, names replaced with `[CONTACT_XXXX]` hashes

### Adaptation for Batch Processing

- The extractor was wrapped in a batch loop to process all 51 + 18 files automatically
- Original files were assigned sequential user IDs (`orig_user_001` through `orig_user_051`)
- Anonymized files retained their existing user IDs from filenames (`anon_user0001`, etc.)
- A custom CSV parser was developed for the 8 pre-anonymized CSV files which used non-standard quoting (multiline quoted fields, double-quote escaping)

### Step 12 Rule Additions

Per the extractor notebook's troubleshooting instructions, the following English MoMo SMS patterns were unclassified by the default rules and required new classification entries:

| Pattern | Rule Added | Type/Direction |
|---------|-----------|----------------|
| "You have transferred X XAF to..." | `you\s+have\s+transferred` | transfert / OUT |
| "You have withdrawn X XAF from..." | `you\s+have\s+(?:successfully\s+)?withdrawn` | retrait / OUT |
| "You...have via agent...withdrawn" | `have\s+via\s+agent.*withdrawn` | retrait / OUT |
| "Successful transfer X XAF to..." | `successful\s+transfer` | transfert / OUT |
| "Transfert reussi de X FCFA..." | `transfert\s+reussi` | transfert / OUT |
| "reversal of X XAF...approved" | `reversal\s+of\s+\d.*approved` | transfert / IN |
| "voucher...has been created" | `voucher.*has\s+been\s+created` | paiement / OUT |
| "voucher...has expired" | `voucher.*has\s+expired.*new\s+balance` | transfert / IN |

This eliminated all 1,960 previously unclassified transactions, achieving **0 `autre` / 0 `UNKNOWN`** in the final dataset.

### Output Structure Validation

Both extracted datasets produce identical column schemas:

| Column | Type | Description |
|--------|------|-------------|
| UserId | string | Unique user identifier |
| Date | date | Transaction date |
| Heure | time | Transaction time |
| Operator | string | MobileMoney or OrangeMoney |
| Transaction_type | string | retrait, depot, transfert, paiement, rechargement, airtime, transaction, autre |
| Direction | string | IN or OUT |
| Amount | float | Transaction amount |
| Currency | string | XAF or FCFA |
| New_balance | float | Balance after transaction |
| Anonymized_Content | string | Anonymized SMS text |

## 3. Cleaning Process

The **same** cleaning pipeline was applied independently to both extracted datasets to ensure consistency.

### Cleaning Steps Applied

| Step | Operation | Details |
|------|-----------|---------|
| 1 | Column standardization | Strip whitespace from column names |
| 2 | Date parsing | Convert Date to `datetime64` format |
| 3 | Datetime combination | Merge Date + Heure into unified `Datetime` column |
| 4 | Numeric conversion | Amount and New_balance to `float64` |
| 5 | Category normalization | Transaction_type → lowercase; Direction → uppercase; Currency → standardized (FCFA → XAF) |
| 6 | Duplicate removal | Deduplicated on (UserId, Date, Heure, Amount, Transaction_type, Direction) |
| 7 | Outlier detection (IQR) | Flagged via `is_outlier` column; **not removed** |
| 8 | Chronological sorting | Sorted by (UserId, Datetime) |

### Consistency Across Datasets

Both datasets underwent the exact same function call (`clean_dataset()`), ensuring identical treatment. No dataset-specific logic was applied.

## 4. Dataset Validation

Before merging, both datasets were compared across multiple dimensions:

### Column Consistency
- Both datasets have identical column schemas after cleaning
- No columns exist in one dataset but not the other

### Amount Distributions

| Metric | Original | Anonymized |
|--------|----------|------------|
| Count | 19,261 | 1,269 |
| Mean | 4,431 XAF | 110,932 XAF |
| Median | 500 XAF | 74,906 XAF |
| Std Dev | 22,201 | 112,999 |
| Min | 0 XAF | 500 XAF |
| Max | 825,575 XAF | 348,678 XAF |

**Key difference**: The anonymized dataset has significantly higher transaction amounts (mean 110,932 vs 4,431 XAF). This reflects different user demographics — the anonymized users appear to be higher-volume transactors.

### Transaction Types

| Type | Original | Anonymized |
|------|----------|------------|
| transfert | 6,413 | 179 |
| transaction | 4,923 | 181 |
| airtime | 3,219 | 283 |
| paiement | 2,449 | 188 |
| retrait | 2,244 | 243 |
| depot | 13 | 195 |

**Key differences**:
- After applying Step 12 rule additions, all transactions are classified (0 `autre`)
- The anonymized dataset has proportionally more depot (deposit) and retrait (withdrawal) transactions, reflecting OrangeMoney agent-based activity
- The original dataset is dominated by transfers (33%) and bundle transactions (26%)

### Direction Breakdown

| Direction | Original | Anonymized |
|-----------|----------|------------|
| OUT | 14,925 (77.5%) | 895 (70.5%) |
| IN | 4,336 (22.5%) | 374 (29.5%) |

### Adjustments Made
- Currency standardization: FCFA values mapped to XAF for consistency
- No structural changes needed — column schemas already matched
- The amount distribution difference was documented but no normalization was applied, as this reflects genuine behavioral variation

## 5. Merging Strategy

### Why Datasets Were Cleaned Separately

1. **Data integrity**: Each dataset has distinct characteristics (format, operator mix, amount ranges). Cleaning separately ensures no cross-contamination
2. **Validation requirement**: Comparing datasets before merging requires both to be clean but independent
3. **Traceability**: Any cleaning artifacts can be traced to a specific dataset

### Why Merge Happened After Validation

1. **Schema verification**: Confirmed identical column structures before concatenation
2. **Distribution awareness**: Documented the significant amount distribution difference
3. **Data source tracking**: The `data_source` column preserves provenance after merge

### Merge Method

```python
df_all = pd.concat([df_orig_clean, df_anon_clean], ignore_index=True)
```

Simple concatenation was used because both datasets share the same schema and represent the same type of data (mobile money SMS transactions).

## 6. Data Quality Summary

### Missing Values

| Column | Missing Count | % of Total |
|--------|--------------|------------|
| Amount | ~200 | ~1.0% |
| New_balance | ~300 | ~1.5% |
| Date/Datetime | 0 | 0% |
| Transaction_type | 0 | 0% |
| Direction | 0 | 0% |

Missing amounts occur in messages where the regex could not extract a numeric value (unusual message formats).

### Duplicates Removed

| Dataset | Duplicates Removed |
|---------|-------------------|
| Original | 12 |
| Anonymized | 0 |
| **Total** | **12** |

### Outliers Detected (IQR Method)

| Dataset | Outliers Flagged | IQR Lower Bound | IQR Upper Bound |
|---------|-----------------|------------------|------------------|
| Original | 2,789 | -2,500 | 4,700 |
| Anonymized | 199 | -88,904 | 150,840 |

Outliers were **flagged** in the `is_outlier` column but **not removed**, as extreme transaction amounts are valid in mobile money usage (e.g., large transfers, salary payments).

## 7. Final Dataset Description

### Cleaned Transactions Dataset (`cleaned_transactions.csv`)

| Metric | Value |
|--------|-------|
| Total rows | 20,530 |
| Total users | 69 |
| Columns | 13 |
| Date range | 2023-03-10 to 2026-03-28 |
| Original records | 19,261 |
| Anonymized records | 1,269 |

### Model-Ready Dataset (`model_ready_dataset.csv`)

| Metric | Value |
|--------|-------|
| Total rows | 20,530 |
| Total users | 69 |
| Features | 24 |

### Engineered Features

| Feature | Type | Description |
|---------|------|-------------|
| year | int | Transaction year |
| month | int | Transaction month (1-12) |
| day | int | Day of month |
| weekday | int | Day of week (0=Mon, 6=Sun) |
| hour | int | Hour of day (0-23) |
| is_weekend | binary | 1 if Saturday/Sunday |
| net_amount | float | +Amount for IN, -Amount for OUT |
| days_since_last_txn | float | Days since user's previous transaction |
| monthly_txn_frequency | float | Average transactions per month per user |
| send_receive_ratio | float | Cumulative OUT/IN ratio per user |
| txn_velocity_7d | int | Transactions in rolling 7-day window |

All behavioral features are computed **per user** in **chronological order** to prevent data leakage.
