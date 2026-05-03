# FACULTY OF INFORMATION AND COMMUNICATION TECHNOLOGIES

## FALL 2025

## FINAL EXAMINATION

| | |
|---|---|
| **COURSE TITLE:** | Introduction to Data Science |
| **COURSE CODE:** | CSC 3221 |
| **INSTRUCTOR:** | Dr. Fotsing Kuetche |
| **DATE:** | |

---

# Final Assessment: Complete Data Science Project — Mobile Money Transaction Analysis

**Assessment Type:** Group Project, Report & Presentation  
**Group Size:** 5 students per group  
**Submission Deadline:** Sunday, 3rd May, 2026 11:59 PM WAT  
**Submission Format:** Submit a .zip file (see "Submission Instructions" below)

---

## Context

Mobile money services (MTN Mobile Money, Orange Money) have transformed financial transactions in Cameroon and across Africa. Understanding transaction patterns can help:

- Financial institutions assess credit risk
- Service providers improve user experience
- Businesses optimize payment solutions
- Regulators monitor financial inclusion

---

## Your Task

Analyze mobile money transaction patterns to **predict user behavior** or **classify user segments** based on transaction history and demographic characteristics.

**Possible Prediction Targets** (choose ONE):

1. **Transaction Volume Prediction:** Predict next month's transaction volume/amount
2. **User Classification:** Classify users into behavioral segments (e.g., high/medium/low activity)
3. **Credit Risk Assessment:** Estimate creditworthiness based on transaction patterns
4. **Custom Problem:** Propose and justify your own prediction target (requires instructor approval)

---

## Learning Outcomes

By completing this assessment, you will demonstrate the ability to:

- **Collect** real-world data ethically and systematically, ensuring data quality and privacy
- **Clean and wrangle** messy, real-world data using appropriate techniques
- **Explore** data using descriptive statistics and effective visualizations
- **Apply** statistical methods and machine learning algorithms to make predictions
- **Evaluate** model performance using appropriate metrics and validation techniques
- **Communicate** data science findings clearly to both technical and non-technical audiences
- **Collaborate** effectively in a team environment, managing a complex analytical project
- **Practice** ethical data science, including privacy protection and bias awareness

---

## Assessment Components

### 1. Data Collection (10 points)

#### Requirements

**A. Sample Size:**
- **50 individuals minimum** per group (10 persons per student × 5 students)
- Must be diverse (different ages, professions, zones)
- Voluntary participation with informed consent

**B. Transaction Data (Primary Data):**

Collect **3 to 12 months** of mobile money transaction history including relevant transaction fields.

**C. Demographic & Contextual Data (Primary Data):**

Collect through questionnaire:
- Age / Age range
- Gender
- Profession / Occupation category
- Education level
- Monthly income range (optional, can be broad categories)
- Geographic zone (urban/suburban/rural; specific neighborhood/district)
- Household size
- Primary use of mobile money (personal, business, both)
- Smartphone ownership (yes/no)

**D. Ethical & Privacy Requirements:**

- **Informed Consent:** Create and use a consent form explaining:
  - Purpose of data collection
  - What data will be collected
  - How data will be used and protected
  - Right to withdraw
  - Anonymization guarantee
- **Anonymization:** Assign unique IDs (e.g., USER_001) to replace names/phone numbers
- **Data Security:** Store data securely, do not share publicly
- **No Harm:** Ensure participants face no risks from participation

#### Deliverables
- Raw anonymized dataset (CSV/Excel)
- Consent form template (PDF)
- Data collection questionnaire (PDF)
- Data collection report (1 page): sampling strategy, challenges, quality assurance

---

### 2. Data Cleaning & Preparation (10 points)

#### Requirements

**A. Data Quality Assessment:**
- Identify and document all data quality issues (missing values, outliers, inconsistencies, errors)
- Create data quality report with statistics (% missing per variable, outlier counts, etc.)

**B. Data Cleaning Operations:**
- Handle missing values (justify deletion vs. imputation approach)
- Remove or correct erroneous entries
- Standardize formats (dates, currency, categories)
- Remove duplicates
- Handle outliers (identify method: IQR, Z-score; justify treatment)

**C. Feature Engineering:**

Create meaningful derived variables, such as:
- Average transaction amount per month
- Transaction frequency (transactions per week/month)
- Send/Receive ratio
- Weekend vs. weekday activity
- Time since last transaction
- Transaction velocity (change over time)
- Any domain-specific features you identify

