#!/usr/bin/env python3
"""Download a Tencent Docs online sheet to a local .xlsx, expanding all merged
cells so each previously-merged cell carries the (top-left) value.

Usage:
  python download_sheet.py --file-id DYXVYdUpra29NcXpx --sheet-id BB08J2 --out 平面文案.xlsx

Optional:
  --td PATH      explicit path to tencentdocs.py (else auto-discovered)
  --rows N --cols M   force grid size (else read from get_sheet_info)
  --sheet-name NAME   set the worksheet title in the output xlsx
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

try:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
    from openpyxl import Workbook
    from openpyxl.styles import Alignment


def find_tencentdocs():
    # auto-discover the tencent-docs skill entrypoint
    base = os.path.expanduser("~/.workbuddy/plugins/cache/workbuddy-builtin/tencent-docs-plugin")
    hits = glob.glob(os.path.join(base, "*", "skills", "tencent-docs", "tencentdocs.py"))
    return hits[0] if hits else None


def tdoc(td_path, tool, args, timeout=120):
    payload = json.dumps(args)
    proc = subprocess.run(
        [sys.executable, td_path, "tdoc_call", "sheet-mcp", tool, payload],
        capture_output=True, text=True, encoding="utf-8", timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError("tdoc_call %s failed: %s" % (tool, proc.stderr.strip()))
    out = json.loads(proc.stdout)
    return json.loads(out["result"]["content"][0]["text"])


def col_letter_to_idx(s):
    idx = 0
    for ch in s:
        idx = idx * 26 + (ord(ch.upper()) - ord("A") + 1)
    return idx - 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file-id", required=True)
    ap.add_argument("--sheet-id", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--td", default=None)
    ap.add_argument("--rows", type=int, default=None)
    ap.add_argument("--cols", type=int, default=None)
    ap.add_argument("--sheet-name", default=None)
    args = ap.parse_args()

    td = args.td or find_tencentdocs()
    if not td or not os.path.exists(td):
        raise SystemExit("tencentdocs.py not found; pass --td PATH")
    print("[info] using tencentdocs.py:", td)

    # determine grid size
    n_rows, n_cols = args.rows, args.cols
    if n_rows is None or n_cols is None:
        info = tdoc(td, "get_sheet_info", {"file_id": args.file_id})
        for s in info["sheets"]:
            if s["sheet_id"] == args.sheet_id:
                n_rows = n_rows or s["row_count"]
                n_cols = n_cols or s["col_count"]
                break
    print("[info] grid size: rows=%s cols=%s" % (n_rows, n_cols))

    # fetch structured cells, chunked to stay under the 20000-cell limit
    grid = [[None] * n_cols for _ in range(n_rows)]
    cap = 18000
    r = 0
    while r < n_rows:
        rows_this = max(1, cap // n_cols)
        end_r = min(n_rows, r + rows_this) - 1
        res = tdoc(td, "get_cell_data", {
            "file_id": args.file_id, "sheet_id": args.sheet_id,
            "start_row": r, "start_col": 0,
            "end_row": end_r, "end_col": n_cols - 1,
            "return_csv": False,
        })
        for c in res["cells"]:
            rr, cc = c["row"], c["col"]
            if 0 <= rr < n_rows and 0 <= cc < n_cols:
                vt = c.get("value_type")
                if vt == "NUMBER":
                    grid[rr][cc] = c.get("number_value")
                elif vt == "BOOL":
                    grid[rr][cc] = c.get("bool_value")
                else:
                    grid[rr][cc] = c.get("string_value")
        r = end_r + 1

    # fetch merged ranges and expand them (fill top-left value into all cells)
    merge_res = tdoc(td, "get_merged_cells", {
        "file_id": args.file_id, "sheet_id": args.sheet_id,
        "start_row": 0, "start_col": 0,
        "end_row": n_rows - 1, "end_col": n_cols - 1,
    })
    merge_ranges = merge_res.get("merged_cells", merge_res.get("ranges", []))
    pat = re.compile(r"([A-Z]+)(\d+):([A-Z]+)(\d+)")
    filled = 0
    for entry in merge_ranges:
        s = entry if isinstance(entry, str) else json.dumps(entry)
        m = pat.search(s)
        if not m:
            continue
        c1, r1 = col_letter_to_idx(m.group(1)), int(m.group(2)) - 1
        c2, r2 = col_letter_to_idx(m.group(3)), int(m.group(4)) - 1
        val = grid[r1][c1] if 0 <= r1 < n_rows and 0 <= c1 < n_cols else None
        for rr in range(r1, r2 + 1):
            for cc in range(c1, c2 + 1):
                if 0 <= rr < n_rows and 0 <= cc < n_cols:
                    grid[rr][cc] = val
                    filled += 1
    print("[info] merged ranges=%d cells filled=%d" % (len(merge_ranges), filled))

    # write xlsx
    wb = Workbook()
    ws = wb.active
    ws.title = args.sheet_name or "Sheet1"
    for rr in range(n_rows):
        for cc in range(n_cols):
            v = grid[rr][cc]
            cell = ws.cell(row=rr + 1, column=cc + 1, value=v)
            if isinstance(v, str) and "\n" in v:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    wb.save(args.out)
    print("[done] saved:", args.out, "size:", os.path.getsize(args.out))


if __name__ == "__main__":
    main()
