"""Step 6 - Build the Excel workbook: live formulas, a Result-Hub style lookup, and charts.
Pivot tables cannot be authored by openpyxl, so the summary sheets use AVERAGEIFS/COUNTIFS formulas instead
(they recalculate when the data sheets change). A short pivot recipe is on the README sheet."""
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.formatting.rule import ColorScaleRule, DataBarRule, CellIsRule
from openpyxl.utils import get_column_letter as L
from utils import PROC, ROOT

S = pd.read_csv(PROC / "student_summary.csv").merge(pd.read_csv(PROC / "student_ml_insights.csv"), on="enrollment_no")
SEM = pd.read_csv(PROC / "student_semester.csv").merge(S[["enrollment_no", "branch", "batch"]], on="enrollment_no")
R = pd.read_csv(PROC / "results_clean.csv")
D = pd.read_csv(PROC / "course_difficulty.csv")
D["xl_score"] = (10 - D.avg_gp) * 10 + D.fail_rate * 100
D = D.sort_values("xl_score", ascending=False)

F = "Arial"
NAVY, GOLD, GREY = "14213D", "F2A900", "EEF1F5"
hfont = Font(name=F, bold=True, color="FFFFFF"); hfill = PatternFill("solid", fgColor=NAVY)
base = Font(name=F, size=10); bold = Font(name=F, size=10, bold=True)
inp_font = Font(name=F, size=11, bold=True, color="0000FF"); inp_fill = PatternFill("solid", fgColor="FFFF00")
thin = Side(style="thin", color="D5DBE5"); box = Border(top=thin, bottom=thin, left=thin, right=thin)

wb = Workbook()
rd = wb.active; rd.title = "README"
db = wb.create_sheet("Dashboard"); bs = wb.create_sheet("Branch_Summary"); st = wb.create_sheet("Sem_Trend"); cd = wb.create_sheet("Course_Difficulty")
ds = wb.create_sheet("Data_Summary"); dsem = wb.create_sheet("Data_StudentSem"); dr = wb.create_sheet("Data_Results")

def write_df(ws, df):
    ws.append(list(df.columns))
    for row in df.itertuples(index=False):
        ws.append(list(row))
    for c in ws[1]:
        c.font = hfont; c.fill = hfill; c.alignment = Alignment(horizontal="center", wrap_text=True)
    ws.freeze_panes = "B2"; ws.auto_filter.ref = ws.dimensions
    for i, col in enumerate(df.columns, 1):
        ws.column_dimensions[L(i)].width = max(12, min(26, len(str(col)) + 3))

sum_cols = ["enrollment_no", "branch", "batch", "gender", "residence", "board_pct", "entrance_percentile", "weekly_study_hrs", "extracurricular",
            "cgpa", "avg_attendance", "total_backlogs"] + [f"sgpa_s{i}" for i in range(1, 7)] + ["predicted_cgpa_s3_6", "risk_probability", "risk_band", "cluster"]
write_df(ds, S[sum_cols])
write_df(dsem, SEM[["enrollment_no", "branch", "batch", "semester", "sgpa", "credits_attempted", "credits_earned", "backlogs", "avg_attendance"]])
write_df(dr, R[["enrollment_no", "course_id", "semester", "internal_marks", "external_marks", "total_marks", "grade", "grade_point", "attendance_pct", "credits"]])
NS, NSEM, NR = len(S) + 1, len(SEM) + 1, len(R) + 1
for ws in (ds, dsem, dr):
    for row in ws.iter_rows(min_row=2):
        for c in row: c.font = base
# Data_Summary column letters
col = {n: L(i + 1) for i, n in enumerate(sum_cols)}
rng = lambda n: f"Data_Summary!${col[n]}$2:${col[n]}${NS}"

