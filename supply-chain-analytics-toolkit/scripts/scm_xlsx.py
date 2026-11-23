"""
scm_xlsx.py - helpers for building SCM-345-style Excel workbooks with openpyxl.

The course conventions these helpers enforce:
  * four color zones: grey = inputs/parameters, yellow = decisions,
    green = calculations, cream = outputs
  * every block Solver reads (objective, changing cells, both sides of every
    constraint) and every SUMPRODUCT range gets a NAMED RANGE
  * a "Solver Setup" card written out field by field, so the user can copy it
    into Excel's Solver dialog (openpyxl cannot run Solver)
  * plain text never starts with "=" (openpyxl would silently turn it into a
    formula that shows #NAME? in Excel)

Typical use:
    import sys; sys.path.insert(0, "<skill>/scripts")
    from scm_xlsx import *
    wb, ws = new_workbook("Product Mix")
    title(ws, "Woodshop product mix", "Maximize profit from lumber and labor")
    write_block(ws, "B5", [["", "Bookcase", "Desk", "Table"], ...], zone="input")
    name_range(wb, ws, "Profit_Per_Unit", "C6:E6")
    ...
    solver_card(wb, objective="Total_Profit", sense="Max",
                changing="Build", constraints=["Used <= Available", "Build >= 0"],
                engine="Simplex LP")
    save(wb, "/mnt/user-data/outputs/Woodshop.xlsx")
"""
import re
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import range_boundaries, get_column_letter
from openpyxl.workbook.defined_name import DefinedName

# ---------------------------------------------------------------- styling
ZONES = {
    "input":    {"fill": "D9D9D9", "label": "GREY = inputs / parameters (given numbers)"},
    "decision": {"fill": "FFF2CC", "label": "YELLOW = decisions (Solver changes these)"},
    "calc":     {"fill": "E2EFDA", "label": "GREEN = calculations (formulas you build)"},
    "output":   {"fill": "F6F1E8", "label": "CREAM = outputs / results to report"},
}
HEADER_FILL = "653819"   # Lehigh brown
TITLE_COLOR = "3A2214"   # espresso
THIN = Side(style="thin", color="A6A6A6")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

_CELL_LIKE = re.compile(r"^[A-Za-z]{1,3}[0-9]+$")
_R1C1_LIKE = re.compile(r"^[RrCc][0-9]*$|^[Rr][0-9]*[Cc][0-9]*$")


def safe_text(s):
    """Return text that Excel will show as text, never parse as a formula."""
    if isinstance(s, str) and s[:1] in ("=", "+", "-", "@") and not _looks_like_number(s):
        return " " + s
    return s


def _looks_like_number(s):
    try:
        float(s.replace(",", ""))
        return True
    except ValueError:
        return False


def new_workbook(first_sheet="Model"):
    wb = Workbook()
    ws = wb.active
    ws.title = first_sheet
    ws.sheet_view.showGridLines = True
    ws.column_dimensions["A"].width = 3
    return wb, ws


def title(ws, text, subtitle=None, cell="B2"):
    ws[cell] = safe_text(text)
    ws[cell].font = Font(name="Calibri", size=16, bold=True, color=TITLE_COLOR)
    if subtitle:
        col, row = re.match(r"([A-Z]+)(\d+)", cell).groups()
        c = ws[f"{col}{int(row) + 1}"]
        c.value = safe_text(subtitle)
        c.font = Font(name="Calibri", size=11, italic=True, color="595959")


def section(ws, cell, text, width_cols=4):
    """A brown band with white text marking a block (INPUTS, DECISIONS, ...)."""
    c = ws[cell]
    c.value = safe_text(text)
    c.font = Font(bold=True, color="FFFFFF")
    min_col, row, _, _ = range_boundaries(cell + ":" + cell)
    for k in range(width_cols):
        ws.cell(row=row, column=min_col + k).fill = PatternFill("solid", fgColor=HEADER_FILL)


def style_zone(ws, cell_range, zone, number_format=None, bold=False):
    """Color a block by its role: 'input', 'decision', 'calc' or 'output'."""
    fill = PatternFill("solid", fgColor=ZONES[zone]["fill"])
    for row in ws[cell_range] if ":" in cell_range else [[ws[cell_range]]]:
        for c in row:
            c.fill = fill
            c.border = BOX
            if number_format:
                c.number_format = number_format
            if bold:
                c.font = Font(bold=True)


def write_block(ws, top_left, rows, zone=None, number_format=None, header_row=False):
    """Write a 2-D list starting at top_left. Strings starting with '=' are
    treated as FORMULAS (that is what openpyxl does); wrap literal text in
    safe_text() if it must start with '='. Returns the A1 range written."""
    min_col, min_row, _, _ = range_boundaries(top_left + ":" + top_left)
    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            c = ws.cell(row=min_row + i, column=min_col + j, value=v)
            if header_row and i == 0:
                c.font = Font(bold=True)
    max_row = min_row + len(rows) - 1
    max_col = min_col + max(len(r) for r in rows) - 1
    rng = f"{get_column_letter(min_col)}{min_row}:{get_column_letter(max_col)}{max_row}"
    if zone:
        first = 1 if header_row else 0
        body = f"{get_column_letter(min_col)}{min_row + first}:{get_column_letter(max_col)}{max_row}"
        style_zone(ws, body, zone, number_format)
    return rng


