"""Run the whole pipeline end to end:  python run_all.py
Excel note: openpyxl writes formulas without cached values; Excel/LibreOffice calculates them when you open the file."""
import subprocess, sys
from pathlib import Path

SRC = Path(__file__).parent / "src"
STEPS = ["01_generate_data.py", "02_clean_data.py", "03_eda.py", "04_ml_models.py", "05_build_sqlite.py",
         "06_build_excel.py", "07_export_bi_assets.py", "08_make_report.py", "09_build_notebook.py"]
for s in STEPS:
    print(f"\n=== {s} ===", flush=True)
    r = subprocess.run([sys.executable, s], cwd=SRC)
    if r.returncode:
        sys.exit(f"{s} failed")
print("\nDone. Open reports/insights.md, excel/Student_Performance_Analytics.xlsx and notebooks/analysis.ipynb")
