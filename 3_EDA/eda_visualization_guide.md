# EDA Visualization Guide

This document explains the purpose of the EDA phase and walks through each chart in the `visualizations` folder one by one so you can describe them clearly in class, in a report, or during a viva.

## What EDA Is About

Exploratory Data Analysis (EDA) is the stage where you study the dataset before modeling.

The goal is to:

- understand what the data looks like
- check whether the data is clean and usable
- find patterns, trends, and unusual values
- compare groups and categories
- detect possible data leakage or misleading variables
- form hypotheses that can later be tested in modeling
- decide which features are likely to be useful

In this project, EDA is especially important because the final prediction task is user classification. That means we are trying to understand how different users behave in the mobile money system and which transaction patterns separate Low, Medium, and High activity users.

When you explain EDA, a good simple structure is:

1. What the chart shows
2. Why the chart matters
3. What pattern you notice
4. What that pattern means for the project

---

## How to Read the Visualizations

The charts in this folder are not just pictures. Each one answers a different question:

- Are transaction amounts mostly small or large?
- Are there extreme outliers?
- Do users transact more during certain months or hours?
- Which transaction types dominate the data?
- Are some variables related to each other?
- Do different user groups behave differently?
- Which patterns may help predict user class?

If you explain the charts in this order, your audience will see a logical story rather than a random set of graphs.

---

## Chart-by-Chart Guide

### 1. `01_amount_distributions.png`

**What it shows:**
Distribution plots for key financial variables, usually using histogram plus KDE curve.

**How to explain it:**
This chart shows how transaction values are spread across the dataset. The histogram shows the frequency of values in each range, while the KDE line gives a smoother view of the overall shape.

**What to notice:**
- The amounts are heavily right-skewed.
- Most transactions are small.
- A few large transactions create a long tail.

**Why it matters:**
This tells us the dataset is dominated by micro-transactions rather than large-value transfers. That means the mean can be misleading, so the median is often more useful for describing a typical transaction.

**How to say it in presentation form:**
"Most transactions are small, and only a small number are very large. This creates a long right tail, which means the dataset is not evenly distributed."

**Link to modeling:**
Skewed variables may need transformation or robust handling before classification.

---

### 2. `02_amount_boxplots.png`

**What it shows:**
Box plots for transaction amount and related numerical variables.

**How to explain it:**
A box plot summarizes the median, quartiles, and outliers. It is useful for quickly seeing spread and extreme values.

**What to notice:**
- The median is much lower than the mean for amount-related variables.
- There are many outliers.
- Some categories or groups may have much wider variation than others.

**Why it matters:**
This confirms the financial data is highly uneven and contains extreme values. It also helps you see whether certain transaction types are more variable than others.

**How to say it in presentation form:**
"The box plot shows that typical transaction values are low, but a few very large transactions stretch the distribution far upward."

**Link to modeling:**
Outliers can influence algorithms like Logistic Regression, so scaling and careful feature engineering matter.

---

### 3. `03_monthly_time_series.png`

**What it shows:**
Monthly transaction volume over time.

**How to explain it:**
This chart tracks how transaction activity changes from month to month across the observation period.

**What to notice:**
- Some months are busier than others.
- There may be growth, seasonality, or irregular peaks.
- The activity is not perfectly uniform over time.

**Why it matters:**
This helps you understand whether user behavior is stable or time-dependent. It also shows whether there are bursts of activity that may reflect holidays, business cycles, or collection periods.

**How to say it in presentation form:**
"Transaction activity changes over time, which suggests that user behavior is influenced by time-based patterns rather than being constant every month."

**Link to modeling:**
Time-based changes can support features like monthly frequency or rolling velocity.

---

### 4. `04_hourly_distribution.png`

**What it shows:**
Transaction distribution by hour of day.

**How to explain it:**
This chart shows when users are most active during the day.

**What to notice:**
- Activity is usually higher in the evening.
- There may also be a smaller morning peak.
- Night-time activity is generally lower.

**Why it matters:**
This suggests that transaction behavior follows daily routines. Users tend to transact when they are active socially or commercially, not randomly across the day.

**How to say it in presentation form:**
"Users are most active during specific hours, especially in the evening, which shows that the timing of activity is structured rather than random."

