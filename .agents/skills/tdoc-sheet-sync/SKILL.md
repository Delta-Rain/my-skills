---
name: tdoc-sheet-sync
description: This skill should be used when the user asks to download the latest version of a Tencent Docs online spreadsheet (e.g. "下载最新版本"), compare the 海外简中 (overseas Simplified Chinese, column E) column against the previous local copy to report increments (增量) and modifications (改量, including rows inserted in the middle of the document), request the user's approval, and then overwrite the local source file. Only the 海外简中 column is authoritative; other Chinese columns are treated as original/source text and are not diffed. When multiple Chinese columns exist and 海外简中 cannot be uniquely identified from the header, ASK the user which column is 海外简中 before proceeding. Applies to Tencent Docs sheets where only specific sub-sheets are needed and merged cells must be flattened.
agent_created: true
---

# Tdoc Sheet Sync（腾讯文档表格增量同步）

## Overview

A repeatable workflow for keeping a local working copy of a Tencent Docs online
sheet in sync. Each time the user says "下载最新版本" (download the latest
version), pull the newest data from the online document, diff the 海外简中
column (column E) against the existing local file, surface the 增量 (new/inserted
rows) and 改量 (changed values) to the user, ask for approval, and — only after
approval — overwrite the local source file with the fresh download.

Merged cells are always expanded so every previously-merged cell carries its
value (required for clean diffing and editing).

## Column Policy（列规则，必读）

本工作流**仅以「海外简中」列为准**，其余列一律视为辅助上下文，不参与判定：

- **唯一权威列 = 海外简中列**（默认 E 列 / 1-based index 5，可用 `--e-col` 调整）。
  增量、改量、减量均只基于该列判定与报告。
- **其他中文列（如国服简中、中文文案、繁中等）一律视为「原始中文列」**：
  它们是源语言/参考内容，只作为 diff 报告中的上下文展示（如平面名、国服简中），
  **不作为判定依据、不参与比对**，也不写入判定结果。
- **多中文列时必须先向用户确认**：当表格中存在多个疑似中文列、且无法从表头
  唯一确定哪一列是「海外简中」时，**必须先向用户 check 确认海外简中列是哪一列**，
  得到明确答复后才继续执行。不得自行猜测。
  - 若表头存在明确标注「海外简中」的列 → 直接使用该列，无需确认。
  - 若表头无明确标注、存在多个中文列 → 暂停并向用户列出候选列，请其指定。
- 输出 xlsx 仍保留全量列（便于上下文核对），但**所有 diff 与报告只针对海外简中列**。

## Inputs

Resolve these before running:

- **Target path** (where to save/overwrite the file). Provided by the user each
  run. If the user gives no path, default to the **current workspace root**
  (e.g. `C:\Users\Administrator\WorkBuddy\<date>\`) with a filename derived from
  the sheet name (e.g. `平面文案_20260827_1430.xlsx`). Do NOT ask when no path is
  given — use the default.
- **Filename timestamp — minute precision (必填)**: every output filename MUST
  carry a timestamp to the **minute**, format `原始文件名_YYYYMMDD_HHMM.xlsx`
  (e.g. `平面文案_20260827_1435.xlsx`). Minute precision is required because
  multiple versions may be generated within the same hour. Hour precision
  (`YYYYMMDD_HH`) is NOT acceptable.
- **Online document identity**: the Tencent Docs sheet URL, or its `file_id`
  plus `sheet_id`. From a URL `https://docs.qq.com/sheet/<FILEID>?tab=<SHEETID>`,
  `FILEID` is the file_id and the `tab` value is the sheet_id. If the user has
  not supplied it yet, ask once and remember it for the session.
- **Sheet name** (optional): set as the worksheet title in the output xlsx.

## Workflow

### Step 1 — Resolve the target path
Decide the output path: user-provided path, else `<workspace>/<sheet_name>.xlsx`.
The existing file at that path (if any) is the **baseline** (旧) for the diff.

### Step 2 — Download the latest version
Use `scripts/download_sheet.py` (auto-discovers the tencent-docs skill's
`tencentdocs.py` and handles merged-cell expansion + chunking):

```bash
python <skill>/scripts/download_sheet.py \
  --file-id <FILEID> --sheet-id <SHEETID> \
  --out <target>.new.xlsx --sheet-name <SHEET_NAME>
```

Alternative (no script): call `tdoc_call sheet-mcp get_sheet_info`,
`get_cell_data` (return_csv=false), `get_merged_cells`, expand each merge's
top-left value into all its cells, then write xlsx with openpyxl. Always write
to a **temporary** name (e.g. `<target>.new.xlsx`) first — never overwrite the
baseline until approved.

### Step 3 — Diff the 海外简中 column (E)
Run the diff script comparing baseline vs the fresh download:

```bash
python <skill>/scripts/diff_overseas_column.py \
  --old <target> --new <target>.new.xlsx \
  --sheet <SHEET_NAME> --report <target>.diff.md
```

The script aligns rows by a content key (all columns **except** E), so:
- 增量 = rows present in NEW but not OLD — including rows **inserted in the
  middle** of the document (not just appended).
- 改量 = rows in both whose E value changed.
- 减量 (removals) are listed for awareness only.

### Step 4 — Report to the user
Show the 增量 / 改量 summary from the diff output. Use clear Chinese, list each
changed/added entry with its 平面名 (col B) and 国服简中 (col D) context so the
user understands what moved.

### Step 5 — Request approval
Ask the user to approve overwriting the source file. Use AskUserQuestion with a
single question (header "覆盖确认"):
- Option "确认覆盖" — proceed to overwrite.
- Option "取消" — keep the old file, discard the `.new.xlsx`, stop.

Do NOT overwrite without explicit approval.

### Step 6 — Overwrite (on approval)
Replace the target file with the approved download, then clean up the temp file:

```bash
mv / rename <target>.new.xlsx -> <target>
rm -f <target>.new.xlsx   # after successful rename
```

**因为文件名自带分钟时间戳（`_YYYYMMDD_HHMM.xlsx`），每次批准的新版本不会覆盖
历史版本**，而是作为独立文件保留；被替换/生成的即为该时间戳对应的最新版本。
If the user rejects, delete `<target>.new.xlsx` and leave the baseline intact.

## Notes & Edge Cases

- **Column E = 海外简中** (1-based index 5). If the sheet layout differs,
  pass `--e-col` to `diff_overseas_column.py`.
- **Merged cells**: always expanded before writing, so every cell holds a value.
  The diff therefore operates on flat data.
- **Large sheets**: `download_sheet.py` chunks requests to stay under the
  20,000-cell `get_cell_data` limit automatically.
- **Multiple sheets**: only the requested `sheet_id` is downloaded; other tabs
  are ignored (matches "只要某个 sheet" needs).
- **Token/network**: fetching requires the host-injected Tencent Docs credential;
  if `tdoc_call` returns `400006`, tell the user to re-authorize Tencent Docs and
  retry.

## Resources

### scripts/download_sheet.py
Downloads a Tencent Docs sheet to xlsx with merged cells expanded. Auto-discovers
`tencentdocs.py`; accepts `--file-id --sheet-id --out --sheet-name [--td --rows --cols]`.

### scripts/diff_overseas_column.py
Compares two xlsx files and reports 增量/改量/减量 for column E (海外简中),
handling mid-document inserts via content-key alignment. Accepts
`--old --new --sheet [--report PATH] [--e-col N]`.
