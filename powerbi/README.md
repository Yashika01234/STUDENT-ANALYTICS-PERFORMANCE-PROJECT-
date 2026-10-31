# Power BI build guide (about 30 minutes)

A `.pbix` file is a binary that only Power BI Desktop can author, so this folder gives you everything needed to build it quickly and exactly:
clean star-schema CSVs, DAX measures, a theme, Power Query code and the page-by-page report spec.

## 1. Load the data
Home > Get Data > Text/CSV, load every file in `data/` (or use `load_data.m`). Keep `user_map` and `hod_map` only if you want row-level security.

## 2. Model (Model view)
| From (one) | To (many) | Column |
|---|---|---|
| dim_branch[branch] | dim_student[branch] | branch |
| dim_student[enrollment_no] | fact_results[enrollment_no] | enrollment_no |
| dim_student[enrollment_no] | fact_student_semester[enrollment_no] | enrollment_no |
| dim_student[enrollment_no] | fact_student_summary[enrollment_no] | enrollment_no (1:1) |
| dim_course[course_id] | fact_results[course_id] | course_id |
| dim_course[course_id] | course_difficulty[course_id] | course_id (1:1) |
| dim_semester[semester] | fact_results[semester] and fact_student_semester[semester] | semester |

Cross-filter direction: single (dim to fact). Hide key columns in the fact tables. Import `theme.json` (View > Themes > Browse for themes).

## 3. Measures
Create a `_Measures` table and paste the measures from `measures.dax`. Add the three calculated columns listed at the bottom of that file.

## 4. Report pages
| Page | Visuals |
|---|---|
| 1. Overview | Cards: Students, Avg CGPA, % CGPA >= 8, Avg Attendance, High Risk %. Clustered column: Avg CGPA by branch (legend: batch). Line: Avg SGPA by semester (legend: branch). Slicers: batch, branch, gender, residence. |
| 2. My Result (Result Hub) | Single-select slicer on `enrollment_no` (search enabled). Cards: Selected CGPA, Cohort Rank, Top % Label, Percentile. Line: Avg SGPA by semester vs Branch benchmark (use a second line measure). Column chart of count of students by `cgpa_bin` filtered to the cohort. Set this page as drill-through target from the Overview. |
| 3. Course Difficulty | Matrix (branch rows x semester columns, Avg Grade Point, conditional-format background). Bar: top 15 `course_label` by Avg Difficulty Index. Scatter: x = average grade point, y = fail rate, size = students, details = course. |
| 4. Early Warning and Segments | Donut: students by `risk_band`. Scatter: `avg_attendance` vs `cgpa` coloured by `cluster`. Table of High-risk students with `risk_probability` (data bars) and `predicted_cgpa_s3_6`. Cards: Model MAE (CGPA), Actual At-Risk % in High Band. |

## 5. Polish for the interview
- Bookmarks + buttons for "Branch view" and "Cohort view".
- Tooltip page showing a student's SGPA sparkline.
- Row-level security: roles `Student` and `HOD` from `measures.dax`; test with View as.
- Publish to a workspace and pin Overview to a dashboard (or export screenshots into `reports/`).
