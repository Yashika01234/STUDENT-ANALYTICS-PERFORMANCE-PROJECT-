"""Step 4 - Machine learning with scikit-learn.

A. Regression      : predict CGPA over semesters 3-6 from information known after semester 2.
B. Classification  : early-warning flag for students likely to finish semesters 3-6 below CGPA 7.0.
C. Clustering      : K-Means student archetypes from performance trajectory and habits.
All features come from semesters 1-2 + admission data, so there is no target leakage.
"""
import json
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score, cross_val_predict, KFold, StratifiedKFold, GridSearchCV
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, RandomForestClassifier
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error, roc_auc_score, roc_curve, confusion_matrix, \
    classification_report, silhouette_score, precision_recall_fscore_support
from sklearn.inspection import permutation_importance
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from utils import PROC, FIG, OUT, MODELS

sns.set_theme(style="whitegrid"); plt.rcParams.update({"figure.dpi": 130, "axes.titleweight": "bold"})
SEED = 42
S = pd.read_csv(PROC / "student_summary.csv")
SEM = pd.read_csv(PROC / "student_semester.csv")

# ---------- feature table (info available after semester 2) ----------
early = SEM[SEM.semester <= 2].groupby("enrollment_no").agg(early_attendance=("avg_attendance", "mean"), early_backlogs=("backlogs", "sum")).reset_index()
late = SEM[SEM.semester >= 3].merge(S[["enrollment_no"]], on="enrollment_no")
late_cgpa = late.assign(w=late.credits_attempted).groupby("enrollment_no").apply(
    lambda d: (d.sgpa * d.w).sum() / d.w.sum(), include_groups=False).rename("target_cgpa_s3_6").reset_index()
df = S.merge(early, on="enrollment_no").merge(late_cgpa, on="enrollment_no")
df["sgpa_s2_minus_s1"] = df.sgpa_s2 - df.sgpa_s1
NUM = ["sgpa_s1", "sgpa_s2", "sgpa_s2_minus_s1", "early_attendance", "early_backlogs", "board_pct", "entrance_percentile", "weekly_study_hrs"]
CAT = ["branch", "gender", "residence", "extracurricular"]
X, y = df[NUM + CAT], df["target_cgpa_s3_6"]
pre = ColumnTransformer([("num", StandardScaler(), NUM), ("cat", OneHotEncoder(drop="first"), CAT)])
RISK_THRESHOLD = 7.0

# ======================= A. REGRESSION =======================
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=.2, random_state=SEED, stratify=df.branch)
cv = KFold(5, shuffle=True, random_state=SEED)
models = {
    "Baseline (mean)": DummyRegressor(),
    "Ridge": Ridge(alpha=1.0),
    "Random Forest": RandomForestRegressor(n_estimators=300, min_samples_leaf=3, random_state=SEED, n_jobs=-1),
    "Gradient Boosting": GradientBoostingRegressor(random_state=SEED),
}
rows = []
for name, m in models.items():
    pipe = Pipeline([("pre", pre), ("m", m)])
    rmse = -cross_val_score(pipe, Xtr, ytr, cv=cv, scoring="neg_root_mean_squared_error")
    r2 = cross_val_score(pipe, Xtr, ytr, cv=cv, scoring="r2")
    rows.append({"model": name, "cv_rmse": rmse.mean(), "cv_rmse_std": rmse.std(), "cv_r2": r2.mean()})
cmp = pd.DataFrame(rows).sort_values("cv_rmse").round(4)

gs = GridSearchCV(Pipeline([("pre", pre), ("m", GradientBoostingRegressor(random_state=SEED))]),
                  {"m__n_estimators": [100, 200], "m__max_depth": [2, 3], "m__learning_rate": [.05, .1]},
                  cv=cv, scoring="neg_root_mean_squared_error", n_jobs=-1).fit(Xtr, ytr)
