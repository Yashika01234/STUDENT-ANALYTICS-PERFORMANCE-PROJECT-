"""Step 5 - Load clean tables into SQLite and run the analytical SQL in sql/queries.sql."""
import re, sqlite3
import pandas as pd
from utils import PROC, ROOT, OUT

db = ROOT / "data" / "results.db"
if db.exists():
    db.unlink()
con = sqlite3.connect(db)
for t in ["students_clean", "courses", "results_clean", "student_semester", "student_summary", "course_difficulty", "student_ml_insights"]:
    pd.read_csv(PROC / f"{t}.csv").to_sql(t, con, index=False)
con.execute("CREATE INDEX idx_res_student ON results_clean(enrollment_no)")
con.execute("CREATE INDEX idx_res_course ON results_clean(course_id)")
con.execute("CREATE INDEX idx_sum_branch ON student_summary(branch, batch)")

sql = (ROOT / "sql" / "queries.sql").read_text()
blocks = re.split(r"^-- name: ", sql, flags=re.M)[1:]
(OUT / "sql_results").mkdir(exist_ok=True)
for b in blocks:
    name, body = b.split("\n", 1)
    df = pd.read_sql_query(body.strip().rstrip(";"), con)
    df.to_csv(OUT / "sql_results" / f"{name.strip()}.csv", index=False)
    print(f"\n== {name.strip()} ({len(df)} rows)\n{df.head(6).to_string(index=False)}")
con.close()