**D. Data Transformation:**
- Encode categorical variables appropriately
- Scale/normalize numerical features if needed for your models
- Create train/validation/test splits (e.g., 70/15/15 or 80/20)

#### Deliverables
- Cleaned dataset (CSV)
- Data cleaning script (Python/R notebook with detailed comments)
- Data cleaning report (2 pages):
  - Issues found and solutions applied
  - Features engineered and rationale
  - Summary statistics before/after cleaning

---

### 3. Exploratory Data Analysis (EDA) (15 points)

#### Requirements

**A. Descriptive Statistics:**
- Summary statistics for all key variables
- Distribution analysis (mean, median, std dev, skewness)
- Cross-tabulations for categorical variables

**B. Visualizations (Minimum 8 diverse charts):**

Must include:
1. Distribution plots (histograms/density plots) for key numerical variables
2. Box plots showing outliers and spread
3. Time series plots (transaction patterns over time)
4. Correlation heatmap (relationships between numerical variables)
5. Bar charts for categorical variables (profession, zone, transaction types)
6. Scatter plots exploring relationships (e.g., income vs. transaction volume)
7. Grouped comparisons (e.g., transaction behavior by profession or zone)
8. At least ONE advanced visualization (geographic map, network graph, interactive plot, etc.)

**C. Key Insights:**
- Identify at least **5 meaningful patterns** from your EDA
- Formulate hypotheses about what drives transaction behavior
- Identify potential predictive features

**D. Data Storytelling:**
- Visualizations should be publication-quality (proper labels, titles, legends)
- Include interpretations with each visualization
- Connect findings to your prediction goal

#### Deliverables
- EDA notebook (Python/R with markdown explanations)
- EDA summary report (2-3 pages with embedded visualizations)
- Key insights document (bullet points highlighting discoveries)

---

### 4. Statistical Modeling & Prediction (25 points)

#### Requirements

**A. Problem Formulation:**
- Clearly state your prediction target
- Justify why this prediction is valuable
- Define success criteria and metrics

**B. Baseline Model:**
- Create a simple baseline (e.g., mean prediction, most frequent class)
- Establish performance benchmark to beat

**C. Model Development:**

**Minimum Requirement:** Train and evaluate **at least 3 different models**

Suggested Models (choose 3+):
- Linear Regression (for continuous predictions)
- Logistic Regression (for binary classification)
- Decision Trees
- Random Forest
- Gradient Boosting (XGBoost, LightGBM)
- K-Nearest Neighbors (KNN)
- Support Vector Machines (SVM)
- Naive Bayes (for classification)

**D. Model Training Process:**
- Use proper train/validation/test splits
- Apply cross-validation where appropriate
- Tune hyperparameters systematically
- Document your experimental process

**E. Model Evaluation:**

*For Regression Tasks:*
- R-squared (R²)
- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- Residual analysis

*For Classification Tasks:*
- Accuracy
- Precision, Recall, F1-Score
- Confusion Matrix
- ROC Curve and AUC
- Classification report

**F. Model Comparison:**
- Create comparison table showing all models' performance
- Select best model with clear justification
- Discuss trade-offs (interpretability vs. performance, overfitting risks)

**G. Feature Importance:**
- Identify which features are most predictive
- Interpret what drives predictions
- Discuss business implications

#### Deliverables
- Modeling notebook (Python/R with full pipeline)
- Model comparison report (2 pages)
- Best model saved (pickle/joblib file)
- Performance metrics summary (table/chart)

---

### 5. Model Interpretation & Business Insights (10 points)

#### Requirements

**A. Model Interpretation:**
- Explain how your model makes predictions
- Interpret coefficients (for linear models) or feature importances
- Provide example predictions with explanations

**B. Business Recommendations:**
- Translate model findings into actionable insights
- Recommend at least **3 specific actions** based on your analysis
- Quantify potential impact where possible

**C. Limitations & Ethics:**
- Discuss model limitations (assumptions, data quality, generalizability)
- Address potential biases in data or model
- Consider ethical implications (privacy, fairness, potential misuse)
- Suggest how model should and should not be used

**D. Future Work:**
- Identify how the analysis could be improved
- Suggest additional data that would help
- Propose next steps for deployment

#### Deliverables
- Interpretation report (2 pages)
- Business recommendations document (1 page)
- Limitations and ethics assessment (1 page)

---

### 6. Project Report (15 points)

Submit a comprehensive **8-12 page PDF report** (excluding appendices) structured as follows:

#### Report Structure

**1. Executive Summary (1 page)**
- Problem statement and objectives
- Key findings (3-5 bullet points)
- Primary recommendation
- Expected impact

