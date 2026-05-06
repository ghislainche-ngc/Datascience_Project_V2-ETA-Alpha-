"""
Fast modeling pipeline — fixed hyperparameters, no GridSearchCV.
Uses best params from prior behavioral-only run.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.preprocessing import RobustScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             confusion_matrix, classification_report)
from sklearn.dummy import DummyClassifier
from xgboost import XGBClassifier
import pickle, os, json, warnings
warnings.filterwarnings('ignore')

np.random.seed(42)
plt.rcParams['figure.dpi'] = 120
plt.rcParams['font.size'] = 10
sns.set_style('whitegrid')
os.makedirs('results', exist_ok=True)

print("=" * 60)
print("MODELING PIPELINE WITH DEMOGRAPHIC INTEGRATION")
print("=" * 60)

# ============================================================
# 1. LOAD
# ============================================================
print("\n[1] Loading data...")
user_features = pd.read_csv('results/user_features_with_class.csv')
demo_raw = pd.read_excel('../Data/demographic.xlsx')
prior = pd.read_csv('results/model_comparison.csv')
print(f"  Behavioral: {user_features.shape[0]} users")
print(f"  Demographic: {demo_raw.shape[0]} users")

# ============================================================
# 2. CLEAN DEMOGRAPHICS
# ============================================================
print("\n[2] Cleaning demographics...")
demo = demo_raw.copy()
demo.columns = ['user_id','age_range','gender','profession','education',
                'income_range','geo_zone','household_size','primary_use','smartphone']

demo['age_range'] = demo['age_range'].str.replace(' ','').str.strip()
demo['gender'] = demo['gender'].map({'M':'Male','F':'Female'})

prof_map = {'Student':'Student','Self-Employed':'Self-Employed',
            'Private sector':'Employed','Teacher':'Employed',
            'Public Sector Employee':'Employed','Unemployed':'Unemployed',
            'Trader':'Self-Employed','Retired':'Retired'}
demo['profession'] = demo['profession'].str.strip().map(prof_map)

edu_map = {'Bachelor':'Bachelor','Bachelors':'Bachelor',
           'High School':'Secondary','Secondary School':'Secondary',
           'Secondary':'Secondary','Masters':'Master','Primary':'Primary'}
demo['education'] = demo['education'].map(edu_map)

income_map = {'< 50,000':'<50k','50,000 - 100,000':'50k-100k',
              '100,000 - 200,000':'100k-200k','200,000 - 400,000':'200k-400k',
              '> 400,000':'>400k','400,000 >':'>400k'}
demo['income_range'] = demo['income_range'].map(income_map)

demo['geo_zone'] = demo['geo_zone'].apply(
    lambda z: 'Urban' if 'Urban' in str(z) else ('Suburban' if 'Suburban' in str(z) else 'Rural'))
demo['primary_use'] = demo['primary_use'].str.strip()
demo['smartphone'] = demo['smartphone'].str.strip()

print("  Cleaned. Distributions:")
for col in ['age_range','gender','profession','education','income_range','geo_zone']:
    print(f"    {col}: {demo[col].value_counts().to_dict()}")

# ============================================================
# 3. EXTEND TO ALL 69 USERS
# ============================================================
print("\n[3] Extending demographics...")
demo['UserId'] = demo['user_id'].apply(lambda x: f"orig_user_{int(x.replace('User0','')):03d}")
demo['demo_source'] = 'real'

missing_ids = sorted(set(user_features['UserId']) - set(demo['UserId']))
np.random.seed(42)
synthetic = []
for uid in missing_ids:
    synthetic.append({
        'UserId': uid,
        'age_range': np.random.choice(['18-24','25-34','35-44','45-54','55+'],p=[.30,.35,.20,.10,.05]),
        'gender': np.random.choice(['Male','Female'],p=[.45,.55]),
        'profession': np.random.choice(['Student','Employed','Self-Employed','Unemployed','Retired'],p=[.30,.30,.25,.10,.05]),
        'education': np.random.choice(['Primary','Secondary','Bachelor','Master'],p=[.05,.35,.40,.20]),
        'income_range': np.random.choice(['<50k','50k-100k','100k-200k','200k-400k','>400k'],p=[.35,.25,.20,.12,.08]),
        'geo_zone': np.random.choice(['Urban','Suburban','Rural'],p=[.65,.20,.15]),
        'household_size': int(np.random.choice(range(1,11),p=[.08,.12,.18,.20,.15,.10,.07,.05,.03,.02])),
        'primary_use': np.random.choice(['Personal','Business','Both'],p=[.50,.15,.35]),
        'smartphone': np.random.choice(['Yes','No'],p=[.85,.15]),
        'demo_source': 'proxy'
    })

demo_clean = demo[['UserId','age_range','gender','profession','education',
                    'income_range','geo_zone','household_size','primary_use','smartphone','demo_source']]
demo_full = pd.concat([demo_clean, pd.DataFrame(synthetic)], ignore_index=True)
print(f"  Full: {demo_full.shape[0]} users (Real={len(demo)}, Proxy={len(synthetic)})")

# ============================================================
# 4. MERGE
# ============================================================
print("\n[4] Merging...")
merged = user_features.merge(demo_full, on='UserId', how='inner')
assert merged.shape[0] == 69 and merged['UserId'].duplicated().sum() == 0
print(f"  Merged: {merged.shape[0]} × {merged.shape[1]}")

# ============================================================
# 5. ENCODE
# ============================================================
print("\n[5] Encoding...")
merged['age_ordinal'] = merged['age_range'].map({'18-24':1,'25-34':2,'35-44':3,'45-54':4,'55+':5})
merged['education_ordinal'] = merged['education'].map({'Primary':1,'Secondary':2,'Bachelor':3,'Master':4})
merged['income_ordinal'] = merged['income_range'].map({'<50k':1,'50k-100k':2,'100k-200k':3,'200k-400k':4,'>400k':5})
merged['gender_binary'] = (merged['gender']=='Male').astype(int)
merged['smartphone_binary'] = (merged['smartphone']=='Yes').astype(int)

prof_dum = pd.get_dummies(merged['profession'], prefix='prof', drop_first=True)
geo_dum = pd.get_dummies(merged['geo_zone'], prefix='geo', drop_first=True)
use_dum = pd.get_dummies(merged['primary_use'], prefix='use', drop_first=True)
encoded = pd.concat([merged, prof_dum, geo_dum, use_dum], axis=1)

BEHAVIORAL = ['mean_amount','median_amount','std_amount','avg_balance',
              'pct_weekend','avg_sr_ratio','pct_out','avg_hour','std_hour',
              'pct_airtime','pct_depot','pct_paiement','pct_retrait','pct_transaction','pct_transfert']
DEMOGRAPHIC = (['age_ordinal','education_ordinal','income_ordinal',
                'gender_binary','smartphone_binary','household_size'] +
               list(prof_dum.columns) + list(geo_dum.columns) + list(use_dum.columns))
ALL_FEATURES = BEHAVIORAL + DEMOGRAPHIC
print(f"  Behavioral={len(BEHAVIORAL)}, Demographic={len(DEMOGRAPHIC)}, Total={len(ALL_FEATURES)}")

# ============================================================
# 6. SPLIT
# ============================================================
print("\n[6] Splitting 70/15/15...")
le = LabelEncoder()
encoded['target'] = le.fit_transform(encoded['activity_class'])
X = encoded[ALL_FEATURES].values
y = encoded['target'].values
indices = np.arange(len(y))
train_idx, temp_idx, y_train, y_temp = train_test_split(indices, y, test_size=0.30, random_state=42, stratify=y)
val_idx, test_idx, y_val, y_test = train_test_split(temp_idx, y_temp, test_size=0.50, random_state=42, stratify=y_temp)

X_train, X_val, X_test = X[train_idx], X[val_idx], X[test_idx]
scaler = RobustScaler()
X_train_sc = scaler.fit_transform(X_train)
X_val_sc = scaler.transform(X_val)
X_test_sc = scaler.transform(X_test)
print(f"  Train={X_train.shape[0]}, Val={X_val.shape[0]}, Test={X_test.shape[0]}, Features={X_train.shape[1]}")

# ============================================================
# 7. BASELINES
# ============================================================
print("\n[7] Baselines...")
baselines = {}
for bname, strat in [('Majority Class','most_frequent'),('Stratified Random','stratified')]:
    clf = DummyClassifier(strategy=strat, random_state=42).fit(X_train, y_train)
    yp = clf.predict(X_test)
    baselines[bname] = {'accuracy':accuracy_score(y_test,yp),
                        'f1_weighted':f1_score(y_test,yp,average='weighted',zero_division=0),
                        'f1_macro':f1_score(y_test,yp,average='macro',zero_division=0)}
    print(f"  {bname}: F1m={baselines[bname]['f1_macro']:.4f}")

# ============================================================
# 8. TRAIN 3 MODELS (fixed hyperparameters — no GridSearchCV)
# ============================================================
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scoring = ['accuracy','f1_weighted','f1_macro']
results = {}

print("\n[8a] Logistic Regression...")
lr_model = LogisticRegression(C=1, solver='lbfgs', class_weight='balanced', max_iter=1000, random_state=42)
lr_model.fit(X_train_sc, y_train)
lr_cv = cross_validate(lr_model, X_train_sc, y_train, cv=cv, scoring=scoring)
results['Logistic Regression'] = {
    'model': lr_model, 'uses_scaler': True,
    'best_params': {'C': 1, 'solver': 'lbfgs'},
    'cv_accuracy': lr_cv['test_accuracy'].mean(), 'cv_accuracy_std': lr_cv['test_accuracy'].std(),
    'cv_f1w': lr_cv['test_f1_weighted'].mean(), 'cv_f1w_std': lr_cv['test_f1_weighted'].std(),
    'cv_f1m': lr_cv['test_f1_macro'].mean(), 'cv_f1m_std': lr_cv['test_f1_macro'].std(),
}
print(f"  CV F1m={results['Logistic Regression']['cv_f1m']:.4f}")

print("\n[8b] Random Forest...")
rf_model = RandomForestClassifier(n_estimators=200, max_depth=5, min_samples_split=2,
                                   min_samples_leaf=1, class_weight='balanced', random_state=42)
rf_model.fit(X_train, y_train)
rf_cv = cross_validate(rf_model, X_train, y_train, cv=cv, scoring=scoring)
results['Random Forest'] = {
    'model': rf_model, 'uses_scaler': False,
    'best_params': {'n_estimators':200,'max_depth':5,'min_samples_split':2,'min_samples_leaf':1},
    'cv_accuracy': rf_cv['test_accuracy'].mean(), 'cv_accuracy_std': rf_cv['test_accuracy'].std(),
    'cv_f1w': rf_cv['test_f1_weighted'].mean(), 'cv_f1w_std': rf_cv['test_f1_weighted'].std(),
    'cv_f1m': rf_cv['test_f1_macro'].mean(), 'cv_f1m_std': rf_cv['test_f1_macro'].std(),
}
print(f"  CV F1m={results['Random Forest']['cv_f1m']:.4f}")

print("\n[8c] XGBoost...")
xgb_model = XGBClassifier(n_estimators=200, max_depth=3, learning_rate=0.1, subsample=0.8,
                           use_label_encoder=False, eval_metric='mlogloss', random_state=42, verbosity=0)
xgb_model.fit(X_train, y_train)
xgb_cv = cross_validate(xgb_model, X_train, y_train, cv=cv, scoring=scoring)
results['XGBoost'] = {
    'model': xgb_model, 'uses_scaler': False,
    'best_params': {'n_estimators':200,'max_depth':3,'learning_rate':0.1,'subsample':0.8},
    'cv_accuracy': xgb_cv['test_accuracy'].mean(), 'cv_accuracy_std': xgb_cv['test_accuracy'].std(),
    'cv_f1w': xgb_cv['test_f1_weighted'].mean(), 'cv_f1w_std': xgb_cv['test_f1_weighted'].std(),
    'cv_f1m': xgb_cv['test_f1_macro'].mean(), 'cv_f1m_std': xgb_cv['test_f1_macro'].std(),
}
print(f"  CV F1m={results['XGBoost']['cv_f1m']:.4f}")

# ============================================================
# 9. EVALUATE ON TEST SET
# ============================================================
print("\n[9] Test set evaluation...")
for name, info in results.items():
    Xt = X_test_sc if info['uses_scaler'] else X_test
    yp = info['model'].predict(Xt)
    Xv = X_val_sc if info['uses_scaler'] else X_val
    yv = info['model'].predict(Xv)
    info['test_accuracy'] = accuracy_score(y_test, yp)
    info['test_f1w'] = f1_score(y_test, yp, average='weighted')
    info['test_f1m'] = f1_score(y_test, yp, average='macro')
    info['test_precision'] = precision_score(y_test, yp, average='weighted')
    info['test_recall'] = recall_score(y_test, yp, average='weighted')
    info['val_accuracy'] = accuracy_score(y_val, yv)
    info['val_f1w'] = f1_score(y_val, yv, average='weighted')
    info['val_f1m'] = f1_score(y_val, yv, average='macro')
    info['y_pred'] = yp
    print(f"\n  {name}: Val F1m={info['val_f1m']:.4f} | Test F1m={info['test_f1m']:.4f}")
    print(classification_report(y_test, yp, target_names=le.classes_))

# ============================================================
# 10. DEMOGRAPHIC IMPACT
# ============================================================
print("\n[10] Demographic impact...")
models_list = ['Logistic Regression','Random Forest','XGBoost']
impact_data = {}
print(f"  {'Model':<25} {'Behav':>8} {'Combined':>8} {'Delta':>8}")
print("  "+"-"*50)
for name in models_list:
    pr = prior[prior['Model']==name]
    f1b = pr['Test F1 (macro)'].values[0] if len(pr)>0 else 0
    f1a = results[name]['test_f1m']
    impact_data[name] = {'before':f1b,'after':f1a,'delta':f1a-f1b}
    print(f"  {name:<25} {f1b:>8.4f} {f1a:>8.4f} {f1a-f1b:>+8.4f}")

# ============================================================
# 11. BEST MODEL
# ============================================================
best_name = max(results, key=lambda k: results[k]['test_f1m'])
best = results[best_name]
print(f"\n[11] Best: {best_name} (F1m={best['test_f1m']:.4f}, CV={best['cv_f1m']:.4f}±{best['cv_f1m_std']:.4f})")

# ============================================================
# 12. OVERFITTING
# ============================================================
print("\n[12] Overfitting analysis...")
for name, info in results.items():
    gap = info['test_f1w'] - info['cv_f1w']
    v = "Stable" if abs(gap)<0.05 else ("Moderate" if abs(gap)<0.15 else "Large")
    print(f"  {name:<25} Test={info['test_f1w']:.4f} CV={info['cv_f1w']:.4f} Gap={gap:+.4f} {v}")

# ============================================================
# 13. FEATURE IMPORTANCE
# ============================================================
print("\n[13] Feature importance...")
xgb_imp = pd.Series(xgb_model.feature_importances_, index=ALL_FEATURES)
rf_imp = pd.Series(rf_model.feature_importances_, index=ALL_FEATURES)

print("\n  XGBoost Top 10:")
for f,v in xgb_imp.sort_values(ascending=False).head(10).items():
    t = "BEHAV" if f in BEHAVIORAL else "DEMO"
    print(f"    {f:<25} {v:.4f} [{t}]")

print("\n  RF Top 10:")
for f,v in rf_imp.sort_values(ascending=False).head(10).items():
    t = "BEHAV" if f in BEHAVIORAL else "DEMO"
    print(f"    {f:<25} {v:.4f} [{t}]")

coef_df = pd.DataFrame(lr_model.coef_, columns=ALL_FEATURES, index=le.classes_).T
print("\n  LR top coefficients per class:")
for cls in le.classes_:
    top = coef_df[cls].sort_values(ascending=False).head(3)
    print(f"    {cls}: {', '.join(f'{ff}={vv:+.3f}' for ff,vv in top.items())}")

# ============================================================
# 14. FIGURES
# ============================================================
print("\n[14] Generating figures...")
from matplotlib.patches import Patch
legend_el = [Patch(facecolor='#2E86C1',label='Behavioral'),Patch(facecolor='#E67E22',label='Demographic')]

# Fig 1: Feature importance
fig, axes = plt.subplots(1,2,figsize=(14,7))
for ax, imp, title in [(axes[0],xgb_imp,'XGBoost'),(axes[1],rf_imp,'Random Forest')]:
    top = imp.sort_values(ascending=False).head(15)
    colors = ['#2E86C1' if f in BEHAVIORAL else '#E67E22' for f in top.index]
    ax.barh(range(15), top.values[::-1], color=colors[::-1])
    ax.set_yticks(range(15)); ax.set_yticklabels(top.index[::-1], fontsize=8)
    ax.set_xlabel('Importance'); ax.set_title(f'{title} Feature Importance')
    ax.legend(handles=legend_el, fontsize=8)
plt.tight_layout()
plt.savefig('results/feature_importance.png', dpi=150, bbox_inches='tight'); plt.close()
print("  feature_importance.png")

# Fig 2: Confusion matrices
fig, axes = plt.subplots(1,3,figsize=(15,4.5))
for i,(name,info) in enumerate(results.items()):
    cm = confusion_matrix(y_test, info['y_pred'])
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[i],
                xticklabels=le.classes_, yticklabels=le.classes_)
    axes[i].set_title(f'{name}\nF1m={info["test_f1m"]:.3f}', fontsize=10)
    axes[i].set_ylabel('True' if i==0 else ''); axes[i].set_xlabel('Predicted')
plt.suptitle('Confusion Matrices (Behavioral + Demographic)', fontsize=12, y=1.02)
plt.tight_layout()
plt.savefig('results/confusion_matrices.png', dpi=150, bbox_inches='tight'); plt.close()
print("  confusion_matrices.png")

# Fig 3: Demographic impact
fig, axes = plt.subplots(1,2,figsize=(14,5))
x = np.arange(3); w = 0.35
bf = [impact_data[m]['before'] for m in models_list]
cf = [impact_data[m]['after'] for m in models_list]
bl = baselines['Stratified Random']['f1_macro']
axes[0].bar(x-w/2, bf, w, label='Behavioral Only', color='#2E86C1')
axes[0].bar(x+w/2, cf, w, label='Behavioral + Demographic', color='#E67E22')
axes[0].axhline(y=bl, color='red', linestyle='--', alpha=0.7, label=f'Baseline ({bl:.2f})')
axes[0].set_ylabel('F1 (Macro)'); axes[0].set_title('Test F1: Behavioral vs Combined')
axes[0].set_xticks(x); axes[0].set_xticklabels(models_list, fontsize=9)
axes[0].legend(fontsize=8); axes[0].set_ylim(0,0.85)
for b in axes[0].patches[:3]:
    axes[0].text(b.get_x()+b.get_width()/2, b.get_height()+0.01, f'{b.get_height():.3f}', ha='center', fontsize=8)
for b in list(axes[0].patches)[3:6]:
    axes[0].text(b.get_x()+b.get_width()/2, b.get_height()+0.01, f'{b.get_height():.3f}', ha='center', fontsize=8)

cvf = [results[m]['cv_f1m'] for m in models_list]
cvs = [results[m]['cv_f1m_std'] for m in models_list]
pcv = [prior[prior['Model']==m]['CV F1m (mean)'].values[0] for m in models_list]
pcs = [prior[prior['Model']==m]['CV F1m (std)'].values[0] for m in models_list]
axes[1].bar(x-w/2, pcv, w, yerr=pcs, capsize=4, label='Behavioral Only', color='#2E86C1', alpha=0.8)
axes[1].bar(x+w/2, cvf, w, yerr=cvs, capsize=4, label='Behavioral + Demographic', color='#E67E22', alpha=0.8)
axes[1].set_ylabel('F1 (Macro)'); axes[1].set_title('CV F1 ± Std')
axes[1].set_xticks(x); axes[1].set_xticklabels(models_list, fontsize=9)
axes[1].legend(fontsize=8); axes[1].set_ylim(0,0.85)
plt.tight_layout()
plt.savefig('results/demographic_impact_comparison.png', dpi=150, bbox_inches='tight'); plt.close()
print("  demographic_impact_comparison.png")

# Fig 4: CV results
fig, ax = plt.subplots(figsize=(10,5))
x = np.arange(3); w = 0.2
for i,(k,l,c) in enumerate(zip(['cv_accuracy','cv_f1w','cv_f1m'],
    ['CV Accuracy','CV F1 (weighted)','CV F1 (macro)'],['#3498DB','#27AE60','#E74C3C'])):
    vs = [results[m][k] for m in models_list]
    ss = [results[m][f'{k}_std'] for m in models_list]
    ax.bar(x+i*w, vs, w, yerr=ss, capsize=3, label=l, color=c, alpha=0.8)
ax.set_xticks(x+w); ax.set_xticklabels(models_list)
ax.set_ylabel('Score'); ax.set_title('Cross-Validation Performance (5-Fold)')
ax.legend(); ax.set_ylim(0,0.85)
plt.tight_layout()
plt.savefig('results/cv_results.png', dpi=150, bbox_inches='tight'); plt.close()
print("  cv_results.png")

# Fig 5: LR coefficients
fig, ax = plt.subplots(figsize=(10,8))
sns.heatmap(coef_df, annot=True, fmt='.2f', cmap='RdBu_r', center=0, ax=ax)
ax.set_title('LR Coefficients by Class')
plt.tight_layout()
plt.savefig('results/lr_coefficients.png', dpi=150, bbox_inches='tight'); plt.close()
print("  lr_coefficients.png")

# ============================================================
# 15. SAVE
# ============================================================
print("\n[15] Saving...")

with open('best_model.pkl','wb') as f:
    pickle.dump({'model':best['model'],'label_encoder':le,'features':ALL_FEATURES,
                 'behavioral_features':BEHAVIORAL,'demographic_features':DEMOGRAPHIC,
                 'scaler':scaler if best['uses_scaler'] else None,
                 'model_name':best_name,'test_f1_macro':best['test_f1m'],'cv_f1_macro':best['cv_f1m']}, f)
print(f"  best_model.pkl ({best_name})")

# Comparison table
rows = []
for bname, m in baselines.items():
    rows.append({'Model':bname,'Feature Set':'Baseline','Test Accuracy':m['accuracy'],
                 'Test F1 (weighted)':m['f1_weighted'],'Test F1 (macro)':m['f1_macro'],
                 'CV F1m (mean)':'','CV F1m (std)':''})
for nm in models_list:
    pr = prior[prior['Model']==nm]
    if len(pr)>0:
        rows.append({'Model':nm,'Feature Set':'Behavioral Only',
                     'Test Accuracy':pr['Test Accuracy'].values[0],
                     'Test F1 (weighted)':pr['Test F1 (weighted)'].values[0],
                     'Test F1 (macro)':pr['Test F1 (macro)'].values[0],
                     'CV F1m (mean)':pr['CV F1m (mean)'].values[0],
                     'CV F1m (std)':pr['CV F1m (std)'].values[0]})
for nm, info in results.items():
    rows.append({'Model':nm,'Feature Set':'Behavioral + Demographic',
                 'Test Accuracy':round(info['test_accuracy'],4),
                 'Test F1 (weighted)':round(info['test_f1w'],4),
                 'Test F1 (macro)':round(info['test_f1m'],4),
                 'CV F1m (mean)':round(info['cv_f1m'],4),
                 'CV F1m (std)':round(info['cv_f1m_std'],4)})
pd.DataFrame(rows).to_csv('results/model_comparison_full.csv', index=False)
print("  model_comparison_full.csv")

demo_full.to_csv('results/demographics_cleaned.csv', index=False)
encoded.to_csv('results/user_features_with_demographics.csv', index=False)
coef_df.to_csv('results/lr_coefficients.csv')
print("  demographics_cleaned.csv, user_features_with_demographics.csv, lr_coefficients.csv")

# Error analysis
test_users = encoded.iloc[test_idx].copy()
test_users['predicted'] = le.inverse_transform(results[best_name]['y_pred'])
test_users['correct'] = test_users['activity_class'] == test_users['predicted']
nc = int(test_users['correct'].sum())

# JSON summary
summary = {
    'best_model': best_name, 'best_params': best['best_params'],
    'n_behavioral': len(BEHAVIORAL), 'n_demographic': len(DEMOGRAPHIC),
    'n_total': len(ALL_FEATURES), 'demographic_features': DEMOGRAPHIC,
    'split': {'train': int(X_train.shape[0]), 'val': int(X_val.shape[0]), 'test': int(X_test.shape[0])},
    'classes': list(le.classes_),
    'baselines': baselines, 'impact': {k:{kk:round(vv,4) for kk,vv in v.items()} for k,v in impact_data.items()},
    'error_analysis': {'correct':nc,'total':len(test_users),'pct':round(nc/len(test_users)*100,1)},
    'xgb_top10': {f:round(float(v),4) for f,v in xgb_imp.sort_values(ascending=False).head(10).items()},
    'rf_top10': {f:round(float(v),4) for f,v in rf_imp.sort_values(ascending=False).head(10).items()},
    'results': {}
}
for nm, info in results.items():
    summary['results'][nm] = {k:v for k,v in info.items() if k not in ['model','y_pred']}
    summary['results'][nm]['y_pred'] = info['y_pred'].tolist()

with open('results/pipeline_summary.json','w') as f:
    json.dump(summary, f, indent=2, default=str)
print("  pipeline_summary.json")

print("\n" + "=" * 60)
print("PIPELINE COMPLETE")
print("=" * 60)
print(f"Best: {best_name} | Test F1m={best['test_f1m']:.4f} | CV F1m={best['cv_f1m']:.4f}±{best['cv_f1m_std']:.4f}")
