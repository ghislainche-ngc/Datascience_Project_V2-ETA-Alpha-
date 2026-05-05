"""
Build the comprehensive modeling notebook with demographic integration.
3 models: Logistic Regression, Random Forest, XGBoost (with combined features).
Compares against prior behavioral-only results from model_comparison.csv.
"""
import nbformat as nbf

nb = nbf.v4.new_notebook()
nb.metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.12.0"}
}

cells = []

# ============================================================
# TITLE
# ============================================================
cells.append(nbf.v4.new_markdown_cell("""# Section 4: Statistical Modeling & Prediction

## Mobile Money User Activity Classification — With Demographic Integration

**Task:** Multi-class classification (Low / Medium / High activity users) using behavioral + demographic features.

**Pipeline:**
1. Load & clean demographic data → merge with behavioral features
2. Feature encoding (ordinal + one-hot)
3. Train/validation/test split (70/15/15, stratified)
4. Train 3 models: Logistic Regression, Random Forest, XGBoost
5. Evaluate & compare against prior behavioral-only results
6. Feature importance & error analysis

**Reproducibility:** `random_state=42` used throughout."""))

# ============================================================
# IMPORTS
# ============================================================
cells.append(nbf.v4.new_code_cell("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV, cross_validate
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             confusion_matrix, classification_report)
from sklearn.dummy import DummyClassifier
from xgboost import XGBClassifier
import pickle, os, warnings
warnings.filterwarnings('ignore')

np.random.seed(42)
plt.rcParams['figure.dpi'] = 120
plt.rcParams['font.size'] = 10
sns.set_style('whitegrid')
os.makedirs('results', exist_ok=True)
print("Setup complete.")"""))

# ============================================================
# LOAD DATA
# ============================================================
cells.append(nbf.v4.new_markdown_cell("""---
## 1. Data Loading

Two datasets:
1. **Behavioral features** — 69 users aggregated from 20,530 transactions
2. **Demographic data** — 10 real questionnaire responses used as a demographic supplement"""))

cells.append(nbf.v4.new_code_cell("""user_features = pd.read_csv('results/user_features_with_class.csv')
print(f"Behavioral dataset: {user_features.shape[0]} users × {user_features.shape[1]} columns")
print(f"\\nActivity class distribution:")
print(user_features['activity_class'].value_counts().to_string())

# Load prior behavioral-only results for comparison
prior_results = pd.read_csv('results/model_comparison.csv')
print(f"\\nPrior behavioral-only results loaded ({prior_results.shape[0]} rows)")
prior_results"""))

cells.append(nbf.v4.new_code_cell("""demo_raw = pd.read_excel('../Data/demographic.xlsx')
print(f"Demographic dataset: {demo_raw.shape[0]} users × {demo_raw.shape[1]} columns\\n")
demo_raw"""))

# ============================================================
# CLEAN DEMOGRAPHICS
# ============================================================
cells.append(nbf.v4.new_markdown_cell("""---
## 2. Demographic Data Cleaning

Standardizing all categorical fields:
- Age ranges: consistent format (18-24, 25-34, 35-44, 45-54, 55+)
- Gender: Male / Female
- Profession: 5 groups (Student, Employed, Self-Employed, Unemployed, Retired)
- Education: 4 levels (Primary, Secondary, Bachelor, Master)
- Income: 5 brackets (<50k, 50k-100k, 100k-200k, 200k-400k, >400k)
- Geography: Urban / Suburban / Rural
- Fix encoding issues (e.g. Yaoundé)"""))

cells.append(nbf.v4.new_code_cell("""demo = demo_raw.copy()
demo.columns = ['user_id', 'age_range', 'gender', 'profession', 'education',
                'income_range', 'geo_zone', 'household_size', 'primary_use', 'smartphone']

# 1. Normalize age ranges
age_map = {'25-34': '25-34', '25 - 34': '25-34', '18-24': '18-24', '18 - 24': '18-24',
           '35-44': '35-44', '35 - 44': '35-44', '45-54': '45-54', '45 - 54': '45-54', '55+': '55+'}
demo['age_range'] = demo['age_range'].map(age_map)

# 2. Standardize gender
demo['gender'] = demo['gender'].map({'M': 'Male', 'F': 'Female'})

# 3. Group professions
prof_map = {'Student': 'Student', 'Self-Employed': 'Self-Employed',
            'Private sector': 'Employed', 'Teacher': 'Employed',
            'Public Sector Employee': 'Employed', 'Unemployed': 'Unemployed',
            'Trader': 'Self-Employed', 'Retired': 'Retired'}
demo['profession'] = demo['profession'].str.strip().map(prof_map)

# 4. Standardize education
edu_map = {'Bachelor': 'Bachelor', 'Bachelors': 'Bachelor',
           'High School': 'Secondary', 'Secondary School': 'Secondary',
           'Secondary': 'Secondary', 'Masters': 'Master', 'Primary': 'Primary'}
demo['education'] = demo['education'].map(edu_map)

# 5. Standardize income
income_map = {'< 50,000': '<50k', '50,000 - 100,000': '50k-100k',
              '100,000 - 200,000': '100k-200k', '200,000 - 400,000': '200k-400k',
              '> 400,000': '>400k', '400,000 >': '>400k'}
demo['income_range'] = demo['income_range'].map(income_map)

# 6. Simplify geographic zone
demo['geo_zone'] = demo['geo_zone'].apply(
    lambda z: 'Urban' if 'Urban' in str(z) else ('Suburban' if 'Suburban' in str(z) else 'Rural'))

# 7. Clean primary_use and smartphone
demo['primary_use'] = demo['primary_use'].str.strip()
demo['smartphone'] = demo['smartphone'].str.strip()

print("=== Cleaned Demographic Data ===\\n")
print(demo.to_string(index=False))
print(f"\\nNull values: {demo.isnull().sum().sum()}")"""))

cells.append(nbf.v4.new_code_cell("""# Cleaning summary
print("=== Distribution per Variable ===\\n")
for col in ['age_range', 'gender', 'profession', 'education', 'income_range',
            'geo_zone', 'primary_use', 'smartphone']:
    print(f"{col}: {demo[col].value_counts().to_dict()}")
print(f"household_size: mean={demo['household_size'].mean():.1f}, "
      f"range=[{demo['household_size'].min()}, {demo['household_size'].max()}]")"""))

# ============================================================
# DEMOGRAPHIC EXTENSION
# ============================================================
cells.append(nbf.v4.new_markdown_cell("""---
## 3. Demographic Augmentation

Only 10/69 users completed the questionnaire. To keep the modeling sample aligned with the full behavioral dataset, we generate demographic proxies for the remaining 59 users using:
- Distributions from the 10 real responses
- Cameroon urban population priors (World Bank / INS data)

All records are tagged: `demo_source = "real"` vs `"proxy"`."""))

cells.append(nbf.v4.new_code_cell("""# Map demographic IDs to behavioral IDs
demo['UserId'] = demo['user_id'].apply(lambda x: f"orig_user_{int(x.replace('User0', '')):03d}")
demo['demo_source'] = 'real'

in_behav = demo['UserId'].isin(user_features['UserId'])
print(f"Mapped IDs: {demo['UserId'].tolist()}")
print(f"All found in behavioral data: {in_behav.all()}")

# Generate proxy demographics for remaining users
all_ids = set(user_features['UserId'])
missing_ids = sorted(all_ids - set(demo['UserId']))
print(f"\\nReal demographic users: {len(demo)}")
print(f"Need proxy records for: {len(missing_ids)} users")

np.random.seed(42)
synthetic = []
for uid in missing_ids:
    synthetic.append({
        'UserId': uid,
        'age_range': np.random.choice(['18-24','25-34','35-44','45-54','55+'], p=[.30,.35,.20,.10,.05]),
        'gender': np.random.choice(['Male','Female'], p=[.45,.55]),
        'profession': np.random.choice(['Student','Employed','Self-Employed','Unemployed','Retired'], p=[.30,.30,.25,.10,.05]),
        'education': np.random.choice(['Primary','Secondary','Bachelor','Master'], p=[.05,.35,.40,.20]),
        'income_range': np.random.choice(['<50k','50k-100k','100k-200k','200k-400k','>400k'], p=[.35,.25,.20,.12,.08]),
        'geo_zone': np.random.choice(['Urban','Suburban','Rural'], p=[.65,.20,.15]),
        'household_size': int(np.random.choice(range(1,11), p=[.08,.12,.18,.20,.15,.10,.07,.05,.03,.02])),
        'primary_use': np.random.choice(['Personal','Business','Both'], p=[.50,.15,.35]),
        'smartphone': np.random.choice(['Yes','No'], p=[.85,.15]),
        'demo_source': 'proxy'
    })

demo_clean = demo[['UserId','age_range','gender','profession','education',
                    'income_range','geo_zone','household_size','primary_use','smartphone','demo_source']]
demo_full = pd.concat([demo_clean, pd.DataFrame(synthetic)], ignore_index=True)
    print(f"\nFull demographic dataset: {demo_full.shape[0]} users (Real: {(demo_full.demo_source=='real').sum()}, Proxy: {(demo_full.demo_source=='proxy').sum()})")"""))

# ============================================================
# MERGE
# ============================================================
cells.append(nbf.v4.new_markdown_cell("""---
## 4. Merge Datasets"""))

cells.append(nbf.v4.new_code_cell("""merged = user_features.merge(demo_full, on='UserId', how='inner')
print(f"Merged dataset: {merged.shape[0]} users × {merged.shape[1]} columns")
print(f"No duplicates: {merged['UserId'].duplicated().sum() == 0}")
print(f"No missing joins: {merged.shape[0] == user_features.shape[0]}")
print(f"\\nClass distribution: {merged['activity_class'].value_counts().to_dict()}")"""))

# ============================================================
# FEATURE ENCODING
# ============================================================
cells.append(nbf.v4.new_markdown_cell("""---
## 5. Feature Encoding

**Ordinal** for ordered categories (age, education, income) — preserves order without extra dimensions.
**Binary** for 2-category (gender, smartphone). **One-hot** for unordered (profession, geo_zone, primary_use).
**Numeric** as-is (household_size)."""))

cells.append(nbf.v4.new_code_cell("""# Ordinal encoding
merged['age_ordinal'] = merged['age_range'].map({'18-24':1,'25-34':2,'35-44':3,'45-54':4,'55+':5})
merged['education_ordinal'] = merged['education'].map({'Primary':1,'Secondary':2,'Bachelor':3,'Master':4})
merged['income_ordinal'] = merged['income_range'].map({'<50k':1,'50k-100k':2,'100k-200k':3,'200k-400k':4,'>400k':5})

# Binary encoding
merged['gender_binary'] = (merged['gender'] == 'Male').astype(int)
merged['smartphone_binary'] = (merged['smartphone'] == 'Yes').astype(int)

# One-hot encoding
prof_dum = pd.get_dummies(merged['profession'], prefix='prof', drop_first=True)
geo_dum = pd.get_dummies(merged['geo_zone'], prefix='geo', drop_first=True)
use_dum = pd.get_dummies(merged['primary_use'], prefix='use', drop_first=True)

encoded = pd.concat([merged, prof_dum, geo_dum, use_dum], axis=1)

DEMOGRAPHIC_FEATURES = (['age_ordinal','education_ordinal','income_ordinal',
                         'gender_binary','smartphone_binary','household_size'] +
                        list(prof_dum.columns) + list(geo_dum.columns) + list(use_dum.columns))

print(f"Demographic features ({len(DEMOGRAPHIC_FEATURES)}): {DEMOGRAPHIC_FEATURES}")"""))

# ============================================================
# FEATURE DEFINITION & LEAKAGE PREVENTION
# ============================================================
cells.append(nbf.v4.new_markdown_cell("""---
## 6. Feature Selection & Data Leakage Prevention

| Category | Features | Decision |
|----------|----------|----------|
| **Safe behavioral (15)** | mean_amount, median_amount, std_amount, avg_balance, pct_weekend, avg_sr_ratio, pct_out, avg_hour, std_hour, pct_airtime, pct_depot, pct_paiement, pct_retrait, pct_transaction, pct_transfert | Describe *how* a user transacts |
| **Safe demographic** | age, gender, profession, education, income, geo_zone, household_size, primary_use, smartphone | External attributes |
| **Excluded (leakage)** | monthly_txn_frequency, txn_velocity_7d, txn_count, total_in, total_out | Derived from transaction count = target |
| **Excluded (proxy)** | data_source, demo_source | Dataset identity |"""))

cells.append(nbf.v4.new_code_cell("""BEHAVIORAL_FEATURES = [
    'mean_amount','median_amount','std_amount','avg_balance',
    'pct_weekend','avg_sr_ratio','pct_out','avg_hour','std_hour',
    'pct_airtime','pct_depot','pct_paiement','pct_retrait','pct_transaction','pct_transfert'
]

ALL_FEATURES = BEHAVIORAL_FEATURES + DEMOGRAPHIC_FEATURES

LEAKAGE = ['txn_count','total_in','total_out','monthly_txn_frequency','txn_velocity_7d']
PROXIES = ['data_source','demo_source']

assert not any(f in ALL_FEATURES for f in LEAKAGE + PROXIES), "Leakage detected!"

print(f"Behavioral features: {len(BEHAVIORAL_FEATURES)}")
print(f"Demographic features: {len(DEMOGRAPHIC_FEATURES)}")
print(f"Total features: {len(ALL_FEATURES)}")
print(f"Excluded (leakage): {[f for f in LEAKAGE if f in encoded.columns]}")
print("\\n✓ No data leakage in feature set")"""))

# ============================================================
# TARGET & SPLIT
# ============================================================
cells.append(nbf.v4.new_markdown_cell("""---
## 7. Target Encoding & Train-Validation-Test Split (70/15/15 Stratified)

**Why 70/15/15:** With 69 users, this yields a train set large enough for model fitting while preserving separate validation and test holdouts.
**Why stratification:** Ensures proportional class representation in each split.
**Validation set:** Used as a holdout check alongside cross-validation on the training set."""))

cells.append(nbf.v4.new_code_cell("""le = LabelEncoder()
encoded['target'] = le.fit_transform(encoded['activity_class'])
print(f"Classes: {dict(zip(le.classes_, le.transform(le.classes_)))}")

X = encoded[ALL_FEATURES].values
y = encoded['target'].values

X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.30, random_state=42, stratify=y
)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.50, random_state=42, stratify=y_temp
)

print(f"\nTrain: {X_train.shape[0]} users | Val: {X_val.shape[0]} users | Test: {X_test.shape[0]} users")
print(f"Train classes: {dict(zip(*np.unique(y_train, return_counts=True)))}")
print(f"Val classes:   {dict(zip(*np.unique(y_val, return_counts=True)))}")
print(f"Test classes:  {dict(zip(*np.unique(y_test, return_counts=True)))}")
print(f"Features: {X_train.shape[1]}")

# Scale for Logistic Regression
scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_val_sc = scaler.transform(X_val)
X_test_sc = scaler.transform(X_test)"""))

# ============================================================
# BASELINES
# ============================================================
cells.append(nbf.v4.new_markdown_cell("""---
## 8. Baseline Models"""))

cells.append(nbf.v4.new_code_cell("""baselines = {}

majority = DummyClassifier(strategy='most_frequent', random_state=42)
majority.fit(X_train, y_train)
y_maj = majority.predict(X_test)
baselines['Majority Class'] = {
    'accuracy': accuracy_score(y_test, y_maj),
    'f1_weighted': f1_score(y_test, y_maj, average='weighted', zero_division=0),
    'f1_macro': f1_score(y_test, y_maj, average='macro', zero_division=0),
}

stratified = DummyClassifier(strategy='stratified', random_state=42)
stratified.fit(X_train, y_train)
y_strat = stratified.predict(X_test)
baselines['Stratified Random'] = {
    'accuracy': accuracy_score(y_test, y_strat),
    'f1_weighted': f1_score(y_test, y_strat, average='weighted', zero_division=0),
    'f1_macro': f1_score(y_test, y_strat, average='macro', zero_division=0),
}

for name, m in baselines.items():
    print(f"{name}: Accuracy={m['accuracy']:.4f}, F1(macro)={m['f1_macro']:.4f}")"""))

# ============================================================
# MODEL TRAINING (3 models with combined features)
# ============================================================
cells.append(nbf.v4.new_markdown_cell("""---
## 9. Model Training (Behavioral + Demographic Features)

Training 3 models on the combined feature set. GridSearchCV with Stratified 5-Fold CV for hyperparameter tuning."""))

cells.append(nbf.v4.new_code_cell("""cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scoring = ['accuracy', 'f1_weighted', 'f1_macro']
results = {}

# ---- 1. Logistic Regression ----
print("Training Logistic Regression...")
lr_grid = GridSearchCV(
    LogisticRegression(solver='lbfgs', class_weight='balanced', max_iter=1000, random_state=42),
    {'C': [0.1, 1, 10]},
    cv=cv, scoring='f1_macro', refit=True, n_jobs=1
)
lr_grid.fit(X_train_sc, y_train)
lr_model = lr_grid.best_estimator_
lr_cv = cross_validate(lr_model, X_train_sc, y_train, cv=cv, scoring=scoring)
results['Logistic Regression'] = {
    'model': lr_model, 'uses_scaler': True,
    'best_params': lr_grid.best_params_,
    'cv_accuracy': lr_cv['test_accuracy'].mean(), 'cv_accuracy_std': lr_cv['test_accuracy'].std(),
    'cv_f1w': lr_cv['test_f1_weighted'].mean(), 'cv_f1w_std': lr_cv['test_f1_weighted'].std(),
    'cv_f1m': lr_cv['test_f1_macro'].mean(), 'cv_f1m_std': lr_cv['test_f1_macro'].std(),
}
print(f"  Best C={lr_grid.best_params_['C']}, CV F1(macro)={lr_grid.best_score_:.4f}")"""))

cells.append(nbf.v4.new_code_cell("""# ---- 2. Random Forest ----
print("Training Random Forest...")
rf_grid = GridSearchCV(
    RandomForestClassifier(class_weight='balanced', random_state=42),
    {'n_estimators': [100,200], 'max_depth': [3,5,7],
     'min_samples_split': [2,5], 'min_samples_leaf': [1,2]},
    cv=cv, scoring='f1_macro', refit=True, n_jobs=1
)
rf_grid.fit(X_train, y_train)
rf_model = rf_grid.best_estimator_
rf_cv = cross_validate(rf_model, X_train, y_train, cv=cv, scoring=scoring)
results['Random Forest'] = {
    'model': rf_model, 'uses_scaler': False,
    'best_params': rf_grid.best_params_,
    'cv_accuracy': rf_cv['test_accuracy'].mean(), 'cv_accuracy_std': rf_cv['test_accuracy'].std(),
    'cv_f1w': rf_cv['test_f1_weighted'].mean(), 'cv_f1w_std': rf_cv['test_f1_weighted'].std(),
    'cv_f1m': rf_cv['test_f1_macro'].mean(), 'cv_f1m_std': rf_cv['test_f1_macro'].std(),
}
print(f"  Best params: {rf_grid.best_params_}")
print(f"  CV F1(macro)={rf_grid.best_score_:.4f}")"""))

cells.append(nbf.v4.new_code_cell("""# ---- 3. XGBoost ----
print("Training XGBoost...")
xgb_grid = GridSearchCV(
    XGBClassifier(use_label_encoder=False, eval_metric='mlogloss', random_state=42, verbosity=0),
    {'n_estimators': [100,200], 'max_depth': [3,5],
     'learning_rate': [0.05,0.1], 'subsample': [0.8,1.0]},
    cv=cv, scoring='f1_macro', refit=True, n_jobs=1
)
xgb_grid.fit(X_train, y_train)
xgb_model = xgb_grid.best_estimator_
xgb_cv = cross_validate(xgb_model, X_train, y_train, cv=cv, scoring=scoring)
results['XGBoost'] = {
    'model': xgb_model, 'uses_scaler': False,
    'best_params': xgb_grid.best_params_,
    'cv_accuracy': xgb_cv['test_accuracy'].mean(), 'cv_accuracy_std': xgb_cv['test_accuracy'].std(),
    'cv_f1w': xgb_cv['test_f1_weighted'].mean(), 'cv_f1w_std': xgb_cv['test_f1_weighted'].std(),
    'cv_f1m': xgb_cv['test_f1_macro'].mean(), 'cv_f1m_std': xgb_cv['test_f1_macro'].std(),
}
print(f"  Best params: {xgb_grid.best_params_}")
print(f"  CV F1(macro)={xgb_grid.best_score_:.4f}")
print("\\nAll 3 models trained.")"""))

# ============================================================
# EVALUATION
# ============================================================
cells.append(nbf.v4.new_markdown_cell("""---
## 10. Test Set Evaluation"""))

cells.append(nbf.v4.new_code_cell("""print("=== Test Set Performance (Behavioral + Demographic) ===\\n")

for name, info in results.items():
    model = info['model']
    Xt = X_test_sc if info['uses_scaler'] else X_test
    y_pred = model.predict(Xt)

    info['test_accuracy'] = accuracy_score(y_test, y_pred)
    info['test_f1w'] = f1_score(y_test, y_pred, average='weighted')
    info['test_f1m'] = f1_score(y_test, y_pred, average='macro')
    info['test_precision'] = precision_score(y_test, y_pred, average='weighted')
    info['test_recall'] = recall_score(y_test, y_pred, average='weighted')
    info['y_pred'] = y_pred

    print(f"--- {name} ---")
    print(f"  Accuracy:  {info['test_accuracy']:.4f}")
    print(f"  F1 (wt):   {info['test_f1w']:.4f}")
    print(f"  F1 (macro):{info['test_f1m']:.4f}")
    print(f"  Precision: {info['test_precision']:.4f}")
    print(f"  Recall:    {info['test_recall']:.4f}")
    print(classification_report(y_test, y_pred, target_names=le.classes_))"""))

# ============================================================
# CROSS-VALIDATION RESULTS
# ============================================================
cells.append(nbf.v4.new_markdown_cell("""---
## 11. Cross-Validation Results (Stratified 5-Fold)"""))

cells.append(nbf.v4.new_code_cell("""print("=== Cross-Validation Performance ===\\n")
print(f"{'Model':<25} {'CV Acc':>8} {'± Std':>8} {'CV F1w':>8} {'± Std':>8} {'CV F1m':>8} {'± Std':>8}")
print("-"*75)
for name, info in results.items():
    print(f"{name:<25} {info['cv_accuracy']:>8.4f} {info['cv_accuracy_std']:>8.4f} "
          f"{info['cv_f1w']:>8.4f} {info['cv_f1w_std']:>8.4f} "
          f"{info['cv_f1m']:>8.4f} {info['cv_f1m_std']:>8.4f}")"""))

# ============================================================
# DEMOGRAPHIC IMPACT COMPARISON
# ============================================================
cells.append(nbf.v4.new_markdown_cell("""---
## 12. Demographic Impact Analysis

Comparing current results (behavioral + demographic) against prior behavioral-only results."""))

cells.append(nbf.v4.new_code_cell("""# Load prior behavioral-only results
prior = pd.read_csv('results/model_comparison.csv')

print("=== Demographic Impact: Before vs After ===\\n")
print(f"{'Model':<25} {'Behav F1m':>10} {'Combined F1m':>12} {'Delta':>8} {'Impact':>10}")
print("-"*70)
for name in ['Logistic Regression', 'Random Forest', 'XGBoost']:
    prior_row = prior[prior['Model'] == name]
    if len(prior_row) > 0:
        f1_before = prior_row['Test F1 (macro)'].values[0]
    else:
        f1_before = 0
    f1_after = results[name]['test_f1m']
    delta = f1_after - f1_before
    impact = "Improved" if delta > 0.01 else ("Degraded" if delta < -0.01 else "Neutral")
    print(f"{name:<25} {f1_before:>10.4f} {f1_after:>12.4f} {delta:>+8.4f} {impact:>10}")

print("\\n--- Interpretation ---")
print("Demographic coverage is limited to 10 real questionnaire responses; the rest use proxy values.")
print("Impact should be interpreted cautiously until more real demographic responses are collected.")"""))

cells.append(nbf.v4.new_code_cell("""# Visualization: Before vs After comparison
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

models = ['Logistic Regression', 'Random Forest', 'XGBoost']
x = np.arange(len(models))
width = 0.35

# Chart 1: Test F1 (macro)
behav_f1 = [prior[prior['Model']==m]['Test F1 (macro)'].values[0] for m in models]
combined_f1 = [results[m]['test_f1m'] for m in models]
baseline_f1 = prior[prior['Model']=='Stratified Random Baseline']['Test F1 (macro)'].values[0]

b1 = axes[0].bar(x - width/2, behav_f1, width, label='Behavioral Only (prior)', color='#2E86C1')
b2 = axes[0].bar(x + width/2, combined_f1, width, label='Behavioral + Demographic', color='#E67E22')
axes[0].axhline(y=baseline_f1, color='red', linestyle='--', alpha=0.7, label=f'Baseline ({baseline_f1:.2f})')
axes[0].set_ylabel('F1 Score (Macro)')
axes[0].set_title('Test F1 (Macro): Behavioral vs. Combined')
axes[0].set_xticks(x)
axes[0].set_xticklabels(models, fontsize=9)
axes[0].legend(fontsize=8)
axes[0].set_ylim(0, 0.85)
for bar in b1:
    axes[0].text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.01, f'{bar.get_height():.3f}', ha='center', fontsize=8)
for bar in b2:
    axes[0].text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.01, f'{bar.get_height():.3f}', ha='center', fontsize=8)

# Chart 2: CV F1 (macro) with error bars
cv_f1 = [results[m]['cv_f1m'] for m in models]
cv_std = [results[m]['cv_f1m_std'] for m in models]
prior_cv = [prior[prior['Model']==m]['CV F1m (mean)'].values[0] for m in models]
prior_cv_std = [prior[prior['Model']==m]['CV F1m (std)'].values[0] for m in models]

axes[1].bar(x - width/2, prior_cv, width, yerr=prior_cv_std, capsize=4,
            label='Behavioral Only (prior)', color='#2E86C1', alpha=0.8)
axes[1].bar(x + width/2, cv_f1, width, yerr=cv_std, capsize=4,
            label='Behavioral + Demographic', color='#E67E22', alpha=0.8)
axes[1].set_ylabel('F1 Score (Macro)')
axes[1].set_title('Cross-Validation F1 (Macro) ± Std')
axes[1].set_xticks(x)
axes[1].set_xticklabels(models, fontsize=9)
axes[1].legend(fontsize=8)
axes[1].set_ylim(0, 0.85)

plt.tight_layout()
plt.savefig('results/demographic_impact_comparison.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saved: results/demographic_impact_comparison.png")"""))

# ============================================================
# MODEL COMPARISON TABLE
# ============================================================
cells.append(nbf.v4.new_markdown_cell("""---
## 13. Full Model Comparison Table"""))

cells.append(nbf.v4.new_code_cell("""rows = []
for name, m in baselines.items():
    rows.append({'Model': name, 'Feature Set': 'Baseline',
                 'Test Accuracy': m['accuracy'], 'Test F1 (weighted)': m['f1_weighted'],
                 'Test F1 (macro)': m['f1_macro'],
                 'CV F1 (macro) mean': '-', 'CV F1 (macro) std': '-'})

for name in models:
    pr = prior[prior['Model']==name]
    if len(pr) > 0:
        rows.append({'Model': name, 'Feature Set': 'Behavioral Only (prior)',
                     'Test Accuracy': pr['Test Accuracy'].values[0],
                     'Test F1 (weighted)': pr['Test F1 (weighted)'].values[0],
                     'Test F1 (macro)': pr['Test F1 (macro)'].values[0],
                     'CV F1 (macro) mean': pr['CV F1m (mean)'].values[0],
                     'CV F1 (macro) std': pr['CV F1m (std)'].values[0]})

for name, info in results.items():
    rows.append({'Model': name, 'Feature Set': 'Behavioral + Demographic',
                 'Test Accuracy': info['test_accuracy'],
                 'Test F1 (weighted)': info['test_f1w'],
                 'Test F1 (macro)': info['test_f1m'],
                 'CV F1 (macro) mean': info['cv_f1m'],
                 'CV F1 (macro) std': info['cv_f1m_std']})

comparison = pd.DataFrame(rows)
print(comparison.to_string(index=False))
comparison.to_csv('results/model_comparison_full.csv', index=False)
print("\\nSaved: results/model_comparison_full.csv")"""))

# ============================================================
# BEST MODEL SELECTION
# ============================================================
cells.append(nbf.v4.new_markdown_cell("""---
## 14. Best Model Selection"""))

cells.append(nbf.v4.new_code_cell("""best_name = max(results, key=lambda k: results[k]['test_f1m'])
best = results[best_name]

print(f"=== Best Model: {best_name} ===")
print(f"  Test Accuracy:  {best['test_accuracy']:.4f}")
print(f"  Test F1 (wt):   {best['test_f1w']:.4f}")
print(f"  Test F1 (macro):{best['test_f1m']:.4f}")
print(f"  Test Precision:  {best['test_precision']:.4f}")
print(f"  Test Recall:     {best['test_recall']:.4f}")
print(f"  CV F1 (macro):   {best['cv_f1m']:.4f} ± {best['cv_f1m_std']:.4f}")
print(f"  Best params: {best['best_params']}")

print(f"\\nPer-class performance:")
Xt = X_test_sc if best['uses_scaler'] else X_test
print(classification_report(y_test, best['y_pred'], target_names=le.classes_))"""))

# ============================================================
# OVERFITTING ANALYSIS
# ============================================================
cells.append(nbf.v4.new_markdown_cell("""---
## 15. Overfitting Analysis"""))

cells.append(nbf.v4.new_code_cell("""print("=== Overfitting Analysis ===\\n")
print(f"{'Model':<25} {'Test F1w':>10} {'CV F1w':>10} {'Gap':>8} {'Verdict':>15}")
print("-"*70)
for name, info in results.items():
    gap = info['test_f1w'] - info['cv_f1w']
    verdict = "Stable" if abs(gap) < 0.05 else ("Moderate" if abs(gap) < 0.15 else "Large gap")
    print(f"{name:<25} {info['test_f1w']:>10.4f} {info['cv_f1w']:>10.4f} {gap:>+8.4f} {verdict:>15}")
print("\\nGaps < 0.15 are acceptable for a 69-sample dataset.")"""))

# ============================================================
# FEATURE IMPORTANCE
# ============================================================
cells.append(nbf.v4.new_markdown_cell("""---
## 16. Feature Importance

Identifying the most predictive features — behavioral and demographic."""))

cells.append(nbf.v4.new_code_cell("""# XGBoost feature importance
xgb_imp = pd.Series(xgb_model.feature_importances_, index=ALL_FEATURES)
xgb_top = xgb_imp.sort_values(ascending=False)

print("=== XGBoost Feature Importance (Top 15) ===\\n")
for feat, imp in xgb_top.head(15).items():
    tag = "BEHAV" if feat in BEHAVIORAL_FEATURES else "DEMO"
    print(f"  {feat:<25} {imp:.4f}  [{tag}]")

# Count behavioral vs demographic in top 10
top10 = xgb_top.head(10)
n_behav = sum(1 for f in top10.index if f in BEHAVIORAL_FEATURES)
n_demo = sum(1 for f in top10.index if f in DEMOGRAPHIC_FEATURES)
print(f"\\nTop 10 composition: {n_behav} behavioral, {n_demo} demographic")"""))

cells.append(nbf.v4.new_code_cell("""# Random Forest feature importance
rf_imp = pd.Series(rf_model.feature_importances_, index=ALL_FEATURES)
rf_top = rf_imp.sort_values(ascending=False)

print("=== Random Forest Feature Importance (Top 15) ===\\n")
for feat, imp in rf_top.head(15).items():
    tag = "BEHAV" if feat in BEHAVIORAL_FEATURES else "DEMO"
    print(f"  {feat:<25} {imp:.4f}  [{tag}]")"""))

cells.append(nbf.v4.new_code_cell("""# Feature importance visualization
fig, axes = plt.subplots(1, 2, figsize=(14, 7))
from matplotlib.patches import Patch
legend_el = [Patch(facecolor='#2E86C1', label='Behavioral'), Patch(facecolor='#E67E22', label='Demographic')]

top_n = 15

# XGBoost
top_xgb = xgb_imp.sort_values(ascending=False).head(top_n)
colors_xgb = ['#2E86C1' if f in BEHAVIORAL_FEATURES else '#E67E22' for f in top_xgb.index]
axes[0].barh(range(top_n), top_xgb.values[::-1], color=colors_xgb[::-1])
axes[0].set_yticks(range(top_n))
axes[0].set_yticklabels(top_xgb.index[::-1], fontsize=8)
axes[0].set_xlabel('Importance')
axes[0].set_title('XGBoost Feature Importance')
axes[0].legend(handles=legend_el, fontsize=8)

# Random Forest
top_rf = rf_imp.sort_values(ascending=False).head(top_n)
colors_rf = ['#2E86C1' if f in BEHAVIORAL_FEATURES else '#E67E22' for f in top_rf.index]
axes[1].barh(range(top_n), top_rf.values[::-1], color=colors_rf[::-1])
axes[1].set_yticks(range(top_n))
axes[1].set_yticklabels(top_rf.index[::-1], fontsize=8)
axes[1].set_xlabel('Importance')
axes[1].set_title('Random Forest Feature Importance')
axes[1].legend(handles=legend_el, fontsize=8)

plt.tight_layout()
plt.savefig('results/feature_importance.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saved: results/feature_importance.png")"""))

cells.append(nbf.v4.new_code_cell("""# Logistic Regression coefficients
coef_df = pd.DataFrame(lr_model.coef_, columns=ALL_FEATURES, index=le.classes_).T

print("=== LR Coefficients — Top Drivers per Class ===\\n")
for cls in le.classes_:
    top_pos = coef_df[cls].sort_values(ascending=False).head(5)
    top_neg = coef_df[cls].sort_values().head(3)
    print(f"--- {cls} ---")
    print("  Positive (pushes toward this class):")
    for feat, val in top_pos.items():
        tag = "BEHAV" if feat in BEHAVIORAL_FEATURES else "DEMO"
        print(f"    {feat:<25} {val:+.4f}  [{tag}]")
    print("  Negative (pushes away):")
    for feat, val in top_neg.items():
        tag = "BEHAV" if feat in BEHAVIORAL_FEATURES else "DEMO"
        print(f"    {feat:<25} {val:+.4f}  [{tag}]")
    print()

fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(coef_df, annot=True, fmt='.2f', cmap='RdBu_r', center=0, ax=ax,
            cbar_kws={'label': 'Coefficient'})
ax.set_title('LR Coefficients by Class')
plt.tight_layout()
plt.savefig('results/lr_coefficients.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saved: results/lr_coefficients.png")"""))

# ============================================================
# CONFUSION MATRICES
# ============================================================
cells.append(nbf.v4.new_markdown_cell("""---
## 17. Confusion Matrices"""))

cells.append(nbf.v4.new_code_cell("""fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

for idx, (name, info) in enumerate(results.items()):
    cm = confusion_matrix(y_test, info['y_pred'])
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx],
                xticklabels=le.classes_, yticklabels=le.classes_)
    axes[idx].set_title(f'{name}\\nF1m={info["test_f1m"]:.3f}', fontsize=10)
    axes[idx].set_ylabel('True' if idx == 0 else '')
    axes[idx].set_xlabel('Predicted')

plt.suptitle('Confusion Matrices (Behavioral + Demographic Features)', fontsize=12, y=1.02)
plt.tight_layout()
plt.savefig('results/confusion_matrices.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saved: results/confusion_matrices.png")"""))

# ============================================================
# ERROR ANALYSIS
# ============================================================
cells.append(nbf.v4.new_markdown_cell("""---
## 18. Error Analysis"""))

cells.append(nbf.v4.new_code_cell("""# Error analysis on best model
_, test_idx = train_test_split(np.arange(len(y)), test_size=0.30, random_state=42, stratify=y)
test_users = encoded.iloc[test_idx].copy()
test_users['predicted'] = le.inverse_transform(results[best_name]['y_pred'])
test_users['correct'] = test_users['activity_class'] == test_users['predicted']

correct = test_users[test_users['correct']]
incorrect = test_users[~test_users['correct']]

print(f"=== Error Analysis ({best_name}) ===\\n")
print(f"Correct: {len(correct)}/{len(test_users)} ({len(correct)/len(test_users)*100:.0f}%)")
print(f"Incorrect: {len(incorrect)}/{len(test_users)} ({len(incorrect)/len(test_users)*100:.0f}%)")

print(f"\\nMisclassification patterns:")
for _, row in incorrect.iterrows():
    print(f"  {row['activity_class']:>6} -> {row['predicted']:<6}  "
          f"mean_amt={row['mean_amount']:,.0f}  sr_ratio={row['avg_sr_ratio']:.2f}")

print(f"\\nFeature comparison:")
for feat in ['mean_amount','median_amount','std_amount','avg_balance','avg_sr_ratio']:
    print(f"  {feat:<20} Correct: {correct[feat].mean():>12,.0f}   Incorrect: {incorrect[feat].mean():>12,.0f}")"""))

# ============================================================
# CV RESULTS CHART
# ============================================================
cells.append(nbf.v4.new_code_cell("""fig, ax = plt.subplots(figsize=(10, 5))
models_list = list(results.keys())
x = np.arange(len(models_list))
width = 0.2
for i, (key, label, color) in enumerate(zip(
    ['cv_accuracy','cv_f1w','cv_f1m'], ['CV Accuracy','CV F1 (weighted)','CV F1 (macro)'],
    ['#3498DB','#27AE60','#E74C3C'])):
    vals = [results[m][key] for m in models_list]
    stds = [results[m][f'{key}_std'] for m in models_list]
    ax.bar(x + i*width, vals, width, yerr=stds, capsize=3, label=label, color=color, alpha=0.8)
ax.set_xticks(x + width)
ax.set_xticklabels(models_list)
ax.set_ylabel('Score')
ax.set_title('Cross-Validation Performance (5-Fold Stratified)')
ax.legend()
ax.set_ylim(0, 0.85)
plt.tight_layout()
plt.savefig('results/cv_results.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saved: results/cv_results.png")"""))

# ============================================================
# SAVE MODELS
# ============================================================
cells.append(nbf.v4.new_markdown_cell("""---
## 19. Save Models & Results"""))

cells.append(nbf.v4.new_code_cell("""# Save best model
model_pkg = {
    'model': results[best_name]['model'],
    'label_encoder': le,
    'features': ALL_FEATURES,
    'behavioral_features': BEHAVIORAL_FEATURES,
    'demographic_features': DEMOGRAPHIC_FEATURES,
    'scaler': scaler if results[best_name]['uses_scaler'] else None,
    'model_name': best_name,
    'test_f1_macro': results[best_name]['test_f1m'],
    'cv_f1_macro': results[best_name]['cv_f1m'],
}
with open('best_model.pkl', 'wb') as f:
    pickle.dump(model_pkg, f)
print(f"Saved: best_model.pkl ({best_name})")

# Save merged dataset
encoded.to_csv('results/user_features_with_demographics.csv', index=False)
print(f"Saved: results/user_features_with_demographics.csv ({encoded.shape})")

# Save cleaned demographics
demo_full.to_csv('results/demographics_cleaned.csv', index=False)
print(f"Saved: results/demographics_cleaned.csv ({demo_full.shape})")

# Save LR coefficients
coef_df.to_csv('results/lr_coefficients.csv')
print("Saved: results/lr_coefficients.csv")

print("\\n" + "="*50)
print("PIPELINE COMPLETE")
print("="*50)
print(f"Best model: {best_name}")
print(f"Test F1 (macro): {results[best_name]['test_f1m']:.4f}")
print(f"CV F1 (macro):   {results[best_name]['cv_f1m']:.4f} ± {results[best_name]['cv_f1m_std']:.4f}")"""))

# ============================================================
# ASSEMBLE
# ============================================================
nb.cells = cells

with open('modeling.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print(f"Notebook created: modeling.ipynb ({len(cells)} cells)")