**Link to modeling:**
Hour-based features can help distinguish different types of users.

---

### 5. `05_correlation_heatmap.png`

**What it shows:**
Correlation heatmap for numerical variables.

**How to explain it:**
A correlation heatmap shows how strongly variables move together. Positive values mean two variables increase together, while negative values mean one tends to increase as the other decreases.

**What to notice:**
- Some variables are strongly related.
- Some engineered features may overlap in meaning.
- Correlations can reveal redundancy.

**Why it matters:**
This helps identify which features carry similar information and which ones may be useful together. It also helps detect multicollinearity risk.

**How to say it in presentation form:**
"The heatmap shows which numeric variables are related and which ones are mostly independent. This helps us choose features more carefully for modeling."

**Link to modeling:**
Highly correlated features may need selection or regularization, especially in Logistic Regression.

---

### 6. `06_categorical_barcharts.png`

**What it shows:**
Bar charts for categorical variables such as transaction type, direction, operator, or source.

**How to explain it:**
These charts show how often each category appears in the dataset.

**What to notice:**
- Some transaction types dominate.
- Outbound transactions are more common than inbound ones.
- One operator may dominate the dataset.
- The data source may be unevenly distributed.

**Why it matters:**
Categorical charts reveal the composition of the dataset and show whether the data is balanced or dominated by one group.

**How to say it in presentation form:**
"The categorical charts show that the dataset is concentrated in a few transaction categories, especially outbound activity and transfers."

**Link to modeling:**
Dominant categories can be important predictors, but some categories may also introduce bias if they are too uneven.

---

### 7. `07_scatter_relationships.png`

**What it shows:**
Scatter plots exploring relationships between pairs of numeric variables.

**How to explain it:**
A scatter plot helps you see whether one variable changes as another changes.

**What to notice:**
- Some relationships may be weak or noisy.
- Others may show a visible trend.
- Outliers may cluster in specific areas.

**Why it matters:**
Scatter plots help determine whether simple numeric relationships exist in the data. They are useful for spotting trends that summary statistics cannot show.

**How to say it in presentation form:**
"The scatter plots help us see whether higher activity is associated with higher amounts, stronger balance changes, or other behavioral patterns."

**Link to modeling:**
Scatter relationships can justify interaction features or nonlinear models such as Random Forest and XGBoost.

---

### 8. `08_grouped_comparisons.png`

**What it shows:**
Grouped bar charts comparing metrics across categories or user groups.

**How to explain it:**
This chart compares one group against another so you can see differences in behavior more clearly.

**What to notice:**
- Some classes have higher average amounts.
- Some groups transact more frequently.
- Patterns differ by class, type, or source.

**Why it matters:**
Grouped comparisons are useful for identifying which segments behave differently. This is especially important because the final target is user classification.

**How to say it in presentation form:**
"This chart compares groups side by side, and it shows that user activity is not the same across all classes."

**Link to modeling:**
These differences support the idea that user class can be predicted from behavioral features.

---

### 9. `09_activity_heatmap.png`

**What it shows:**
A heatmap of activity by hour and day.

**How to explain it:**
This is an advanced chart that combines time-of-day and day-of-week patterns into one view.

**What to notice:**
- Certain hours are consistently busier.
- Some days are more active than others.
- The highest activity often clusters in realistic routine periods.

**Why it matters:**
This gives a richer understanding of user behavior than a simple hourly bar chart. It helps show whether activity is concentrated in specific time windows.

**How to say it in presentation form:**
"The activity heatmap reveals when users are most active during the week and during the day, which makes the behavioral pattern much easier to see."

**Link to modeling:**
This can support temporal features such as hour, weekday, and weekend indicators.

---

### 10. `10_user_classification.png`

**What it shows:**
The distribution of the target user classes and related class-level profiles.

**How to explain it:**
This chart shows how users are divided into Low, Medium, and High activity groups.

**What to notice:**
- The classes are usually balanced or close to balanced.
- The class profiles differ in transaction frequency and behavior.
- The chart confirms that the target is meaningful and not arbitrary.