ridge = Pipeline([("pre", pre), ("m", Ridge(alpha=1.0))]).fit(Xtr, ytr)
cands = {"Tuned Gradient Boosting": gs.best_estimator_, "Ridge": ridge}
test = {k: dict(rmse=float(np.sqrt(mean_squared_error(yte, v.predict(Xte)))), mae=float(mean_absolute_error(yte, v.predict(Xte))), r2=float(r2_score(yte, v.predict(Xte)))) for k, v in cands.items()}
best_name = min(test, key=lambda k: test[k]["rmse"]); best = cands[best_name]
cmp.to_csv(OUT / "model_comparison_regression.csv", index=False)
print(cmp); print("Holdout:", json.dumps(test, indent=1)); print("Best:", best_name, gs.best_params_)

pred = best.predict(Xte)
fig, ax = plt.subplots(figsize=(5.8, 5.4))
ax.scatter(yte, pred, alpha=.5, s=18); lim = [min(yte.min(), pred.min()), max(yte.max(), pred.max())]
ax.plot(lim, lim, "r--"); ax.set(title=f"Predicted vs actual CGPA (sem 3-6)\n{best_name}, R2={test[best_name]['r2']:.2f}", xlabel="Actual", ylabel="Predicted")
plt.tight_layout(); plt.savefig(FIG / "10_pred_vs_actual.png"); plt.close()

pi = permutation_importance(best, Xte, yte, n_repeats=15, random_state=SEED, scoring="neg_root_mean_squared_error")
imp = pd.Series(pi.importances_mean, index=NUM + CAT).sort_values()
fig, ax = plt.subplots(figsize=(7, 4.5)); imp.plot.barh(color="#2c7fb8", ax=ax)
ax.set(title="Permutation importance (increase in RMSE when shuffled)", xlabel="RMSE increase")
plt.tight_layout(); plt.savefig(FIG / "11_feature_importance.png"); plt.close()
imp.sort_values(ascending=False).round(4).to_csv(OUT / "feature_importance.csv", header=["rmse_increase"])

GBP = {k[3:]: v for k, v in gs.best_params_.items()}
def build_best():
    """Fresh, unfitted copy of whichever regressor won on the holdout set."""
    m = Ridge(alpha=1.0) if best_name == "Ridge" else GradientBoostingRegressor(random_state=SEED, **GBP)
    return Pipeline([("pre", pre), ("m", m)])
final = build_best().fit(X, y)
joblib.dump(final, MODELS / "cgpa_regressor.joblib")
df["predicted_cgpa_s3_6"] = cross_val_predict(build_best(), X, y, cv=cv)

# ======================= B. CLASSIFICATION =======================
df["at_risk"] = (df.target_cgpa_s3_6 < RISK_THRESHOLD).astype(int)
yc = df["at_risk"]; prev = yc.mean()
Xtr, Xte, ytr, yte = train_test_split(X, yc, test_size=.2, random_state=SEED, stratify=yc)
skf = StratifiedKFold(5, shuffle=True, random_state=SEED)
clfs = {"Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "Random Forest": RandomForestClassifier(n_estimators=300, min_samples_leaf=3, class_weight="balanced", random_state=SEED, n_jobs=-1)}
rows, fitted = [], {}
for name, m in clfs.items():
    pipe = Pipeline([("pre", pre), ("m", m)]); auc = cross_val_score(pipe, Xtr, ytr, cv=skf, scoring="roc_auc")
    pipe.fit(Xtr, ytr); p = pipe.predict_proba(Xte)[:, 1]; lab = (p >= .5).astype(int)
    pr, rc, f1, _ = precision_recall_fscore_support(yte, lab, average="binary")
    rows.append({"model": name, "cv_auc": auc.mean(), "test_auc": roc_auc_score(yte, p), "precision": pr, "recall": rc, "f1": f1}); fitted[name] = (pipe, p)
clf_cmp = pd.DataFrame(rows).round(4); clf_cmp.to_csv(OUT / "model_comparison_classification.csv", index=False)
print(f"At-risk prevalence {prev:.1%}\n", clf_cmp)
best_c = clf_cmp.sort_values("test_auc", ascending=False).iloc[0]["model"]; pipe_c, p_c = fitted[best_c]

fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
for name, (_, p) in fitted.items():
    fpr, tpr, _ = roc_curve(yte, p); axes[0].plot(fpr, tpr, label=f"{name} (AUC {roc_auc_score(yte, p):.2f})")
axes[0].plot([0, 1], [0, 1], "k--"); axes[0].set(title="ROC curve - early-warning model", xlabel="False positive rate", ylabel="True positive rate"); axes[0].legend()
cm = confusion_matrix(yte, (p_c >= .5).astype(int))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=axes[1], xticklabels=["Not at risk", "At risk"], yticklabels=["Not at risk", "At risk"])
axes[1].set(title=f"Confusion matrix - {best_c}", xlabel="Predicted", ylabel="Actual")
plt.tight_layout(); plt.savefig(FIG / "12_classification_roc_confusion.png"); plt.close()
final_c = Pipeline([("pre", pre), ("m", clfs[best_c])]).fit(X, yc); joblib.dump(final_c, MODELS / "at_risk_classifier.joblib")
df["risk_probability"] = cross_val_predict(Pipeline([("pre", pre), ("m", clfs[best_c])]), X, yc, cv=skf, method="predict_proba")[:, 1].round(3)
df["risk_band"] = pd.cut(df.risk_probability, [-.01, .3, .6, 1.0], labels=["Low", "Medium", "High"])

