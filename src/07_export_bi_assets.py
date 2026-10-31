"""Step 7 - Export Power BI (star schema) and Tableau (flat) data sources."""
import pandas as pd
from utils import PROC, ROOT

S = pd.read_csv(PROC / "student_summary.csv"); ML = pd.read_csv(PROC / "student_ml_insights.csv")
SEM = pd.read_csv(PROC / "student_semester.csv"); R = pd.read_csv(PROC / "results_clean.csv")
C = pd.read_csv(PROC / "courses.csv"); D = pd.read_csv(PROC / "course_difficulty.csv"); ST = pd.read_csv(PROC / "students_clean.csv")
PB, TB = ROOT / "powerbi" / "data", ROOT / "tableau" / "data"

# ---------------- Power BI star schema ----------------
dim_student = ST[["enrollment_no", "branch", "batch", "gender", "residence", "board_pct", "entrance_percentile", "weekly_study_hrs", "extracurricular"]].copy()
dim_student["cohort"] = dim_student.branch + " " + dim_student.batch.astype(str)
dim_branch = pd.DataFrame({"branch": ["CSE", "IT", "ECE", "EE", "ME"], "branch_code": ["UCS", "UIT", "UEC", "UEE", "UME"],
    "branch_name": ["Computer Science and Engineering", "Information Technology", "Electronics and Communication Engineering", "Electrical Engineering", "Mechanical Engineering"]})
dim_sem = pd.DataFrame({"semester": range(1, 7)}); dim_sem["year_of_study"] = (dim_sem.semester + 1) // 2
dim_sem["season"] = dim_sem.semester.map(lambda s: "Odd" if s % 2 else "Even"); dim_sem["label"] = "Sem " + dim_sem.semester.astype(str)
fact_results = R[["enrollment_no", "course_id", "semester", "internal_marks", "external_marks", "total_marks", "grade", "grade_point", "passed", "attendance_pct"]]
fact_sem = SEM[["enrollment_no", "semester", "sgpa", "credits_attempted", "credits_earned", "backlogs", "avg_attendance"]]
fact_sum = S.merge(ML, on="enrollment_no")[["enrollment_no", "branch", "batch", "cgpa", "branch_rank", "cohort_size", "top_percent", "percentile", "overall_rank",
    "total_backlogs", "avg_attendance", "sgpa_trend", "sgpa_std", "target_cgpa_s3_6", "predicted_cgpa_s3_6", "at_risk", "risk_probability", "risk_band", "cluster"]]
for n, d in {"dim_student": dim_student, "dim_course": C, "dim_branch": dim_branch, "dim_semester": dim_sem, "fact_results": fact_results,
             "fact_student_semester": fact_sem, "fact_student_summary": fact_sum, "course_difficulty": D.round(3)}.items():
    d.to_csv(PB / f"{n}.csv", index=False)
pd.DataFrame({"email": ["student.2022uec0094@example.com", "student.2021ucs0001@example.com"], "enrollment_no": ["2022UEC0094", "2021UCS0001"]}).to_csv(PB / "user_map.csv", index=False)
pd.DataFrame({"email": ["hod.ece@example.com", "hod.cse@example.com"], "branch": ["ECE", "CSE"]}).to_csv(PB / "hod_map.csv", index=False)

# ---------------- Tableau flat files ----------------
stu = S.merge(ML, on="enrollment_no").merge(ST[["enrollment_no", "gender"]].rename(columns={"gender": "gender_dup"}), on="enrollment_no").drop(columns="gender_dup")
stu.to_csv(TB / "student_level.csv", index=False)
SEM.merge(ST[["enrollment_no", "branch", "batch", "gender", "residence"]], on="enrollment_no").to_csv(TB / "student_semester_level.csv", index=False)
R.merge(C[["course_id", "course_name", "branch_scope"]], on="course_id").merge(ST[["enrollment_no", "branch", "batch", "gender", "residence"]], on="enrollment_no").to_csv(TB / "result_level.csv", index=False)
D.round(3).to_csv(TB / "course_level.csv", index=False)
print("exported", sorted(p.name for p in PB.iterdir()), sorted(p.name for p in TB.iterdir()))
