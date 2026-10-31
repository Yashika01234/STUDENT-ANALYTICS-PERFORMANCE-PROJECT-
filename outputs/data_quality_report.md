# Data quality report

- Loaded raw: students=1010, results=24040, courses=88
- Standardised 101 non-canonical branch labels (case, spaces, long names)
- Standardised 100 gender labels
- Removed 10 exact duplicate student rows
- Imputed 30 missing board_pct with the branch median (flagged in board_pct_imputed)
- Removed 40 duplicate (student, course) result rows
- Recomputed 240 missing total_marks as internal + external
- Imputed 600 missing attendance values with the student's semester mean (flagged)
- Grade validation: 0 rows where stored grade != grade derived from marks
- Integrity checks passed: marks/attendance within range, no orphan keys
- Built tables: students=1000, results=24000, student_semester=6000, student_summary=1000, courses=88
