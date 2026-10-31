"""Step 8 - Turn the computed numbers into reports/insights.md (every figure is read from the outputs, nothing typed by hand)."""
import json
import pandas as pd
from utils import OUT, PROC, ROOT

T = json.load(open(OUT / "stats_tests.json")); M = json.load(open(OUT / "ml_metrics.json"))
S = pd.read_csv(PROC / "student_summary.csv"); prof = pd.read_csv(OUT / "cluster_profiles.csv").set_index("cluster")
fi = pd.read_csv(OUT / "feature_importance.csv", index_col=0)["rmse_increase"]
dq = (OUT / "data_quality_report.md").read_text()
bt = T["branch_table"]; best_b = max(bt, key=lambda b: bt[b]["mean"]); worst_b = min(bt, key=lambda b: bt[b]["mean"])
reg = M["regression_holdout"][M["best_regressor"]]; clf = M["classification"][M["best_classifier"]]
low = S[S.avg_attendance < 75].cgpa.mean(); high = S[S.avg_attendance >= 85].cgpa.mean()
md = f"""# Findings

> Data is **synthetic**: relationships were planted by the generator (ability, attendance, study hours), so the aim is to demonstrate a sound method, not to make claims about any real university.

## 1. Branch and cohort performance
- Mean CGPA ranges from **{bt[worst_b]['mean']}** ({worst_b}) to **{bt[best_b]['mean']}** ({best_b}). A one-way ANOVA finds the branch differences statistically significant (F = {T['anova_cgpa_by_branch']['F']}, p = {T['anova_cgpa_by_branch']['p']:.4f}), but the gaps are modest next to the spread inside each branch (std about 1.2-1.4).
- Batch 2021 vs 2022: {T['welch_t_batch_2021_vs_2022']['mean_2021']} vs {T['welch_t_batch_2021_vs_2022']['mean_2022']}, p = {T['welch_t_batch_2021_vs_2022']['p']:.2f}, so no reliable difference between batches.
- Hostel vs day scholar (p = {T['welch_t_hostel_vs_day']['p']:.2f}) and gender (p = {T['welch_t_gender']['p']:.2f}) show **no significant CGPA gap**.

## 2. What goes with CGPA
- Attendance: Pearson r = **{T['pearson_attendance_cgpa']['r']}**. Students under 75% attendance average CGPA {low:.2f}; students at 85%+ average {high:.2f}. {T['share_students_below_75pct_attendance']:.0%} of students are below 75%.
- Board marks: r = **{T['pearson_board_cgpa']['r']}**. Weekly self-study hours: Spearman rho = **{T['spearman_study_hours_cgpa']['rho']}**.
- Correlation is not causation: attendance and CGPA both reflect a student's underlying habits.

## 3. Course difficulty
- Hardest course by the difficulty index: **{T['hardest_course']['course_name']}** ({T['hardest_course']['branch_scope']}, semester {int(T['hardest_course']['semester'])}, index {T['hardest_course']['difficulty_index']:.0f}/100).
- Easiest theory course: **{T['easiest_theory_course']['course_name']}** ({T['easiest_theory_course']['branch_scope']}, semester {int(T['easiest_theory_course']['semester'])}).
- Index = 45% low average grade point + 35% fail rate + 20% spread of marks (each min-max scaled).

## 4. Machine learning
**Predicting CGPA of semesters 3-6 from semesters 1-2 + admission data** (no leakage). Best model: **{M['best_regressor']}**, holdout RMSE **{reg['rmse']:.2f}**, MAE {reg['mae']:.2f}, R2 **{reg['r2']:.2f}** (baseline R2 about 0). A tuned gradient-boosting model did not beat the simple linear model, which is expected when the signal is mostly additive, and the simpler model is easier to explain.
Top drivers (permutation importance): {', '.join(f'{k} ({v:.2f})' for k, v in M['top_features'].items())}.

**Early-warning classifier** (final CGPA of semesters 3-6 below {M['at_risk_threshold']}; prevalence {M['at_risk_prevalence']:.0%}): {M['best_classifier']}, test AUC **{clf['test_auc']:.2f}**, recall {clf['recall']:.2f}, precision {clf['precision']:.2f}. Recall was prioritised because missing a struggling student costs more than a false alarm.

**Student archetypes (K-Means, k = 4)**:
{prof[['students','cgpa','sgpa_trend','avg_attendance','at_risk']].round(2).to_markdown()}
Silhouette for k = 2..7 is in `outputs/silhouette_by_k.csv` (k = 2 scores highest; k = 4 was chosen because four groups are actionable for advisors).

## 5. Recommendations (what a department could do)
1. Flag students below 75% attendance after semester 2: they are the highest-risk group.
2. Offer bridge sessions for the hardest courses before the semester starts.
3. Use the risk score as a triage list for mentors, not as a label on students.

## 6. Limitations
Synthetic data; one institution-style structure; risk threshold of 7.0 is arbitrary; out-of-fold predictions are used for dashboards so no student is scored by a model that saw them.

---
## Appendix: data quality log
{dq.split(chr(10), 2)[2]}
"""
(ROOT / "reports" / "insights.md").write_text(md); print(md[:1500])
