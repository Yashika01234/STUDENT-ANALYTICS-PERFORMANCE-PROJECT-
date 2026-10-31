-- Analytical SQL (SQLite dialect; window functions need SQLite >= 3.25, also works in PostgreSQL with minor tweaks)
-- Each block starts with "-- name:" so src/05_build_sqlite.py can run and export them individually.

-- name: q1_branch_summary
SELECT branch, batch,
       COUNT(*)                               AS students,
       ROUND(AVG(cgpa), 2)                    AS avg_cgpa,
       ROUND(MIN(cgpa), 2)                    AS min_cgpa,
       ROUND(MAX(cgpa), 2)                    AS max_cgpa,
       ROUND(100.0 * SUM(cgpa >= 8) / COUNT(*), 1) AS pct_above_8,
       ROUND(AVG(avg_attendance), 1)          AS avg_attendance
FROM student_summary
GROUP BY branch, batch
ORDER BY avg_cgpa DESC;

-- name: q2_rank_and_percentile_window
-- Result-Hub style: rank, percentile and "top %" inside branch + batch, computed with window functions.
SELECT enrollment_no, branch, batch, cgpa,
       RANK()         OVER w                                   AS branch_rank,
       COUNT(*)       OVER (PARTITION BY branch, batch)        AS cohort_size,
       ROUND(100.0 * RANK() OVER w / COUNT(*) OVER (PARTITION BY branch, batch)) AS top_percent,
       ROUND(100 * PERCENT_RANK() OVER (PARTITION BY branch, batch ORDER BY cgpa), 1) AS percentile
FROM student_summary
WINDOW w AS (PARTITION BY branch, batch ORDER BY cgpa DESC)
ORDER BY branch, batch, branch_rank
LIMIT 25;

-- name: q3_top3_per_branch
WITH ranked AS (
  SELECT enrollment_no, branch, batch, cgpa,
         ROW_NUMBER() OVER (PARTITION BY branch ORDER BY cgpa DESC) AS rn
  FROM student_summary)
SELECT * FROM ranked WHERE rn <= 3 ORDER BY branch, rn;

-- name: q4_hardest_courses
WITH c AS (
  SELECT r.course_id,
         AVG(r.grade_point)                    AS avg_gp,
         AVG(r.total_marks)                    AS avg_marks,
         1.0 * SUM(r.grade_point = 0) / COUNT(*) AS fail_rate,
         COUNT(*)                              AS n
  FROM results_clean r GROUP BY r.course_id)
SELECT k.course_name, k.branch_scope, k.semester, ROUND(c.avg_gp, 2) AS avg_gp,
       ROUND(c.avg_marks, 1) AS avg_marks, ROUND(100 * c.fail_rate, 1) AS fail_pct, c.n
FROM c JOIN courses k USING (course_id)
WHERE k.course_type = 'Theory'
ORDER BY c.avg_gp ASC, fail_pct DESC
LIMIT 10;

-- name: q5_sgpa_change_lag
-- Semester-on-semester movement per student using LAG().
WITH x AS (
  SELECT enrollment_no, semester, sgpa,
         LAG(sgpa) OVER (PARTITION BY enrollment_no ORDER BY semester) AS prev_sgpa
  FROM student_semester)
SELECT semester, ROUND(AVG(sgpa - prev_sgpa), 3) AS avg_change,
       SUM(sgpa - prev_sgpa <= -1.0) AS students_dropping_1pt_or_more
FROM x WHERE prev_sgpa IS NOT NULL GROUP BY semester ORDER BY semester;

-- name: q6_attendance_bands
SELECT CASE WHEN avg_attendance < 65 THEN '1. below 65'
            WHEN avg_attendance < 75 THEN '2. 65-75'
            WHEN avg_attendance < 85 THEN '3. 75-85'
            ELSE '4. 85+' END AS attendance_band,
       COUNT(*) AS students, ROUND(AVG(cgpa), 2) AS avg_cgpa,
       ROUND(AVG(total_backlogs), 2) AS avg_backlogs
FROM student_summary GROUP BY 1 ORDER BY 1;

-- name: q7_early_warning_candidates
-- Students whose SGPA fell in semester 2 AND who are below 75% attendance in semesters 1-2.
SELECT s.enrollment_no, s.branch, s.sgpa_s1, s.sgpa_s2,
       ROUND(s.sgpa_s2 - s.sgpa_s1, 2) AS change, ROUND(e.att, 1) AS att_sem1_2
FROM student_summary s
JOIN (SELECT enrollment_no, AVG(avg_attendance) AS att FROM student_semester WHERE semester <= 2 GROUP BY enrollment_no) e USING (enrollment_no)
WHERE s.sgpa_s2 < s.sgpa_s1 AND e.att < 75
ORDER BY change ASC LIMIT 15;

-- name: q8_cohort_comparison
SELECT branch,
       ROUND(AVG(CASE WHEN batch = 2021 THEN cgpa END), 2) AS cgpa_2021,
       ROUND(AVG(CASE WHEN batch = 2022 THEN cgpa END), 2) AS cgpa_2022,
       ROUND(AVG(CASE WHEN batch = 2022 THEN cgpa END) - AVG(CASE WHEN batch = 2021 THEN cgpa END), 2) AS change
FROM student_summary GROUP BY branch ORDER BY change DESC;

-- name: q9_model_risk_vs_outcome
-- Joins ML output back to the warehouse: how well do risk bands line up with actual outcomes?
SELECT m.risk_band, COUNT(*) AS students, ROUND(AVG(m.target_cgpa_s3_6), 2) AS actual_cgpa_s3_6,
       ROUND(100.0 * AVG(m.at_risk), 1) AS pct_actually_at_risk
FROM student_ml_insights m GROUP BY m.risk_band ORDER BY CASE m.risk_band WHEN 'Low' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END;
