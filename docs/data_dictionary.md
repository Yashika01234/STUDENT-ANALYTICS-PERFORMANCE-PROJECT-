# Data dictionary (synthetic data)

**students**: enrollment_no (`YYYY` + branch code + roll, e.g. 2022UEC0094), branch, batch, gender, residence, board_pct, entrance_percentile, weekly_study_hrs, extracurricular.
**courses**: course_id, course_name, branch_scope (ALL = common first-year), semester, course_type (Theory/Lab), credits.
**results**: enrollment_no, course_id, semester, internal_marks (/40), external_marks (/60), total_marks, grade, grade_point, passed, attendance_pct, credits.
**student_semester**: sgpa (credit-weighted), credits_attempted, credits_earned, backlogs, avg_attendance.
**student_summary**: cgpa (credit-weighted), total_backlogs, sgpa_s1..s6, sgpa_trend (slope per semester), sgpa_std, branch_rank, cohort_size, top_percent, percentile, overall_rank.
**student_ml_insights**: target_cgpa_s3_6, predicted_cgpa_s3_6 (out-of-fold), at_risk (target < 7.0), risk_probability, risk_band (Low <0.3, Medium 0.3-0.6, High >0.6), cluster.
**course_difficulty**: avg_gp, fail_rate, std_marks, difficulty_index (0-100 = 45% low grade point + 35% fail rate + 20% mark spread, each min-max scaled).

Grading scale: O>=90 (10), A+>=80 (9), A>=70 (8), B+>=60 (7), B>=50 (6), C>=45 (5), P>=40 (4), F<40 (0).
Rank rule: rank within (branch, batch) by CGPA descending, ties share the lower rank number. Top % = ceil(rank / cohort size x 100).