def _check_name(name):
    if " " in name:
        raise ValueError(f"Named range '{name}' has a space; use an underscore.")
    if _CELL_LIKE.match(name) or _R1C1_LIKE.match(name):
        raise ValueError(f"Named range '{name}' looks like a cell address; Excel rejects it.")
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_.]*$", name):
        raise ValueError(f"Named range '{name}' must start with a letter/underscore, no symbols.")


def name_range(wb, ws, name, cell_range):
    """Create a workbook-level named range pointing at ws!cell_range (absolute)."""
    _check_name(name)
    if ":" in cell_range:
        a, b = cell_range.split(":")
        ref = f"{_abs(a)}:{_abs(b)}"
    else:
        ref = _abs(cell_range)
    sheet = ws.title
    quoted = f"'{sheet}'" if re.search(r"[^A-Za-z0-9_]", sheet) else sheet
    dn = DefinedName(name, attr_text=f"{quoted}!{ref}")
    wb.defined_names[name] = dn
    return name


def _abs(cell):
    col, row = re.match(r"\$?([A-Z]+)\$?(\d+)", cell).groups()
    return f"${col}${row}"


def color_legend(ws, cell="H2"):
    """Write the four-zone color code as a small legend."""
    min_col, row, _, _ = range_boundaries(cell + ":" + cell)
    ws.cell(row=row, column=min_col, value="COLOR CODE").font = Font(bold=True)
    for k, z in enumerate(["input", "decision", "calc", "output"], start=1):
        c = ws.cell(row=row + k, column=min_col, value=ZONES[z]["label"])
        c.fill = PatternFill("solid", fgColor=ZONES[z]["fill"])
        c.border = BOX


def notes(ws, cell, lines, bold_first=False, width=None):
    """Write a list of instruction lines going down from `cell`."""
    min_col, row, _, _ = range_boundaries(cell + ":" + cell)
    for k, line in enumerate(lines):
        c = ws.cell(row=row + k, column=min_col, value=safe_text(line))
        c.alignment = Alignment(wrap_text=False, vertical="top")
        if bold_first and k == 0:
            c.font = Font(bold=True)
    if width:
        ws.column_dimensions[get_column_letter(min_col)].width = width


def solver_card(wb, objective, sense, changing, constraints, engine,
                options=None, sheet_name="Solver Setup", extra_notes=None):
    """Add a sheet that spells out every Solver field, using NAMED RANGES.

    sense: 'Max', 'Min' or 'Value Of: <number>'
    changing: named range(s), e.g. "Build" or "Weights, Trend, Season_Index"
    constraints: list of strings like "Used <= Available", "Assign = binary"
    engine: 'Simplex LP', 'GRG Nonlinear' or 'Evolutionary'
    options: list of strings (e.g. "Make Unconstrained Variables Non-Negative: TICKED")
    """
    ws = wb.create_sheet(sheet_name)
    ws.column_dimensions["A"].width = 3
    ws.column_dimensions["B"].width = 38
    ws.column_dimensions["C"].width = 60
    title(ws, "Solver setup", "Data > Solver. Type the NAMES below, not cell addresses.")
    rows = [["Solver field", "What to enter"],
            ["Set Objective", objective],
            ["To", sense],
            ["By Changing Variable Cells", changing]]
    for k, con in enumerate(constraints, 1):
        rows.append([f"Subject to the Constraints ({k})", con])
    for opt in (options or []):
        rows.append(["Option", opt])
    rows.append(["Select a Solving Method", engine])
    write_block(ws, "B5", [[safe_text(a), safe_text(b)] for a, b in rows], header_row=True)
    for c in ws["B5:C5"][0]:
        c.fill = PatternFill("solid", fgColor=HEADER_FILL)
        c.font = Font(bold=True, color="FFFFFF")
    last = 5 + len(rows) - 1
    style_zone(ws, f"B6:C{last}", "output")
    # highlight the solving-method row: the most consequential field
    for c in ws[f"B{last}:C{last}"][0]:
        c.fill = PatternFill("solid", fgColor="FED141")
        c.font = Font(bold=True)
    tail = ["",
            "Before you click Solve: Reset All if this workbook has been solved before",
            "(leftover constraints from an earlier run ride along silently).",
            "After Solve: choose Keep Solver Solution. For a linear model, tick the",
            "Answer and Sensitivity reports BEFORE clicking OK."]
    notes(ws, f"B{last + 2}", tail + (extra_notes or []))
    return ws


