"""Step 3 - Exploratory analysis, statistical tests and publication-quality figures."""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from utils import PROC, FIG, OUT

sns.set_theme(style="whitegrid", context="notebook", palette="deep")
plt.rcParams.update({"figure.dpi": 130, "axes.titleweight": "bold", "axes.titlesize": 13})
ORDER = ["CSE", "IT", "ECE", "EE", "ME"]

S = pd.read_csv(PROC / "student_summary.csv")
R = pd.read_csv(PROC / "results_clean.csv")
SEM = pd.read_csv(PROC / "student_semester.csv").merge(S[["enrollment_no", "branch", "batch"]], on="enrollment_no")
D = pd.read_csv(PROC / "course_difficulty.csv")

def save(name):
    plt.tight_layout(); plt.savefig(FIG / name, bbox_inches="tight"); plt.close()

# 1 CGPA by branch
fig, ax = plt.subplots(figsize=(8, 4.5))
sns.violinplot(data=S, x="branch", y="cgpa", order=ORDER, inner="quartile", cut=0, ax=ax, hue="branch", legend=False)
ax.set(title="CGPA distribution by branch", xlabel="", ylabel="CGPA")
save("01_cgpa_by_branch.png")

# 2 SGPA trend
fig, ax = plt.subplots(figsize=(8, 4.5))
sns.lineplot(data=SEM, x="semester", y="sgpa", hue="branch", hue_order=ORDER, marker="o", errorbar=None, ax=ax)
ax.set(title="Average SGPA by semester", xlabel="Semester", ylabel="Mean SGPA"); ax.legend(title="")
save("02_sgpa_trend.png")

# 3 attendance vs CGPA
fig, ax = plt.subplots(figsize=(7, 5))
sns.regplot(data=S, x="avg_attendance", y="cgpa", scatter_kws={"alpha": .35, "s": 14}, line_kws={"color": "crimson"}, ax=ax)
ax.set(title="Attendance vs CGPA", xlabel="Average attendance (%)", ylabel="CGPA")
save("03_attendance_vs_cgpa.png")

# 4 branch x semester heatmap
hm = SEM.pivot_table(index="branch", columns="semester", values="sgpa", aggfunc="mean").loc[ORDER]
fig, ax = plt.subplots(figsize=(8, 3.8))
sns.heatmap(hm, annot=True, fmt=".2f", cmap="YlGnBu", ax=ax, cbar_kws={"label": "Mean SGPA"})
ax.set(title="Mean SGPA - branch x semester", xlabel="Semester", ylabel="")
save("04_branch_semester_heatmap.png")

# 5 hardest courses
top = D.sort_values("difficulty_index", ascending=False).head(12).copy()
top["label"] = top["course_name"] + " (" + top["branch_scope"] + ", S" + top["semester"].astype(str) + ")"
fig, ax = plt.subplots(figsize=(8, 5))
sns.barplot(data=top, y="label", x="difficulty_index", color="#c0392b", ax=ax)
ax.set(title="12 hardest courses (difficulty index 0-100)", xlabel="Difficulty index", ylabel="")
save("05_hardest_courses.png")

# 6 grade distribution
gd = pd.crosstab(R.merge(S[["enrollment_no", "branch"]], on="enrollment_no")["branch"], R.merge(S[["enrollment_no", "branch"]], on="enrollment_no")["grade"], normalize="index").loc[ORDER]
gd = gd[[g for g in ["O", "A+", "A", "B+", "B", "C", "P", "F"] if g in gd.columns]] * 100
gd.plot(kind="barh", stacked=True, figsize=(9, 4), colormap="RdYlGn_r")
plt.title("Grade distribution by branch (%)"); plt.xlabel("% of results"); plt.ylabel(""); plt.legend(title="Grade", bbox_to_anchor=(1, 1))
save("06_grade_distribution.png")

# 7 correlation heatmap
num = S[["cgpa", "avg_attendance", "board_pct", "entrance_percentile", "weekly_study_hrs", "sgpa_s1", "sgpa_s2", "sgpa_trend", "total_backlogs"]]
fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(num.corr(), annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax)
ax.set_title("Correlation matrix")
save("07_correlation_heatmap.png")