# ---------------- Branch_Summary ----------------
branches = ["CSE", "IT", "ECE", "EE", "ME"]
heads = ["Branch", "Students", "Avg CGPA", "Max CGPA", "Min CGPA", "% CGPA >= 8", "Avg attendance %", "High-risk students", "Avg backlogs"]
bs.append(heads)
for i, b in enumerate(branches, 2):
    bs.append([b,
        f'=COUNTIFS({rng("branch")},$A{i})',
        f'=AVERAGEIFS({rng("cgpa")},{rng("branch")},$A{i})',
        f'=_xlfn.MAXIFS({rng("cgpa")},{rng("branch")},$A{i})',
        f'=_xlfn.MINIFS({rng("cgpa")},{rng("branch")},$A{i})',
        f'=COUNTIFS({rng("branch")},$A{i},{rng("cgpa")},">=8")/B{i}',
        f'=AVERAGEIFS({rng("avg_attendance")},{rng("branch")},$A{i})',
        f'=COUNTIFS({rng("branch")},$A{i},{rng("risk_band")},"High")',
        f'=AVERAGEIFS({rng("total_backlogs")},{rng("branch")},$A{i})'])
bs.append(["All", f"=SUM(B2:B6)", f'=AVERAGE({rng("cgpa")})', f"=MAX(D2:D6)", f"=MIN(E2:E6)", f'=COUNTIFS({rng("cgpa")},">=8")/B7',
           f'=AVERAGE({rng("avg_attendance")})', "=SUM(H2:H6)", f'=AVERAGE({rng("total_backlogs")})'])
for c in bs[1]: c.font = hfont; c.fill = hfill; c.alignment = Alignment(horizontal="center", wrap_text=True)
for r in bs.iter_rows(min_row=2):
    for c in r: c.font = bold if r[0].row == 7 else base; c.border = box
for r in range(2, 8):
    for cc in "CDE": bs[f"{cc}{r}"].number_format = "0.00"
    bs[f"F{r}"].number_format = "0.0%"; bs[f"G{r}"].number_format = "0.0"; bs[f"I{r}"].number_format = "0.00"
for i in range(1, 10): bs.column_dimensions[L(i)].width = 16
bs["A9"] = "Note: all figures are live formulas over Data_Summary (synthetic data)."
bs["A9"].font = Font(name=F, size=9, italic=True)

# ---------------- Sem_Trend ----------------
st.append(["Branch"] + list(range(1, 7)))
for i, b in enumerate(branches, 2):
    st.append([b] + [f'=AVERAGEIFS(Data_StudentSem!$E$2:$E${NSEM},Data_StudentSem!$B$2:$B${NSEM},$A{i},Data_StudentSem!$D$2:$D${NSEM},{L(j)}$1)' for j in range(2, 8)])
for c in st[1]: c.font = hfont; c.fill = hfill; c.alignment = Alignment(horizontal="center")
for j in range(2, 8): st.cell(1, j).number_format = '"Sem "0'
for r in st.iter_rows(min_row=2):
    for c in r: c.font = base; c.border = box; c.number_format = "0.00" if c.column > 1 else "General"
st.conditional_formatting.add("B2:G6", ColorScaleRule(start_type="min", start_color="F8CBAD", mid_type="percentile", mid_value=50, mid_color="FFFFFF", end_type="max", end_color="A9D18E"))
st.column_dimensions["A"].width = 12
st["A8"] = "Mean SGPA per branch and semester (AVERAGEIFS over Data_StudentSem). Colour scale: red = lower, green = higher."; st["A8"].font = Font(name=F, size=9, italic=True)

# ---------------- Course_Difficulty ----------------
cd.append(["Course ID", "Course", "Branch", "Semester", "Type", "Students", "Avg grade point", "Fail rate", "Avg marks", "Difficulty score"])
for i, r in enumerate(D.itertuples(), 2):
    rr = f"Data_Results!$B$2:$B${NR}"
    cd.append([r.course_id, r.course_name, r.branch_scope, r.semester, r.course_type,
               f"=COUNTIFS({rr},$A{i})", f"=AVERAGEIFS(Data_Results!$H$2:$H${NR},{rr},$A{i})",
               f"=COUNTIFS({rr},$A{i},Data_Results!$H$2:$H${NR},0)/F{i}", f"=AVERAGEIFS(Data_Results!$F$2:$F${NR},{rr},$A{i})",
               f"=ROUND((10-G{i})*10+H{i}*100,1)"])
for c in cd[1]: c.font = hfont; c.fill = hfill; c.alignment = Alignment(horizontal="center", wrap_text=True)
for r in cd.iter_rows(min_row=2):
    for c in r: c.font = base
    r[6].number_format = "0.00"; r[7].number_format = "0.0%"; r[8].number_format = "0.0"
