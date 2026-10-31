# Student Performance Analytics

An end-to-end analytics project on university results: ingest messy data, clean and validate it, explore and test hypotheses, model it with scikit-learn, query it in SQL, and present it in **Excel, Power BI and Tableau**.

> All data is **synthetic** (generated in `src/01_generate_data.py`, seeded for reproducibility). No real student records are used or scraped.

## What it answers
1. Where does a student stand in their branch? (rank, percentile, "Top x%", like a result portal)
2. Which factors relate to CGPA: attendance, board marks, study hours, branch, hostel, gender?
3. Which courses are hardest, and by what measure?
4. Can we flag students likely to struggle after only two semesters? (regression, classification, clustering)

## Tools used
| Stage | Tool |
|---|---|
| Cleaning, EDA, stats tests | Python: pandas, NumPy, SciPy, seaborn, matplotlib |
| ML | scikit-learn: Ridge, Random Forest, Gradient Boosting, Logistic Regression, K-Means, PCA, GridSearchCV, permutation importance |
| SQL | SQLite with window functions, CTEs, LAG (`sql/queries.sql`) |
| Spreadsheet | Excel workbook with live formulas, a lookup tool and charts |
| BI | Power BI star schema + DAX + RLS guide; Tableau data sources + calculated fields |
| Storytelling | Executed Jupyter notebook + `reports/insights.md` |

## Project layout
```
data/raw/            messy raw CSVs (duplicates, casing, missing values)
data/processed/      clean tables + ML outputs
src/                 numbered scripts 01-09 (run in order, or python run_all.py)
sql/queries.sql      9 analytical queries (results exported to outputs/sql_results/)
excel/               Student_Performance_Analytics.xlsx
powerbi/             star-schema CSVs, measures.dax, theme.json, load_data.m, README.md (build guide)
tableau/             flat CSVs and README.md (calculated fields + dashboard guide)
notebooks/           analysis.ipynb (executed)
models/              saved scikit-learn models (joblib)
reports/             insights.md and figures/
outputs/             metrics, model comparisons, data-quality report
docs/                data dictionary and interview guide
```

## Run it
```bash
pip install -r requirements.txt
python run_all.py
```
Everything is seeded, so results reproduce exactly.

## Headline results
See `reports/insights.md` (generated from the computed outputs). Key ideas: strong link between attendance/board marks and CGPA, no significant hostel or gender gap, a simple linear model matching boosted trees for predicting later CGPA, and a risk score whose "High" band really does contain most struggling students.

## Honest limits
- `.pbix` and `.twbx` files can only be created inside Power BI Desktop / Tableau, so those folders give you the data, measures and a step-by-step build guide.
- Findings reflect relationships planted in the synthetic generator; the value here is the method.
