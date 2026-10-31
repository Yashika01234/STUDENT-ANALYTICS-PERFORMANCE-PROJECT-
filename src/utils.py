"""Shared paths and helpers for the Student Performance Analytics project."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
FIG = ROOT / "reports" / "figures"
OUT = ROOT / "outputs"
MODELS = ROOT / "models"
for _p in (RAW, PROC, FIG, OUT, MODELS):
    _p.mkdir(parents=True, exist_ok=True)

# Marks (out of 100) -> letter grade -> grade point (10-point scale)
GRADE_TABLE = [(90, "O", 10), (80, "A+", 9), (70, "A", 8), (60, "B+", 7),
               (50, "B", 6), (45, "C", 5), (40, "P", 4), (0, "F", 0)]


def grade_letter(total):
    t = np.asarray(total, dtype=float)
    return np.select([t >= m for m, _, _ in GRADE_TABLE], [g for _, g, _ in GRADE_TABLE], default="F")


def grade_point(total):
    t = np.asarray(total, dtype=float)
    return np.select([t >= m for m, _, _ in GRADE_TABLE], [p for _, _, p in GRADE_TABLE], default=0)


def minmax(s):
    s = pd.Series(s, dtype=float)
    rng = s.max() - s.min()
    return (s - s.min()) / rng if rng else s * 0


def difficulty_index(results: pd.DataFrame) -> pd.DataFrame:
    """Course difficulty on a 0-100 scale: 45% low average grade point,
    35% fail rate, 20% spread of marks. Each part is min-max scaled across courses."""
    g = results.groupby("course_id").agg(
        avg_gp=("grade_point", "mean"),
        fail_rate=("grade_point", lambda x: (x == 0).mean()),
        std_marks=("total_marks", "std"),
        avg_marks=("total_marks", "mean"),
        avg_attendance=("attendance_pct", "mean"),
        n_students=("enrollment_no", "nunique"),
    )
    g["difficulty_index"] = 100 * (0.45 * minmax(10 - g["avg_gp"]) + 0.35 * minmax(g["fail_rate"])
                                   + 0.20 * minmax(g["std_marks"]))
    return g.reset_index()