for i, w in enumerate([12, 34, 9, 9, 8, 10, 14, 10, 11, 14], 1): cd.column_dimensions[L(i)].width = w
cd.freeze_panes = "C2"; cd.auto_filter.ref = f"A1:J{len(D)+1}"
cd.conditional_formatting.add(f"J2:J{len(D)+1}", DataBarRule(start_type="min", end_type="max", color="C0392B"))
cd[f"L1"] = "Difficulty score = (10 - average grade point) x 10 + fail rate in percentage points. Higher = harder. Rows are pre-sorted hardest first; re-sort with the filter after changing data."
cd["L1"].font = Font(name=F, size=9, italic=True)

# ---------------- Dashboard ----------------
db.sheet_view.showGridLines = False
for c, w in zip("ABCDEFGHIJKL", [24, 16, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14]): db.column_dimensions[c].width = w
db["A1"] = "Student Performance Analytics - Result Hub"; db["A1"].font = Font(name=F, size=18, bold=True, color=NAVY)
db["A2"] = "Synthetic data. Type any enrollment number from Data_Summary into the yellow cell."; db["A2"].font = Font(name=F, size=9, italic=True)
db["A4"] = "Enrollment number"; db["A4"].font = bold
db["B4"] = "2022UEC0094"; db["B4"].font = inp_font; db["B4"].fill = inp_fill; db["B4"].border = box
m = lambda n: f'MATCH($B$4,{rng("enrollment_no")},0)'
look = lambda n: f'=IFERROR(INDEX({rng(n)},{m(n)}),"Not found")'
items = [("Branch", look("branch"), None), ("Batch", look("batch"), None), ("CGPA", look("cgpa"), "0.00"),
         ("Branch rank", f'=IFERROR(COUNTIFS({rng("branch")},B5,{rng("batch")},B6,{rng("cgpa")},">"&B7)+1,"-")', "0"),
         ("Cohort size", f'=IFERROR(COUNTIFS({rng("branch")},B5,{rng("batch")},B6),"-")', "0"),
         ("Top % of cohort", '=IFERROR(ROUNDUP(B8/B9*100,0),"-")', '"Top "0"%"'),
         ("Percentile", '=IFERROR(ROUND((1-(B8-1)/B9)*100,1),"-")', "0.0"),
         ("Avg attendance %", look("avg_attendance"), "0.0"), ("Backlogs", look("total_backlogs"), "0"),
         ("Predicted CGPA (sem 3-6, model)", look("predicted_cgpa_s3_6"), "0.00"), ("Risk band (model)", look("risk_band"), None),
         ("Student archetype", look("cluster"), None)]
for k, (lab, f, nf) in enumerate(items, 5):
    db[f"A{k}"] = lab; db[f"A{k}"].font = base; db[f"B{k}"] = f; db[f"B{k}"].font = bold; db[f"B{k}"].border = box
    db[f"B{k}"].alignment = Alignment(horizontal="right")
    if nf: db[f"B{k}"].number_format = nf
# trend table for chart
db["D4"] = "Semester"; db["E4"] = "You"; db["F4"] = "Branch average"
for c in ("D4", "E4", "F4"): db[c].font = hfont; db[c].fill = hfill; db[c].alignment = Alignment(horizontal="center")
for s in range(1, 7):
    r = 4 + s
    db[f"D{r}"] = f"Sem {s}"
    db[f"E{r}"] = f'=IFERROR(INDEX({rng("sgpa_s%d" % s)},{m("x")}),NA())'
    db[f"F{r}"] = f'=IFERROR(INDEX(Sem_Trend!$B$2:$G$6,MATCH($B$5,Sem_Trend!$A$2:$A$6,0),{s}),NA())'
    for c in (f"D{r}", f"E{r}", f"F{r}"): db[c].font = base; db[c].border = box
    db[f"E{r}"].number_format = "0.00"; db[f"F{r}"].number_format = "0.00"
# KPI strip
kp = [("Students", f'=COUNTA({rng("enrollment_no")})', "#,##0"), ("Average CGPA", f'=AVERAGE({rng("cgpa")})', "0.00"),
      ("% with CGPA >= 8", f'=COUNTIFS({rng("cgpa")},">=8")/COUNTA({rng("enrollment_no")})', "0.0%"),
      ("Avg attendance %", f'=AVERAGE({rng("avg_attendance")})', "0.0"), ("High-risk students", f'=COUNTIFS({rng("risk_band")},"High")', "#,##0")]
