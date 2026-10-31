"""Step 9 - Build and execute notebooks/analysis.ipynb (narrated walkthrough with live outputs)."""
import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor
from utils import ROOT

md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
cells = [
md("""# Student Performance Analytics - walkthrough
Synthetic university results data (1,000 students, 5 branches, 2 batches, 6 semesters, 24,000 course results).
**Questions:** Where does a student rank in their branch? Which factors move CGPA? Which courses are hardest? Can we flag at-risk students after semester 2?"""),
code("""import pandas as pd, numpy as np, matplotlib.pyplot as plt, seaborn as sns, joblib, json
from scipy import stats
sns.set_theme(style="whitegrid"); pd.options.display.float_format = "{:.2f}".format
P = "../data/processed/"
S = pd.read_csv(P+"student_summary.csv"); R = pd.read_csv(P+"results_clean.csv")
SEM = pd.read_csv(P+"student_semester.csv"); D = pd.read_csv(P+"course_difficulty.csv"); ML = pd.read_csv(P+"student_ml_insights.csv")
S.shape, R.shape"""),
md("## 1. Data quality (from the cleaning step)"),
code("print(open('../outputs/data_quality_report.md').read())"),
md("## 2. Result-Hub lookup: rank, percentile and cohort position"),
code("""def result_hub(eid):
    r = S[S.enrollment_no == eid].iloc[0]
    print(f"{eid} | {r.branch} batch {r.batch}\\nCGPA {r.cgpa:.2f} | rank {r.branch_rank}/{r.cohort_size} | Top {r.top_percent}% | percentile {r.percentile}")
    print("SGPA by semester:", [r[f'sgpa_s{i}'] for i in range(1,7)])
result_hub("2022UEC0094")"""),
code("""coh = S[(S.branch=="ECE")&(S.batch==2022)]
ax = sns.histplot(coh.cgpa, bins=18, color="#9bb1d1"); ax.axvline(8.67, color="#f2a900", lw=3); ax.set_title("ECE 2022 CGPA distribution (marker = 2022UEC0094)"); plt.show()"""),
md("## 3. Branch comparison and statistical test"),
code("""print(S.groupby('branch').cgpa.agg(['count','mean','median','std']))
print(stats.f_oneway(*[g.cgpa.values for _, g in S.groupby('branch')]))
sns.boxplot(data=S, x='branch', y='cgpa', hue='batch'); plt.title('CGPA by branch and batch'); plt.show()"""),
md("## 4. Drivers of CGPA"),
code("""cols = ['cgpa','avg_attendance','board_pct','entrance_percentile','weekly_study_hrs','sgpa_s1','sgpa_trend']
sns.heatmap(S[cols].corr(), annot=True, cmap='coolwarm', center=0); plt.show()
S['att_band'] = pd.cut(S.avg_attendance, [0,65,75,85,100], labels=['<65','65-75','75-85','85+'])
S.groupby('att_band', observed=True).agg(students=('cgpa','size'), avg_cgpa=('cgpa','mean'), avg_backlogs=('total_backlogs','mean'))"""),
md("## 5. Course difficulty (index = 45% low grade point, 35% fail rate, 20% mark spread)"),
code("""D.sort_values('difficulty_index', ascending=False)[['course_name','branch_scope','semester','avg_gp','fail_rate','difficulty_index']].head(10)"""),
md("## 6. Early-warning model (features known after semester 2 only)"),
code("""m = json.load(open('../outputs/ml_metrics.json'))
print('Best regressor:', m['best_regressor'], m['regression_holdout'][m['best_regressor']])
print('Best classifier:', m['best_classifier'], m['classification'][m['best_classifier']])
pd.read_csv('../outputs/model_comparison_regression.csv')"""),
code("""from IPython.display import Image, display
for f in ['10_pred_vs_actual.png','11_feature_importance.png','12_classification_roc_confusion.png','13_student_clusters.png']:
    display(Image('../reports/figures/'+f, width=640))"""),
code("""# Do the risk bands line up with what actually happened?
x = S.merge(ML, on='enrollment_no')
x.groupby('risk_band', observed=True).agg(students=('cgpa','size'), actual_cgpa_s3_6=('target_cgpa_s3_6','mean'), pct_actually_at_risk=('at_risk','mean'))"""),
md("""## 7. Takeaways
Attendance, board marks and early SGPA explain most of the variation in later CGPA; branch, gender and hostel status matter far less. A linear model beats boosted trees here, so the simpler, explainable model wins. See `reports/insights.md` for the full write-up and caveats."""),
]
nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}})
ExecutePreprocessor(timeout=300, kernel_name="python3", resources={"metadata": {"path": str(ROOT / "notebooks")}}).preprocess(nb, {"metadata": {"path": str(ROOT / "notebooks")}})
nbf.write(nb, ROOT / "notebooks" / "analysis.ipynb"); print("notebook executed")
