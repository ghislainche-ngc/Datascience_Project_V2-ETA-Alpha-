# Mobile Money Transaction Analysis Project Report

**Course:** CSC 3221 - Introduction to Data Science  
**Assessment:** Final Examination Project  
**Topic:** Mobile Money Transaction Analysis in Cameroon  
**Target:** User Activity Classification (Low / Medium / High)  
**Report format:** 8-12 pages excluding appendices

---

## 1. Executive Summary

This project analyzes 20,530 mobile money transaction records from 69 users in Cameroon and classifies users into Low, Medium, and High activity tiers. The analysis follows the assessment brief in [../Final_Assessment_IDS_2026.md](../Final_Assessment_IDS_2026.md) and the section deliverables in Sections 2 to 6.

The strongest overall model on the same 70/15/15 split is the **behavioral-only Random Forest** model, which achieved a **test macro F1 of 0.5476**. This result is clearly above the majority baseline (0.1429) and stratified baseline (0.2804). Behavioral-only XGBoost also performs well (test macro F1 of 0.4497). When demographic augmentation is introduced, Logistic Regression improves modestly to 0.2545, but Random Forest and XGBoost decline to 0.3611. This indicates that the transaction behavior itself is the most reliable source of predictive signal, while the demographic data currently contributes limited and mixed value because only 10 questionnaire responses are fully observed and the remaining demographic rows are proxy-augmented.

The main findings are:
- Mobile money behavior is strongly predictive of user activity segment.
- Random Forest on behavioral features is the best overall model in this dataset.
- Demographic augmentation helps linear modeling slightly, but does not improve the tree-based models.
- High-activity users are characterized by frequent small-value transfers, airtime, and strong send/receive imbalance.
- Medium activity remains the hardest class because it sits between two overlapping behavioral extremes.

Primary recommendation: use the behavioral-only Random Forest model for segmentation, and expand the real demographic survey coverage before relying on demographics for model improvement.

---

## 2. Introduction

### Background and Motivation

Mobile money platforms such as MTN Mobile Money and Orange Money are deeply embedded in everyday financial life in Cameroon. Transaction records provide a rich behavioral trace that can support customer segmentation, service design, risk assessment, and financial inclusion analysis. In this project, the goal is to use mobile money transaction history to classify users into behavioral activity segments.

### Problem Definition

The prediction task is **user classification**: assign each user to Low, Medium, or High activity based on transaction history. The classes were defined from total transaction count using quantile thresholds so that each class contains roughly the same number of users. This creates a balanced multi-class classification problem rather than an artificial majority-class prediction task.

### Scope and Limitations

The project uses 69 users, which is enough to demonstrate the analytical workflow but small for stable machine learning. The model also has strict leakage prevention rules: direct frequency features such as monthly transaction frequency and 7-day velocity are excluded from training because they overlap with the target definition. Demographic data is included, but only 10 questionnaire responses are real; the remaining demographic rows are proxy-augmented to preserve the modeling sample.

### Research Questions

- Can behavioral transaction features classify users into activity tiers?
- Which models perform best on this small, imbalanced-by-structure classification problem?
- Do demographic features improve classification performance?
- Which features are most predictive and why?

---

## 3. Data Collection Methodology

### Sampling Strategy

The raw transaction data came from two groups:
- 51 original participants from raw SMS exports
- 18 anonymized participants from a separate pre-collected dataset

This yields 69 unique users and 20,530 transactions after cleaning and extraction.

### Data Sources and Variables

The project uses:
- Transaction date and time
- Transaction type and direction
- Transaction amount and balance
- Derived behavioral features such as average amount, send/receive ratio, weekly timing, weekend usage, and transaction variability
- Demographic questionnaire variables: age, gender, profession, education, income range, zone, household size, primary use, and smartphone ownership

### Ethical Considerations

The analysis uses anonymized identifiers only. No names or phone numbers are retained in the modeling datasets. The project also separates transaction behavior from personally identifying data. Because only a limited number of questionnaire responses were collected, demographic augmentation is treated as a proxy layer and not as a substitute for full survey coverage.

### Data Quality Assessment

The cleaning pipeline standardized dates, currency labels, transaction categories, and categorical formats. Outliers were flagged rather than removed because large transfers and withdrawals are valid mobile money behaviors. The extracted data contains no unclassified transaction types after rule tuning.

---

## 4. Exploratory Data Analysis

The EDA deliverable is documented in [../3_EDA/eda_report.md](../3_EDA/eda_report.md) and the notebook in [../3_EDA/exploratory_analysis.ipynb](../3_EDA/exploratory_analysis.ipynb). The section includes 11 publication-quality visualizations, exceeding the minimum required 8.

### Key Descriptive Patterns

- Transaction amounts are heavily right-skewed.
- Outbound transactions dominate the dataset.
- Evening activity peaks between 17:00 and 20:00.
- Different data sources show different value patterns.
- Time-based intensity features are strongly aligned with the eventual activity classes.

### Visual Storytelling

The EDA is organized from univariate summaries to relationship plots, then to activity heatmaps and class-balance checks. That structure supports a clear story: mobile money usage is dominated by small, frequent outgoing transactions, and temporal patterns plus ratio features are more informative than raw amounts alone.

### Most Important Insights

1. Micro-transactions dominate the system.
2. Outbound activity is far more common than inbound activity.
3. Evening usage is a stable cross-day pattern.
4. The original and anonymized user groups differ materially in transaction magnitude.
5. Frequency-based features are powerful but must be handled carefully to avoid leakage.

### EDA Deliverables

- EDA notebook with charts and markdown explanations
- EDA summary report with embedded visualizations
- Key insights document