for i, (lab, f, nf) in enumerate(kp):
    c = 8 + i  # H..L
    db.cell(4, c, lab).font = Font(name=F, size=9, color="5B667A"); db.cell(4, c).alignment = Alignment(wrap_text=True, horizontal="center")
    cell = db.cell(5, c, f); cell.font = Font(name=F, size=16, bold=True, color=NAVY); cell.number_format = nf; cell.alignment = Alignment(horizontal="center")
    cell.fill = PatternFill("solid", fgColor=GREY)
db.row_dimensions[4].height = 28; db.row_dimensions[5].height = 30

lc = LineChart(); lc.title = "SGPA: you vs branch average"; lc.height = 7.5; lc.width = 15
lc.add_data(Reference(db, min_col=5, max_col=6, min_row=4, max_row=10), titles_from_data=True); lc.set_categories(Reference(db, min_col=4, min_row=5, max_row=10))
lc.y_axis.scaling.min = 4; lc.y_axis.scaling.max = 10; lc.y_axis.title = "SGPA"
lc.series[0].graphicalProperties.line.solidFill = GOLD; lc.series[0].graphicalProperties.line.width = 38000
lc.series[1].graphicalProperties.line.solidFill = "1F7A8C"; lc.series[1].graphicalProperties.line.dashStyle = "dash"
db.add_chart(lc, "D12")
bc = BarChart(); bc.type = "col"; bc.title = "Average CGPA by branch"; bc.height = 7.5; bc.width = 12
bc.add_data(Reference(bs, min_col=3, min_row=1, max_row=6), titles_from_data=True); bc.set_categories(Reference(bs, min_col=1, min_row=2, max_row=6))
bc.y_axis.scaling.min = 6; bc.y_axis.scaling.max = 9; bc.legend = None; bc.series[0].graphicalProperties.solidFill = NAVY
db.add_chart(bc, "J12")
hc = BarChart(); hc.type = "bar"; hc.title = "10 hardest courses (difficulty score)"; hc.height = 8.5; hc.width = 27
hc.add_data(Reference(cd, min_col=10, min_row=1, max_row=11), titles_from_data=True); hc.set_categories(Reference(cd, min_col=2, min_row=2, max_row=11))
hc.legend = None; hc.series[0].graphicalProperties.solidFill = "C0392B"; hc.x_axis.scaling.orientation = "maxMin"
db.add_chart(hc, "D28")

# ---------------- README ----------------
lines = ["Student Performance Analytics - Excel workbook", "",
 "All data is SYNTHETIC (generated by src/01_generate_data.py). No real student records are used.", "",
 "Sheets",
 "  Dashboard         Result-Hub style lookup (yellow cell B4), KPIs and charts. Everything is a formula.",
 "  Branch_Summary    COUNTIFS / AVERAGEIFS / MAXIFS / MINIFS by branch.",
 "  Sem_Trend         Mean SGPA by branch and semester with a colour scale.",
 "  Course_Difficulty Per-course grade point, fail rate and difficulty score from Data_Results.",
 "  Data_*            Cleaned data produced by the Python pipeline (1,000 students, 6,000 semester rows, 24,000 results).", "",
 "Edit only the yellow cell (Dashboard!B4). Blue bold text marks inputs. Other cells are formulas.",
 "Rank = COUNTIFS(branch, batch, CGPA greater than yours) + 1. Top % = ROUNDUP(rank / cohort size x 100).", "",
 "Quick pivot recipe (Excel desktop): select Data_Summary > Insert > PivotTable > rows: branch, columns: batch, values: average of cgpa.",
 "Then Insert > PivotChart and add a slicer on risk_band."]
for i, t in enumerate(lines, 1):
    rd[f"A{i}"] = t; rd[f"A{i}"].font = Font(name=F, size=14 if i == 1 else 10, bold=(i == 1 or t == "Sheets"))
rd.column_dimensions["A"].width = 120

out = ROOT / "excel" / "Student_Performance_Analytics.xlsx"
wb.save(out); print("saved", out)