**Why it matters:**
This is the bridge between EDA and modeling. It shows how the target variable is defined and whether the classes are suitable for classification.

**How to say it in presentation form:**
"This chart shows the target classes we will predict. The classes are defined from user activity levels, and their behavioral profiles are different enough to justify classification."

**Link to modeling:**
If the classes are balanced and distinct, classification models are more likely to learn useful patterns.

---

### 11. `11_class_balance_check.png`

**What it shows:**
A deeper class balance and per-class profile check.

**How to explain it:**
This chart confirms that each class has roughly similar representation and shows how the average features differ across classes.

**What to notice:**
- Class balance is acceptable.
- High-activity users often have different frequency and behavioral metrics from Low-activity users.
- The features show clear separation across classes.

**Why it matters:**
A balanced target is important because classification models can struggle when one class dominates heavily. This chart helps confirm that the class design is workable.

**How to say it in presentation form:**
"This chart verifies that the classes are reasonably balanced and that the feature profiles are different enough for classification to make sense."

**Link to modeling:**
This supports model training and evaluation fairness.

---

## How to Explain the EDA Phase in Detail

If you need to explain the entire EDA phase, you can describe it in four parts:

### 1. Data Understanding

You first inspect the dataset to see what variables exist, how many users and transactions there are, and whether the data is complete enough to use.

In this project, that means understanding:

- transaction count
- user count
- transaction types
- dates and time coverage
- amount distributions
- missing values
- balance fields
- categorical variables

### 2. Pattern Discovery

You then look for recurring patterns.

Examples in this project include:

- small-value transactions dominating the dataset
- outbound transactions being more common than inbound ones
- evening activity peaks
- different behavior across data sources
- strong separation between user activity levels

### 3. Feature and Risk Assessment

EDA is also where you decide what may be useful later in modeling and what may be risky.

For this project, EDA helps you identify:

- useful predictors such as amount patterns, frequency, ratio features, and time features
- variables that may be too skewed
- possible outliers
- features that may cause leakage if they overlap with the target
- features that should be excluded, such as the data source shortcut

### 4. Hypothesis Formation

Finally, EDA gives you hypotheses to test in modeling.

Examples here include:

- frequent users are likely easier to identify than occasional users
- send/receive ratio may separate personal users from business-like users
- weekend activity may reflect different usage behavior
- amount statistics alone will not fully explain user class
- time-based behavior may improve prediction accuracy

---

## Short Way to Summarize the EDA Phase

You can say:

"The EDA phase is where we study the mobile money dataset before modeling. We use charts and summary statistics to understand the data structure, identify dominant patterns, detect outliers, compare categories, and form hypotheses about what features might predict user classification. It helps us make sure the data is clean, interpretable, and suitable for machine learning."

---

## What You Should Remember for Viva or Presentation

- EDA is about understanding, not predicting yet.
- Every chart has a purpose.
- The data is highly skewed, so averages alone are not enough.
- Time patterns matter because user behavior changes by hour and day.
- Class balance matters because the final task is classification.
- Strong patterns in EDA help justify the modeling choices later.
- Some variables are useful, but others may cause leakage if used carelessly.

---

## One-Sentence Explanation for Each Chart

- `01_amount_distributions.png`: Shows that transaction values are heavily right-skewed.
- `02_amount_boxplots.png`: Shows spread and outliers in transaction-related numeric variables.
- `03_monthly_time_series.png`: Shows how activity changes month by month.
- `04_hourly_distribution.png`: Shows when users are most active during the day.
- `05_correlation_heatmap.png`: Shows which numeric features move together.
- `06_categorical_barcharts.png`: Shows the makeup of key categorical variables.
- `07_scatter_relationships.png`: Shows pairwise relationships between numeric variables.
- `08_grouped_comparisons.png`: Shows differences between categories or user groups.
- `09_activity_heatmap.png`: Shows day-and-hour activity patterns together.
- `10_user_classification.png`: Shows the user class target and its profile.
- `11_class_balance_check.png`: Confirms class balance and per-class separation.

---

## Final Tip

If you want to explain any chart well, always connect it back to the project goal: predicting user activity class from mobile money behavior. That connection is what turns EDA from "just plotting" into a meaningful analysis.