# ======================= C. CLUSTERING =======================
CF = ["cgpa", "sgpa_trend", "sgpa_std", "avg_attendance", "weekly_study_hrs"]
Z = StandardScaler().fit_transform(df[CF])
sil = {k: silhouette_score(Z, KMeans(k, n_init=10, random_state=SEED).fit_predict(Z)) for k in range(2, 8)}
print("Silhouette by k:", {k: round(v, 3) for k, v in sil.items()})
K = 4  # chosen for interpretability; silhouette for k=2..7 is reported in outputs
km = KMeans(K, n_init=20, random_state=SEED).fit(Z); df["cluster_id"] = km.labels_
prof = df.groupby("cluster_id")[CF].mean()
names = {}
order = prof["cgpa"].sort_values(ascending=False).index.tolist()
names[order[0]] = "High achievers"; names[order[-1]] = "Needs support"
mid = order[1:-1]; mid_sorted = prof.loc[mid, "sgpa_trend"].sort_values(ascending=False).index.tolist()
names[mid_sorted[0]] = "Rising (low base)"; names[mid_sorted[1]] = "Steady middle"
df["cluster"] = df.cluster_id.map(names)
prof = df.groupby("cluster")[CF + ["at_risk"]].mean().round(2); prof["students"] = df.cluster.value_counts()
prof.to_csv(OUT / "cluster_profiles.csv"); print(prof)
pc = PCA(2, random_state=SEED).fit_transform(Z)
fig, ax = plt.subplots(figsize=(7.5, 5.5))
sns.scatterplot(x=pc[:, 0], y=pc[:, 1], hue=df.cluster, palette="Set2", s=26, ax=ax)
ax.set(title="Student archetypes (K-Means, PCA view)", xlabel="PC1", ylabel="PC2"); ax.legend(title="")
plt.tight_layout(); plt.savefig(FIG / "13_student_clusters.png"); plt.close()
pd.Series(sil, name="silhouette").rename_axis("k").round(4).to_csv(OUT / "silhouette_by_k.csv")

# ---------- exports for Power BI / Tableau / Excel ----------
out = df[["enrollment_no", "target_cgpa_s3_6", "predicted_cgpa_s3_6", "at_risk", "risk_probability", "risk_band", "cluster"]].copy()
out["target_cgpa_s3_6"] = out.target_cgpa_s3_6.round(2); out["predicted_cgpa_s3_6"] = out.predicted_cgpa_s3_6.round(2)
out.to_csv(PROC / "student_ml_insights.csv", index=False)
json.dump({"regression_holdout": test, "best_regressor": best_name, "best_params": gs.best_params_, "at_risk_threshold": RISK_THRESHOLD,
           "at_risk_prevalence": round(float(prev), 3), "best_classifier": best_c, "classification": clf_cmp.set_index("model").to_dict("index"),
           "silhouette": {str(k): round(v, 3) for k, v in sil.items()}, "top_features": imp.sort_values(ascending=False).head(5).round(3).to_dict()},
          open(OUT / "ml_metrics.json", "w"), indent=2)
print("saved models + insights")
