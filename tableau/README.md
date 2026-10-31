# Tableau build guide (about 30 minutes)

Tableau workbooks (`.twbx`) are authored in Tableau Desktop/Public (free), so this folder gives you clean flat data sources and exact calculated fields.

## Data sources (`data/`)
| File | Grain | Use for |
|---|---|---|
| student_level.csv | 1 row per student (1,000) | Result Hub, rank/percentile, ML risk and clusters |
| student_semester_level.csv | student x semester (6,000) | SGPA trends |
| result_level.csv | student x course (24,000) | grades, course difficulty |
| course_level.csv | 1 row per course (88) | difficulty index, fail rate |

Connect to Text file. For one workbook with several sources, add student_level and student_semester_level as separate data sources and blend on `Enrollment No`.

## Parameters
- **Selected Student** (String, list or typed): default `2022UEC0094`.
- **CGPA Threshold** (Float, 5 to 10, step 0.25): default 8.

## Calculated fields (student_level)
```
Cohort Size          { FIXED [Branch], [Batch] : COUNTD([Enrollment No]) }
Cohort Avg CGPA      { FIXED [Branch], [Batch] : AVG([Cgpa]) }
Branch Rank          RANK_UNIQUE(SUM([Cgpa]), 'desc')      // compute using Enrollment No, restart every Branch and Batch
Top %                CEILING([Branch Rank] / [Cohort Size] * 100)
Percentile           ROUND((1 - ([Branch Rank] - 1) / [Cohort Size]) * 100, 1)
Is Selected          [Enrollment No] = [Selected Student]
Above Threshold      [Cgpa] >= [CGPA Threshold]
CGPA vs Cohort       [Cgpa] - [Cohort Avg CGPA]
CGPA Band            FLOOR([Cgpa] * 2) / 2
Attendance Band      IF [Avg Attendance] < 65 THEN "<65" ELSEIF [Avg Attendance] < 75 THEN "65-75" ELSEIF [Avg Attendance] < 85 THEN "75-85" ELSE "85+" END
Risk Colour          CASE [Risk Band] WHEN "High" THEN "#B5483A" WHEN "Medium" THEN "#F2A900" ELSE "#1F7A8C" END
```
`Branch Rank` and `Top %` are also already precomputed as columns (`Branch Rank`, `Top Percent`) so you can compare your table calculation with them.

## Sheets
1. **Rank ribbon**: histogram of `CGPA Band` (columns = COUNT of students) filtered to the selected student's Branch and Batch; add a reference line at the selected student's CGPA (Analytics > Reference Line, value = `SUM(IF [Is Selected] THEN [Cgpa] END)`).
2. **Branch comparison**: box plot, Cgpa by Branch, detail = Enrollment No, colour = Batch.
3. **SGPA trend**: Semester on columns, AVG(Sgpa) on rows, colour = Branch. Add a second line for the selected student using `Is Selected` as a filter on a duplicate axis.
4. **Difficulty heat map**: course_level, rows = Course Name, columns = Semester, colour = Difficulty Index (diverging palette), sort descending. Add a scatter of Avg Gp vs Fail Rate, size = N Students.
5. **Attendance vs CGPA**: scatter with linear trend line, colour = Risk Band.
6. **Student archetypes**: Cluster on colour, bar of student count and AVG(Cgpa).

## Dashboard
Layout 1200 x 800. Top: title + Selected Student parameter + KPI tiles. Middle: Rank ribbon, SGPA trend. Bottom: Branch comparison, Difficulty heat map. Add:
- a **Filter action** (hover) from Branch comparison to the other sheets,
- a **Highlight action** from the difficulty heat map to the scatter,
- a **Set action** for "At-risk students" (Risk Band = High).

Publish to Tableau Public and paste the link into your resume and README.
