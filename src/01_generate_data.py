"""Step 1 - Generate a realistic SYNTHETIC university results dataset (raw, deliberately messy).

No real student data is used. A hidden 'ability', 'attendance habit', 'study hours' and 'trend'
drive the marks, so the later analysis and ML have real signal to discover.
"""
import numpy as np
import pandas as pd
from utils import RAW, grade_letter

rng = np.random.default_rng(42)
BRANCHES = {"CSE": ("UCS", 0.30), "IT": ("UIT", 0.22), "ECE": ("UEC", 0.00), "EE": ("UEE", -0.12), "ME": ("UME", -0.25)}
BATCHES = [2021, 2022]
N_PER = 100  # students per branch per batch -> 1,000 students

SPEC = {
 "CSE": ["Data Structures", "Discrete Mathematics", "Digital Logic Design", "Operating Systems", "Computer Organisation", "Database Systems",
         "Design and Analysis of Algorithms", "Computer Networks", "Theory of Computation", "Compiler Design", "Machine Learning", "Software Engineering"],
 "IT":  ["Data Structures", "Discrete Mathematics", "Web Technologies", "Operating Systems", "Database Systems", "Computer Networks",
         "Algorithms", "Information Security", "Cloud Computing", "Data Mining", "Software Engineering", "Machine Learning"],
 "ECE": ["Signals and Systems", "Analog Circuits", "Digital Electronics", "Electromagnetic Theory", "Network Analysis", "Communication Systems",
         "Microprocessors", "Control Systems", "Digital Signal Processing", "VLSI Design", "Antenna Theory", "Embedded Systems"],
 "EE":  ["Circuit Theory", "Electrical Machines-I", "Electromagnetic Fields", "Network Analysis", "Electrical Machines-II", "Power Systems-I",
         "Control Systems", "Measurements", "Power Electronics", "Power Systems-II", "Electric Drives", "Digital Signal Processing"],
 "ME":  ["Thermodynamics", "Fluid Mechanics", "Strength of Materials", "Kinematics of Machines", "Heat Transfer", "Manufacturing Processes",
         "Machine Design", "Dynamics of Machines", "Metrology", "Refrigeration and AC", "Finite Element Methods", "Industrial Engineering"],
}
COMMON = [(1, "Engineering Mathematics-I", "Theory", 4, .75), (1, "Engineering Physics", "Theory", 4, .55),
          (1, "Programming Fundamentals", "Theory", 4, .45), (1, "Physics Lab", "Lab", 2, .15),
          (2, "Engineering Mathematics-II", "Theory", 4, .80), (2, "Engineering Chemistry", "Theory", 4, .50),
          (2, "Basic Electrical Engineering", "Theory", 4, .60), (2, "Chemistry Lab", "Lab", 2, .15)]

courses = []
for k, (sem, name, typ, cr, d) in enumerate(COMMON):
    courses.append(dict(course_id=f"COM-S{sem}-{k % 4 + 1}", course_name=name, branch_scope="ALL", semester=sem, course_type=typ, credits=cr, _d=d))
for b, (code, _) in BRANCHES.items():
    for s in range(3, 7):
        names = SPEC[b][3 * (s - 3): 3 * (s - 3) + 3]
        for k, n in enumerate(names):
            courses.append(dict(course_id=f"{code}-S{s}-{k+1}", course_name=n, branch_scope=b, semester=s, course_type="Theory", credits=4, _d=rng.uniform(.35, .95)))
        courses.append(dict(course_id=f"{code}-S{s}-4", course_name=f"Departmental Lab-{s-2}", branch_scope=b, semester=s, course_type="Lab", credits=2, _d=.15))
cdf = pd.DataFrame(courses)