---

## 5. Modeling Approach

The modeling workflow is documented in [../4_Modeling/modeling.ipynb](../4_Modeling/modeling.ipynb), with the implementation scripts in [../4_Modeling/build_modeling_notebook.py](../4_Modeling/build_modeling_notebook.py) and [../4_Modeling/run_pipeline.py](../4_Modeling/run_pipeline.py).

### Target and Evaluation Setup

The target variable is a 3-class user activity label. The data is split into **70% train, 15% validation, and 15% test** using stratified sampling. This is a better fit for the assessment brief than a single 70/30 split because it preserves a separate validation holdout and a final test holdout.

### Models Trained

Three models were trained in both behavioral-only and behavioral-plus-demographic configurations:
- Logistic Regression
- Random Forest
- XGBoost

A majority-class baseline and a stratified-random baseline were also computed.

### Same-Split Performance Summary

Behavioral-only results:
- Logistic Regression: test macro F1 = 0.1693
- Random Forest: test macro F1 = 0.5476
- XGBoost: test macro F1 = 0.4497

Behavioral + demographic proxy results:
- Logistic Regression: test macro F1 = 0.2545
- Random Forest: test macro F1 = 0.3611
- XGBoost: test macro F1 = 0.3611

### Model Selection Rationale

The strongest overall performer is **behavioral-only Random Forest**. It remains well above the baselines and is more stable than the combined tree-based models in this small sample. The combined Logistic Regression model does improve relative to its behavioral-only version, which suggests the demographic variables carry some signal, but not enough to improve the stronger tree-based models on this dataset.

### Feature Importance and Leakage Control

The strongest predictors are behavioral: deposit frequency, send/receive ratio, transfer proportion, mean amount, and transaction timing. Leakage-prone features such as monthly transaction frequency and 7-day velocity are excluded from the final model.

---

## 6. Results and Interpretation

### Best Model Performance

The best model is the behavioral-only Random Forest with test macro F1 of 0.5476. That score is meaningfully above both baselines and demonstrates a usable, though not production-ready, classification signal.

### Interpretation of the Learned Patterns

- High-activity users behave like daily mobile money power users: frequent small transfers, airtime purchases, and broader usage spread.
- Low-activity users tend to transact less often but with larger values and stronger balance retention.
- Medium-activity users are the hardest to classify because they sit between the two extremes and often resemble one class or the other.

### Example Predictions and Errors

The error analysis shows that misclassifications are usually between adjacent classes, not between the extremes. For example, a Medium user with a high-value, low-frequency pattern may be classified as Low because their behavior resembles the Low-activity profile. Conversely, users near the Medium/High boundary may be classified as High if their usage intensity is elevated.

### Business Meaning

The model can support segmentation and product targeting. The strongest signal is behavioral, so institutions should focus on transaction-pattern features when designing early-stage segmentation logic.

---

## 7. Business Insights and Recommendations

### Recommended Actions

1. Use the behavioral Random Forest model for population-level segmentation.
2. Target High-activity users with loyalty, retention, and premium service offers.
3. Target Low-activity users with onboarding, education, and adoption prompts.
4. Treat Medium users as a transitional segment that may require human review or additional monitoring.

### Practical Implications

The model is best used for marketing segmentation, service personalization, and exploratory customer analytics. It should not be used alone for high-stakes credit decisions or automated service denial.

### Expected Benefits

If deployed carefully, the model can help service providers tailor offerings, identify engagement trends, and improve user experience while maintaining transparency and fairness.

---

## 8. Limitations, Ethics, and Future Work

### Limitations

- Only 69 users are available.
- Demographic coverage is limited; only 10 questionnaire responses are real.
- The split-based evaluation remains volatile because the test set is small.
- Proxy demographic augmentation can add noise rather than true signal.

### Ethics and Bias

Demographic features may encode socioeconomic bias if they are used without fairness checks. The model should be monitored for uneven error rates across age, gender, and geographic zone. Transaction behavior can also act as a proxy for socioeconomic position, so caution is required when interpreting predictions.

### Future Work

- Collect more real questionnaire responses.
- Expand the dataset to at least 200 users.
- Try a temporal validation design.
- Explore binary or hierarchical classification if the three-class boundary remains unstable.
- Engineer richer behavioral diversity features.

---

## 9. Conclusion

This project shows that mobile money transaction behavior is predictive of user activity class. The strongest model is the behavioral-only Random Forest, while demographic augmentation provides mixed benefit and only helps Logistic Regression in this small-sample setting. The findings are useful for segmentation and product design, but the project remains constrained by sample size and incomplete demographic coverage.

The workflow meets the assessment objectives: data extraction and cleaning, EDA, model training and evaluation, interpretation, and presentation preparation. The main next step is better data coverage, especially real demographic responses and a larger user sample.

---

## References

- [../Final_Assessment_IDS_2026.md](../Final_Assessment_IDS_2026.md)
- [../2_Data_Cleaning/section2_data_cleaning_report.md](../2_Data_Cleaning/section2_data_cleaning_report.md)
- [../3_EDA/eda_report.md](../3_EDA/eda_report.md)
- [../4_Modeling/section4_modeling_report.md](../4_Modeling/section4_modeling_report.md)
- [../5_Interpretation/section5_interpretation_report.md](../5_Interpretation/section5_interpretation_report.md)
- [../5_Interpretation/section5_insights.md](../5_Interpretation/section5_insights.md)
- [../6_Presentation/build_presentation.py](../6_Presentation/build_presentation.py)

---

## Appendices

- Consent form template
- Data collection questionnaire
- Additional visualizations
- Code and notebook artifacts

*End of report.*