# 8 rank ribbon for an example student (the "Result Hub" view)
ex = S[(S.branch == "ECE") & (S.batch == 2022)].sort_values("cgpa", ascending=False).iloc[21]
coh = S[(S.branch == ex.branch) & (S.batch == ex.batch)]
fig, ax = plt.subplots(figsize=(8, 3.6))
sns.histplot(coh["cgpa"], bins=18, color="#9bb1d1", ax=ax)
ax.axvline(ex.cgpa, color="#f2a900", lw=3)
ax.text(ex.cgpa - .1, ax.get_ylim()[1] * .95, f"{ex.enrollment_no}\nCGPA {ex.cgpa:.2f}\nTop {int(ex.top_percent)}% (rank {int(ex.branch_rank)}/{int(ex.cohort_size)})", ha="right", va="top", bbox=dict(facecolor="white", edgecolor="none", alpha=.85))
ax.set(title=f"Where one student sits in the {ex.branch} {int(ex.batch)} cohort", xlabel="CGPA", ylabel="Students")
save("08_rank_ribbon_example.png")

# 9 study hours x residence
fig, ax = plt.subplots(figsize=(7.5, 4.8))
sns.scatterplot(data=S, x="weekly_study_hrs", y="cgpa", hue="residence", alpha=.5, s=22, ax=ax)
ax.set(title="Self-study hours vs CGPA", xlabel="Weekly self-study hours", ylabel="CGPA")
save("09_study_hours_vs_cgpa.png")

# ---------- statistical tests ----------
tests = {}
f, p = stats.f_oneway(*[S[S.branch == b].cgpa for b in ORDER])
tests["anova_cgpa_by_branch"] = {"F": round(f, 2), "p": float(p)}
h, d = S[S.residence == "Hostel"].cgpa, S[S.residence == "Day Scholar"].cgpa
t, p = stats.ttest_ind(h, d, equal_var=False)
tests["welch_t_hostel_vs_day"] = {"t": round(t, 2), "p": float(p), "mean_hostel": round(h.mean(), 3), "mean_day": round(d.mean(), 3)}
m, fm = S[S.gender == "Male"].cgpa, S[S.gender == "Female"].cgpa
t, p = stats.ttest_ind(m, fm, equal_var=False)
tests["welch_t_gender"] = {"t": round(t, 2), "p": float(p), "mean_male": round(m.mean(), 3), "mean_female": round(fm.mean(), 3)}
r, p = stats.pearsonr(S.avg_attendance, S.cgpa)
tests["pearson_attendance_cgpa"] = {"r": round(r, 3), "p": float(p)}
r, p = stats.spearmanr(S.weekly_study_hrs, S.cgpa)
tests["spearman_study_hours_cgpa"] = {"rho": round(r, 3), "p": float(p)}
r, p = stats.pearsonr(S.board_pct, S.cgpa)
tests["pearson_board_cgpa"] = {"r": round(r, 3), "p": float(p)}
e1, e2 = S[S.batch == 2021].cgpa, S[S.batch == 2022].cgpa
t, p = stats.ttest_ind(e1, e2, equal_var=False)
tests["welch_t_batch_2021_vs_2022"] = {"t": round(t, 2), "p": float(p), "mean_2021": round(e1.mean(), 3), "mean_2022": round(e2.mean(), 3)}
low = R.groupby("enrollment_no").attendance_pct.mean() < 75
tests["share_students_below_75pct_attendance"] = round(float(low.mean()), 3)
b = S.groupby("branch").cgpa.agg(["mean", "median", "std"]).round(2).loc[ORDER]
tests["branch_table"] = b.to_dict("index")
tests["hardest_course"] = D.sort_values("difficulty_index", ascending=False).iloc[0][["course_name", "branch_scope", "semester", "difficulty_index"]].to_dict()
tests["easiest_theory_course"] = D[D.course_type == "Theory"].sort_values("difficulty_index").iloc[0][["course_name", "branch_scope", "semester", "difficulty_index"]].to_dict()
json.dump(tests, open(OUT / "stats_tests.json", "w"), indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o))
print(json.dumps(tests, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))[:1800])