students, results = [], []
for batch in BATCHES:
    for b, (code, off) in BRANCHES.items():
        sub = cdf[cdf.branch_scope.isin(["ALL", b])]
        for i in range(1, N_PER + 1):
            eid = f"{batch}{code}{i:04d}"
            a = rng.normal(off, 1.0)                                   # latent ability
            board = float(np.clip(86 + 4.5 * a + rng.normal(0, 3), 60, 99.5))
            ent = float(np.clip(93 + 3.5 * a + rng.normal(0, 2.5), 70, 99.99))
            study = float(np.clip(rng.normal(2.2 + .35 * a, 1.0), .3, 7))
            att0 = float(np.clip(78 + 4 * a + rng.normal(0, 6), 50, 98))
            trend = rng.normal(0, 1.2)
            students.append(dict(enrollment_no=eid, branch=b, batch=batch, gender=str(rng.choice(["Male", "Female"], p=[.68, .32])),
                                 residence=str(rng.choice(["Hostel", "Day Scholar"], p=[.45, .55])), board_pct=round(board, 1),
                                 entrance_percentile=round(ent, 2), weekly_study_hrs=round(study, 1),
                                 extracurricular=str(rng.choice(["Yes", "No"], p=[.35, .65]))))
            n = len(sub)
            att = np.clip(att0 + rng.normal(0, 6, n), 35, 100)
            lab = (sub.course_type == "Lab").to_numpy()
            base = (70 + 10.5 * a + .35 * (att - 75) + 1.8 * (study - 2.2) - 22 * (sub._d.to_numpy() - .5)
                    + trend * (sub.semester.to_numpy() - 3.5) + rng.normal(0, 7.5, n))
            base = np.where(lab, base + 12 - rng.normal(0, 2, n), base)
            total = np.clip(np.round(base), 0, 100)
            internal = np.clip(np.round(total * .4 + rng.normal(0, 2.5, n)), 0, 40)
            external = np.clip(total - internal, 0, 60)
            total = internal + external
            for j in range(n):
                results.append((eid, sub.course_id.iloc[j], int(sub.semester.iloc[j]), int(internal[j]), int(external[j]), int(total[j]),
                                str(grade_letter(total[j])), round(float(att[j]), 1)))

sdf = pd.DataFrame(students)
rdf = pd.DataFrame(results, columns=["enrollment_no", "course_id", "semester", "internal_marks", "external_marks", "total_marks", "grade", "attendance_pct"])

# ---- inject realistic mess into the RAW files (fixed in step 2) ----
variants = {"CSE": ["cse", "Computer Science", " CSE"], "IT": ["it", "Information Technology"], "ECE": ["ece", "E.C.E", " ECE "],
            "EE": ["ee", "Electrical"], "ME": ["me", "Mechanical"]}
messy = sdf.copy()
for idx in messy.sample(frac=.10, random_state=1).index:
    messy.loc[idx, "branch"] = str(rng.choice(variants[messy.loc[idx, "branch"]]))
for idx in messy.sample(frac=.10, random_state=2).index:
    messy.loc[idx, "gender"] = str({"Male": rng.choice(["M", "male"]), "Female": rng.choice(["F", "female"])}[messy.loc[idx, "gender"]])
messy.loc[messy.sample(frac=.03, random_state=3).index, "board_pct"] = np.nan
messy = pd.concat([messy, messy.sample(10, random_state=4)], ignore_index=True)

rmess = rdf.copy()
rmess["attendance_pct"] = rmess["attendance_pct"].astype(float)
rmess["total_marks"] = rmess["total_marks"].astype(float)
rmess.loc[rmess.sample(frac=.025, random_state=5).index, "attendance_pct"] = np.nan
rmess.loc[rmess.sample(frac=.01, random_state=6).index, "total_marks"] = np.nan
rmess = pd.concat([rmess, rmess.sample(40, random_state=7)], ignore_index=True)

messy.to_csv(RAW / "students_raw.csv", index=False)
rmess.to_csv(RAW / "results_raw.csv", index=False)
cdf.drop(columns="_d").to_csv(RAW / "courses.csv", index=False)
print(f"students_raw {messy.shape}, results_raw {rmess.shape}, courses {cdf.shape}")
