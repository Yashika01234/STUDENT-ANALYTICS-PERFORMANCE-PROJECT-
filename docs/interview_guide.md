# Interview guide

## 60-second pitch
"I built an end-to-end analytics project on university results, modelled on result portals like NSUT's Result Hub. I generated a realistic messy dataset, cleaned and validated it in pandas, ran statistical tests, built regression, classification and clustering models in scikit-learn, queried it with SQL window functions, and delivered it as an Excel workbook, a Power BI model with DAX and row-level security, and a Tableau dashboard. The core question was: after two semesters, can we predict who will struggle? A simple Ridge model predicts later CGPA with R2 about 0.86, and the risk classifier gets AUC about 0.97."

## Be ready to explain
- **Why synthetic data?** Real student results are personal data; scraping a result portal is not appropriate. A seeded generator also lets me plant known relationships and check the pipeline recovers them.
- **Leakage:** features use only semesters 1-2 and admission data; the target is the CGPA of semesters 3-6. Dashboard predictions are out-of-fold.
- **Why Ridge won:** the signal is mostly additive; boosted trees add variance without benefit. Simpler, explainable model chosen on holdout RMSE.
- **Why recall for the classifier:** a missed struggling student costs more than a false alarm.
- **Difficulty index:** 45% low average grade point, 35% fail rate, 20% mark spread, min-max scaled. Weights are a judgement call; show a sensitivity check if asked.
- **Rank rule:** within branch and batch, ties share the lower rank, Top % = ceil(rank / cohort size x 100).
- **K-Means k:** silhouette favours k = 2; I chose k = 4 for actionable archetypes and said so.
- **Correlation vs causation:** attendance and CGPA both reflect study habits.

## Likely questions
1. How did you handle missing values? (flagged and imputed: branch median / student-semester mean; recomputed totals from components)
2. How would this change with real data? (consent and anonymisation, time-based splits, fairness checks across gender/branch, calibration)
3. How do you compute percentile in SQL / DAX / Excel? (`PERCENT_RANK`, `Cohort Rank` measure, COUNTIFS + 1)
4. What would you do next? (survival analysis for backlogs, SHAP explanations, scheduled refresh, A/B test of an intervention)

## Where each skill lives
pandas `src/02` | statistics `src/03` | scikit-learn `src/04` | SQL `sql/queries.sql` | Excel `src/06` | DAX `powerbi/measures.dax` | Tableau `tableau/README.md`