**2. Introduction (1-2 pages)**
- Background and motivation
- Problem definition
- Research questions
- Scope and limitations

**3. Data Collection Methodology (1-2 pages)**
- Sampling strategy
- Data sources and variables
- Ethical considerations
- Data quality assessment

**4. Exploratory Data Analysis (2-3 pages)**
- Key visualizations (select best 6-8)
- Descriptive statistics
- Patterns and insights discovered
- Hypotheses formed

**5. Modeling Approach (2-3 pages)**
- Model selection rationale
- Training methodology
- Hyperparameter tuning
- Model comparison and selection

**6. Results & Interpretation (2 pages)**
- Best model performance metrics
- Feature importance analysis
- Example predictions
- Model validation

**7. Business Insights & Recommendations (1-2 pages)**
- Key findings for stakeholders
- Actionable recommendations
- Expected benefits
- Implementation considerations

**8. Limitations, Ethics & Future Work (1 page)**
- Model and data limitations
- Ethical considerations
- Bias assessment
- Proposed improvements

**9. Conclusion (0.5 page)**
- Summary of achievement
- Main takeaways
- Final recommendations

**10. References**
- Cite all data sources
- Academic/technical references used

**Appendices** *(not counted in page limit):*
- Consent form template
- Questionnaire
- Additional visualizations
- Code snippets (key sections only)

---

### 7. Presentation & Viva (10 points)

#### Presentation Requirements

**Format:** 15-minute presentation + 10-minute Q&A

**Presentation Slides:** 10-15 slides including title/conclusion

**Presentation Delivery:**
- Clear and confident delivery
- Equal participation from all group members (each presents ≥2 slides)
- Effective use of visualizations
- Time management (stay within 15 minutes)
- Professional appearance and demeanor

**Viva/Q&A Session:** All group members must be prepared to answer questions about:
- Data collection challenges and decisions
- Specific data cleaning choices
- Statistical interpretations
- Model selection and tuning decisions
- Code implementation details
- Ethical considerations
- Alternative approaches considered
- Individual contributions

**Demonstration:**
- Show live or recorded demo of your analysis pipeline
- Be ready to explain specific code sections
- Demonstrate how predictions are made
- Show model evaluation results

---

## Submission Instructions

### File Organization

Create a folder named: `DataScience_Final_GroupX_[GroupName]`

**Required Contents:**

```
DataScience_Final_GroupX_[GroupName]/
│
├── README.md (or README.txt)
│   ├── Group members (names, IDs)
│   ├── Project title
│   ├── Brief description
│   ├── File structure explanation
│   ├── How to run the code
│   └── Dependencies/requirements
│
├── 1_Data_Collection/
│   ├── raw_data_anonymized.csv
│   ├── consent_form.pdf
│   ├── questionnaire.pdf
│   └── data_collection_report.pdf
│
├── 2_Data_Cleaning/
│   ├── data_cleaning.ipynb (or .Rmd)
│   ├── cleaned_data.csv
│   └── cleaning_report.pdf
│
├── 3_EDA/
│   ├── exploratory_analysis.ipynb (or .Rmd)
│   ├── eda_report.pdf
│   └── visualizations/ (folder with saved plots)
│
├── 4_Modeling/
│   ├── modeling.ipynb (or .Rmd)
│   ├── best_model.pkl (saved model file)
│   ├── model_comparison.pdf
│   └── results/ (performance metrics, charts)
│
├── 5_Report/
│   ├── Final_Report.pdf (8-12 pages)
│   └── appendices/ (if separate files)
│
├── 6_Presentation/
│   ├── Presentation_Slides.pdf (or .pptx)
│   └── demo_video.mp4 (optional but recommended)
│
├── requirements.txt (Python) or sessionInfo.txt (R)
│   (list of all libraries and versions used)
│
└── CONTRIBUTIONS.md
    (detailed breakdown of each member's contributions)
```

### Submission Method

1. **Compress** the entire folder into: `DataScience_Final_GroupX_[GroupName].zip`
2. **Submit via email** to: Kuetche.fotsing@ictuniversity.edu.cm
3. **Email Subject:** "Data Science Final Project - Group X - [GroupName]"
4. **Email Body:** Include all group members' names and student IDs

**Deadline:** Sunday, 3rd May, 2026 11:59 PM WAT

> ⚠️ **Late submissions:** 5% penalty per day (up to 3 days). After 5 days: 0 points unless documented emergency.

---

**ALL THE BEST**
