"""
recalc_check.py - recalculate a workbook with LibreOffice and report formula errors.

    python recalc_check.py Model.xlsx                 # error scan
    python recalc_check.py Model.xlsx Total_Profit Avg_Cost   # also print named cells

openpyxl writes formulas but never calculates them. This script opens a COPY in
LibreOffice (headless), recalculates, and scans every cell for #NAME?, #REF!,
#VALUE!, #DIV/0!, #NUM!, #N/A. It never modifies the original file.

Limits: LibreOffice does not evaluate Excel data tables (What-If > Data Table)
and cannot run Solver. Check those numbers with scm_check.py instead.
"""
import os
import shutil
import subprocess
import sys
import tempfile

from openpyxl import load_workbook

ERRORS = ("#NAME?", "#REF!", "#VALUE!", "#DIV/0!", "#NUM!", "#N/A", "#NULL!", "Err:")


def recalc(path):
    tmp = tempfile.mkdtemp()
    src = os.path.join(tmp, "in_" + os.path.basename(path))
    shutil.copy(path, src)
    out_dir = os.path.join(tmp, "out")
    os.makedirs(out_dir)
    cmd = ["soffice", "--headless", "--calc", "--convert-to", "xlsx", "--outdir", out_dir, src]
    subprocess.run(cmd, check=True, capture_output=True, timeout=180)
    return os.path.join(out_dir, os.path.basename(src))


def scan(path, show_names=()):
    rec = recalc(path)
    wb = load_workbook(rec, data_only=True)
    problems = []
    n_formulas = 0
    wf = load_workbook(path)  # to count formulas in the original
    for ws in wf.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith("="):
                    n_formulas += 1
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith(ERRORS):
                    problems.append(f"{ws.title}!{c.coordinate}: {c.value}")
    print(f"{n_formulas} formulas, {len(problems)} error cells")
    for p in problems[:40]:
        print("  ", p)
    for name in show_names:
        dn = wb.defined_names.get(name)
        if dn is None:
            print(f"  name {name}: NOT DEFINED")
            continue
        for sheet, ref in dn.destinations:
            cells = wb[sheet][ref.replace("$", "")]
            if isinstance(cells, tuple):
                vals = [[c.value for c in r] for r in cells]
                flat = [v for r in vals for v in r]
                print(f"  {name} = {flat[:12]}{' ...' if len(flat) > 12 else ''}")
            else:
                print(f"  {name} = {cells.value}")
    return problems


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    bad = scan(sys.argv[1], sys.argv[2:])
    sys.exit(1 if bad else 0)
