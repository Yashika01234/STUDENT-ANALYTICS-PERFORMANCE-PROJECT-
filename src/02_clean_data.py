"""Step 2 - Clean raw data, validate it, and build analysis-ready tables.

Outputs (data/processed): students_clean, courses, results_clean, student_semester,
student_summary, course_difficulty + outputs/data_quality_report.md
"""
import numpy as np
import pandas as pd
from utils import RAW, PROC, OUT, grade_letter, grade_point, difficulty_index

log = []
def note(msg):
    print(msg); log.append(msg)

students = pd.read_csv(RAW / "students_raw.csv")
results = pd.read_csv(RAW / "results_raw.csv")
courses = pd.read_csv(RAW / "courses.csv")
note(f"Loaded raw: students={len(students)}, results={len(results)}, courses={len(courses)}")

# ---------- students ----------
BRANCH_MAP = {"cse": "CSE", "computer science": "CSE", "c.s.e": "CSE", "it": "IT", "information technology": "IT",
              "ece": "ECE", "e.c.e": "ECE", "ee": "EE", "electrical": "EE", "me": "ME", "mechanical": "ME"}
bad = (~students["branch"].isin(["CSE", "IT", "ECE", "EE", "ME"])).sum()
students["branch"] = students["branch"].str.strip().str.lower().map(BRANCH_MAP)
note(f"Standardised {bad} non-canonical branch labels (case, spaces, long names)")
assert students["branch"].notna().all()

gmap = {"m": "Male", "male": "Male", "f": "Female", "female": "Female"}
bad = (~students["gender"].isin(["Male", "Female"])).sum()
students["gender"] = students["gender"].str.strip().str.lower().map(gmap)
note(f"Standardised {bad} gender labels")

d = students.duplicated().sum()
students = students.drop_duplicates().drop_duplicates("enrollment_no")
note(f"Removed {d} exact duplicate student rows")

miss = students["board_pct"].isna().sum()
med = students.groupby("branch")["board_pct"].transform("median")
students["board_pct_imputed"] = students["board_pct"].isna()
students["board_pct"] = students["board_pct"].fillna(med).round(1)
note(f"Imputed {miss} missing board_pct with the branch median (flagged in board_pct_imputed)")

# ---------- results ----------
d = results.duplicated(["enrollment_no", "course_id"]).sum()
results = results.drop_duplicates(["enrollment_no", "course_id"])
note(f"Removed {d} duplicate (student, course) result rows")

m = results["total_marks"].isna().sum()
results["total_marks"] = results["total_marks"].fillna(results["internal_marks"] + results["external_marks"])
note(f"Recomputed {m} missing total_marks as internal + external")
assert (results["total_marks"] == results["internal_marks"] + results["external_marks"]).all()

m = results["attendance_pct"].isna().sum()
results["attendance_imputed"] = results["attendance_pct"].isna()
fill = results.groupby(["enrollment_no", "semester"])["attendance_pct"].transform("mean")
results["attendance_pct"] = results["attendance_pct"].fillna(fill).fillna(results["attendance_pct"].median()).round(1)
note(f"Imputed {m} missing attendance values with the student's semester mean (flagged)")

results["grade_check"] = grade_letter(results["total_marks"])
mism = (results["grade_check"] != results["grade"]).sum()
note(f"Grade validation: {mism} rows where stored grade != grade derived from marks")
results["grade"] = results["grade_check"]; results = results.drop(columns="grade_check")
results["grade_point"] = grade_point(results["total_marks"])
results["passed"] = (results["grade_point"] > 0).astype(int)

assert results["total_marks"].between(0, 100).all() and results["attendance_pct"].between(0, 100).all()
assert set(results["enrollment_no"]) <= set(students["enrollment_no"])
assert set(results["course_id"]) <= set(courses["course_id"])
note("Integrity checks passed: marks/attendance within range, no orphan keys")

results = results.merge(courses[["course_id", "credits", "course_type"]], on="course_id", how="left")

# ---------- student x semester ----------
def sgpa(df):
    return pd.Series({"sgpa": (df["grade_point"] * df["credits"]).sum() / df["credits"].sum(),
                      "credits_attempted": df["credits"].sum(),
                      "credits_earned": (df["credits"] * df["passed"]).sum(),
                      "backlogs": int((df["passed"] == 0).sum()),
                      "avg_attendance": df["attendance_pct"].mean()})
sem = results.groupby(["enrollment_no", "semester"]).apply(sgpa, include_groups=False).reset_index()
sem["sgpa"] = sem["sgpa"].round(2); sem["avg_attendance"] = sem["avg_attendance"].round(1)

# ---------- student summary (the "Result Hub" table) ----------
agg = results.assign(gpxc=results["grade_point"] * results["credits"]).groupby("enrollment_no").agg(
    gpxc=("gpxc", "sum"), credits=("credits", "sum"), total_backlogs=("passed", lambda x: int((x == 0).sum())),
    avg_attendance=("attendance_pct", "mean"))
agg["cgpa"] = (agg["gpxc"] / agg["credits"]).round(2)
piv = sem.pivot(index="enrollment_no", columns="semester", values="sgpa"); piv.columns = [f"sgpa_s{c}" for c in piv.columns]
summ = students.merge(agg[["cgpa", "total_backlogs", "avg_attendance"]].reset_index(), on="enrollment_no").merge(piv.reset_index(), on="enrollment_no")
summ["avg_attendance"] = summ["avg_attendance"].round(1)
summ["sgpa_trend"] = [np.polyfit(range(1, 7), r, 1)[0] for r in summ[[f"sgpa_s{i}" for i in range(1, 7)]].to_numpy()]
summ["sgpa_trend"] = summ["sgpa_trend"].round(3)
summ["sgpa_std"] = summ[[f"sgpa_s{i}" for i in range(1, 7)]].std(axis=1).round(3)
g = summ.groupby(["branch", "batch"])["cgpa"]
summ["branch_rank"] = g.rank(method="min", ascending=False).astype(int)
summ["cohort_size"] = g.transform("size")
summ["top_percent"] = np.ceil(summ["branch_rank"] / summ["cohort_size"] * 100).astype(int)
summ["percentile"] = ((1 - (summ["branch_rank"] - 1) / summ["cohort_size"]) * 100).round(1)
summ["overall_rank"] = summ["cgpa"].rank(method="min", ascending=False).astype(int)

diff = difficulty_index(results).merge(courses, on="course_id")
diff["difficulty_rank"] = diff["difficulty_index"].rank(ascending=False, method="min").astype(int)

students.to_csv(PROC / "students_clean.csv", index=False)
courses.to_csv(PROC / "courses.csv", index=False)
results.to_csv(PROC / "results_clean.csv", index=False)
sem.to_csv(PROC / "student_semester.csv", index=False)
summ.to_csv(PROC / "student_summary.csv", index=False)
diff.round(3).to_csv(PROC / "course_difficulty.csv", index=False)

note(f"Built tables: students={len(students)}, results={len(results)}, student_semester={len(sem)}, student_summary={len(summ)}, courses={len(diff)}")
(OUT / "data_quality_report.md").write_text("# Data quality report\n\n" + "\n".join(f"- {l}" for l in log) + "\n")
print(summ[["enrollment_no", "branch", "cgpa", "branch_rank", "top_percent"]].head())
