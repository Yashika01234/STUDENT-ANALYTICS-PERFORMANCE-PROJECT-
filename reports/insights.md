# Findings

> Data is **synthetic**: relationships were planted by the generator (ability, attendance, study hours), so the aim is to demonstrate a sound method, not to make claims about any real university.

## 1. Branch and cohort performance
- Mean CGPA ranges from **7.25** (ME) to **7.69** (CSE). A one-way ANOVA finds the branch differences statistically significant (F = 4.28, p = 0.0019), but the gaps are modest next to the spread inside each branch (std about 1.2-1.4).
- Batch 2021 vs 2022: 7.57 vs 7.435, p = 0.12, so no reliable difference between batches.
- Hostel vs day scholar (p = 0.25) and gender (p = 0.47) show **no significant CGPA gap**.

## 2. What goes with CGPA
- Attendance: Pearson r = **0.637**. Students under 75% attendance average CGPA 6.58; students at 85%+ average 8.89. 34% of students are below 75%.
- Board marks: r = **0.775**. Weekly self-study hours: Spearman rho = **0.406**.
- Correlation is not causation: attendance and CGPA both reflect a student's underlying habits.

## 3. Course difficulty
- Hardest course by the difficulty index: **Power Systems-I** (EE, semester 4, index 97/100).
- Easiest theory course: **Computer Networks** (IT, semester 4).
- Index = 45% low average grade point + 35% fail rate + 20% spread of marks (each min-max scaled).

## 4. Machine learning
**Predicting CGPA of semesters 3-6 from semesters 1-2 + admission data** (no leakage). Best model: **Ridge**, holdout RMSE **0.55**, MAE 0.41, R2 **0.86** (baseline R2 about 0). A tuned gradient-boosting model did not beat the simple linear model, which is expected when the signal is mostly additive, and the simpler model is easier to explain.
Top drivers (permutation importance): sgpa_s2 (0.27), sgpa_s1 (0.23), board_pct (0.15), entrance_percentile (0.12), weekly_study_hrs (0.04).

**Early-warning classifier** (final CGPA of semesters 3-6 below 7.0; prevalence 31%): Logistic Regression, test AUC **0.97**, recall 0.90, precision 0.80. Recall was prioritised because missing a struggling student costs more than a false alarm.

**Student archetypes (K-Means, k = 4)**:
| cluster           |   students |   cgpa |   sgpa_trend |   avg_attendance |   at_risk |
|:------------------|-----------:|-------:|-------------:|-----------------:|----------:|
| High achievers    |        415 |   8.54 |        -0.04 |            82.13 |      0.03 |
| Needs support     |         98 |   5.46 |        -0.32 |            71.5  |      0.97 |
| Rising (low base) |         92 |   5.72 |         0.26 |            71.49 |      0.79 |
| Steady middle     |        395 |   7.34 |        -0.05 |            76    |      0.33 |
Silhouette for k = 2..7 is in `outputs/silhouette_by_k.csv` (k = 2 scores highest; k = 4 was chosen because four groups are actionable for advisors).

## 5. Recommendations (what a department could do)
1. Flag students below 75% attendance after semester 2: they are the highest-risk group.
2. Offer bridge sessions for the hardest courses before the semester starts.
3. Use the risk score as a triage list for mentors, not as a label on students.

## 6. Limitations
Synthetic data; one institution-style structure; risk threshold of 7.0 is arbitrary; out-of-fold predictions are used for dashboards so no student is scored by a model that saw them.

---
## Appendix: data quality log
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