def freeze_values(ws, top_left, matrix, number_format="0"):
    """Write a frozen block of plain numbers (e.g. 1,000 simulated sample paths)."""
    min_col, min_row, _, _ = range_boundaries(top_left + ":" + top_left)
    for i, r in enumerate(matrix):
        for j, v in enumerate(r if hasattr(r, "__len__") else [r]):
            c = ws.cell(row=min_row + i, column=min_col + j, value=float(v))
            c.number_format = number_format
    n_rows = len(matrix)
    n_cols = len(matrix[0]) if hasattr(matrix[0], "__len__") else 1
    return (f"{get_column_letter(min_col)}{min_row}:"
            f"{get_column_letter(min_col + n_cols - 1)}{min_row + n_rows - 1}")


def fill_down(ws, first_row_formulas, top_left, n_rows):
    """Copy a row of formulas written for the FIRST row down n_rows rows,
    shifting relative row numbers (not $-anchored ones, not names).
    first_row_formulas: list of formula strings for the first row."""
    min_col, min_row, _, _ = range_boundaries(top_left + ":" + top_left)
    # a cell reference not glued to a longer name (so W1_S1 or LOG10( stay put)
    pat = re.compile(r"(?<![A-Za-z_\d.])(\$?)([A-Z]{1,3})(\$?)(\d+)(?![\w(])")
    for i in range(n_rows):
        for j, f in enumerate(first_row_formulas):
            if isinstance(f, str) and f.startswith("="):
                def shift(m):
                    if m.group(3) == "$":
                        return m.group(0)
                    return f"{m.group(1)}{m.group(2)}{m.group(3)}{int(m.group(4)) + i}"
                g = _shift_outside_quotes(f, pat, shift)
            else:
                g = f
            ws.cell(row=min_row + i, column=min_col + j, value=g)


def _shift_outside_quotes(formula, pat, repl):
    parts = formula.split('"')
    for k in range(0, len(parts), 2):          # only outside string literals
        parts[k] = pat.sub(repl, parts[k])
    return '"'.join(parts)


def autosize(ws, min_width=8, max_width=48):
    widths = {}
    for row in ws.iter_rows():
        for c in row:
            if c.value is None:
                continue
            L = len(str(c.value)) if not str(c.value).startswith("=") else 10
            widths[c.column_letter] = max(widths.get(c.column_letter, 0), L)
    for col, w in widths.items():
        if col == "A":
            continue
        ws.column_dimensions[col].width = max(min_width, min(max_width, w + 2))


# Functions added in Excel 2010+ must be stored with an "_xlfn." prefix in the
# file, or Excel shows #NAME?. openpyxl does not add it, so save() does.
NEW_FUNCTIONS = [
    "NORM.INV", "NORM.DIST", "NORM.S.INV", "NORM.S.DIST", "LOGNORM.INV", "LOGNORM.DIST",
    "BINOM.INV", "BINOM.DIST", "POISSON.DIST", "EXPON.DIST", "GAMMA.INV", "GAMMA.DIST",
    "T.INV", "T.INV.2T", "T.DIST", "T.DIST.2T", "T.DIST.RT", "CHISQ.INV", "CHISQ.DIST",
    "F.INV", "F.DIST", "CONFIDENCE.NORM", "CONFIDENCE.T",
    "STDEV.S", "STDEV.P", "VAR.S", "VAR.P", "MODE.SNGL", "MODE.MULT",
    "PERCENTILE.INC", "PERCENTILE.EXC", "QUARTILE.INC", "QUARTILE.EXC",
    "RANK.EQ", "RANK.AVG", "COVARIANCE.S", "COVARIANCE.P", "SKEW.P",
    "XLOOKUP", "XMATCH", "IFS", "SWITCH", "MAXIFS", "MINIFS", "CONCAT", "TEXTJOIN",
    "FORMULATEXT", "IFNA", "FILTER", "SORT", "SORTBY", "UNIQUE", "SEQUENCE", "RANDARRAY", "LET",
]
_NEW_FN = re.compile(r"(?<![\w.])(" + "|".join(re.escape(f) for f in
                     sorted(NEW_FUNCTIONS, key=len, reverse=True)) + r")\(", re.IGNORECASE)


def xlfn(formula):
    """Add the _xlfn. prefix to newer functions (outside string literals)."""
    if not (isinstance(formula, str) and formula.startswith("=")):
        return formula
    parts = formula.split('"')
    for k in range(0, len(parts), 2):
        parts[k] = _NEW_FN.sub(lambda m: "_xlfn." + m.group(1).upper() + "(", parts[k])
    return '"'.join(parts)


def fix_new_functions(wb):
    n = 0
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                v = c.value
                if isinstance(v, str) and v.startswith("="):
                    g = xlfn(v)
                    if g != v:
                        c.value = g
                        n += 1
    return n


def save(wb, path, full_calc_on_load=True):
    """Save, forcing Excel to recalculate every formula when the file opens.
    Also adds the _xlfn. prefix that newer functions need (NORM.INV, STDEV.S,
    PERCENTILE.INC, ...), so write formulas the normal way."""
    fix_new_functions(wb)
    if full_calc_on_load:
        from openpyxl.workbook.properties import CalcProperties
        wb.calculation = CalcProperties(fullCalcOnLoad=True)
    wb.save(path)
    return path
