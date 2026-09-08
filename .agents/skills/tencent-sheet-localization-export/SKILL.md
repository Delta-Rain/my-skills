---
name: tencent-sheet-localization-export
description: 处理腾讯文档在线表格（docs.qq.com）的本地化导出与增量同步。下载指定子表到本地 xlsx，自动拆分合并单元格并铺满填充；支持两种工作模式——纯导出（下载+合并单元格铺满，保留全部原始列内容、不调整列字段）与增量同步（对比海外简中列，报告增量/改量，用户批准后覆盖）。MCP 方案与 Python 方案均可，执行时优先可用且快的方案。按"原始文件名_YYYYMMDD_HHMM.xlsx"保存，供 memoQ 等翻译工具导入及云端文档迭代。
---

# 腾讯文档表格本地化导出与增量同步 Skill

## 概述

从腾讯文档在线表格中导出指定子表并保存为本地 xlsx 文件，供本地翻译工具（如 memoQ）导入使用。本 Skill 支持两种工作模式：

1. **纯导出模式**（默认）：下载/拉取指定子表 → 拆分合并单元格并铺满填充 → 原样保留全部列与内容保存为 xlsx。
2. **增量同步模式**：在纯导出的基础上，对比本地已有副本与最新下载的**海外简中列**，报告增量（新增行）/改量（修改值），经用户批准后覆盖本地副本。

**统一处理规则**：
- **合并单元格**：总是拆分并把左上角值铺满填充至整个区域（便于翻译工具导入与差异比对）。
- **列字段不调整**：不删除列、不筛选列、不重写表头、不修改任何原始列内容与格式；全部原始列原样保留。
- **图例/备注行**：不删除，原样保留（即"原样下载即可"）。
- **尾部空行**：可删除，保持文件整洁。

## 前置依赖

- 已安装并授权 `tencent-docs-operations` MCP 连接器（通过 tool_search 取回工具 schema 后再调用）
- Python 3.x + `openpyxl` 库（`pip install openpyxl`）
- 目标腾讯文档的 file_id（从 URL 中提取，如 `https://docs.qq.com/sheet/DYXVYdUpra29NcXpx?tab=BB08J2` 中的 `DYXVYdUpra29NcXpx`）
- 增量同步模式额外需要本地已有副本（baseline，作为 diff 的旧版本）

## Column Policy（列规则，必读）

本工作流**仅以「海外简中」列为准**，其余列一律视为辅助上下文，不参与判定：

- **唯一权威列 = 海外简中列**（默认 E 列 / 1-based index 5，可用 `--e-col` 调整）。增量、改量、减量均只基于该列判定与报告。
- **其他中文列（如国服简中、中文文案、繁中等）一律视为「原始中文列」**：它们是源语言/参考内容，只作为 diff 报告中的上下文展示（如平面名、国服简中），**不作为判定依据、不参与比对**，也不写入判定结果。
- **多中文列时必须先向用户确认**：当表格中存在多个疑似中文列、且无法从表头唯一确定哪一列是「海外简中」时，**必须先向用户 check 确认海外简中列是哪一列**，得到明确答复后才继续执行。不得自行猜测。
  - 若表头存在明确标注「海外简中」的列 → 直接使用该列，无需确认。
  - 若表头无明确标注、存在多个中文列 → 暂停并向用户列出候选列，请其指定。
- 输出 xlsx 仍保留全量列（便于上下文核对），但**所有 diff 与报告只针对海外简中列**。

## 触发场景

用户说以下任何一句话时触发本 Skill：

- "获取/下载这份腾讯文档的表格内容"
- "把这个 sheet 导出来处理一下合并单元格"
- "从腾讯文档导出本地翻译素材"
- "把云表格同步到本地翻译工具"
- "下载最新版本" / "看看有没有更新" / "增量同步一下"
- 提供 docs.qq.com 表格链接并要求"下载""导出""拉取""同步""处理合并单元格"等

## 工作流

### 步骤 1：调用 tool_search 取回 MCP 工具 schema

在调用任何 `mcp__tencent_docs__*` 工具前，必须先用 tool_search 按工具能力关键词取回参数定义。涉及的工具：

- `mcp__tencent_docs__get_sheet_info` — 获取子表信息（file_id 参数）
- `mcp__tencent_docs__get_cell_data` — 获取单元格数据 CSV/结构化（file_id, sheet_id, start_row, end_row, start_col, end_col, return_csv）
- `mcp__tencent_docs__get_merged_cells` — 获取合并单元格信息（file_id, sheet_id, start_row, end_row, start_col, end_col）

### 步骤 2：获取子表信息，定位目标 sheet

调用 `mcp__tencent_docs__get_sheet_info`，传入 `file_id`，返回所有子表的 `sheet_id`、`sheet_name`、行列数。

从结果中找到目标 sheet，记录其 `sheet_id`、`row_count`、`col_count`。

### 步骤 3：下载最新版本（MCP 方案与 Python 方案二选一）

**执行原则：能调用哪个就调用哪个，实际执行时优先速度快、依赖完整的方案。** 通常优先尝试 Python 方案（一次脚本完成下载+合并展开）；若 tencentdocs.py 不可用（如未安装/未找到），立即回退到 MCP 方案。

**方案 A：Python 脚本方案（推荐优先尝试，速度快）**

```bash
python <skill>/assets/scripts/download_sheet.py \
  --file-id <FILEID> --sheet-id <SHEETID> \
  --out <目标路径>.new.xlsx --sheet-name <SHEET_NAME>
```

- 脚本自动发现 tencent-docs skill 的 `tencentdocs.py` 入口（`~/.workbuddy/plugins/cache/workbuddy-builtin/tencent-docs-plugin/.../tencentdocs.py`），通过 `tdoc_call sheet-mcp ...` 直接拉取结构化数据
- 自动完成合并单元格展开 + 分块（低于 20,000 单元格限制）
- 若找不到 `tencentdocs.py`（报 "tencentdocs.py not found"），改用方案 B
- 增量同步模式下，`--out` 使用临时名 `<目标>.new.xlsx`，先不覆盖 baseline

**方案 B：MCP 工具方案（回退/环境受限时）**

**3B-a. 获取单元格数据**

调用 `mcp__tencent_docs__get_cell_data`：
- `file_id`: 文档 ID
- `sheet_id`: 目标子表 ID
- `start_row`: 0
- `end_row`: row_count - 1
- `start_col`: 0
- `end_col`: col_count - 1
- `return_csv`: true（便于保存处理）

返回结果中的 `csv_data` 字段为完整 CSV 字符串。**若结果过长被系统持久化到外部 URL**（返回 `persisted-output` 提示），必须先用 `curl.exe -L -o <本地路径> "<持久化URL>"` 下载完整内容，再读取本地文件处理，不能仅凭截断摘要操作。

**3B-b. 获取合并单元格信息**

调用 `mcp__tencent_docs__get_merged_cells`：
- `file_id`: 文档 ID
- `sheet_id`: 目标子表 ID
- `start_row`: 0
- `end_row`: row_count - 1
- `start_col`: 0
- `end_col`: col_count - 1

返回 `merged_cells` 数组，格式如 `BB08J2$A5:B6`（sheet_id$起始单元格:结束单元格），行号为 1-based。

**3B-c. 本地处理（Python）**

将 `assets/process_sheet.py` 复制到本地，按实际情况调整顶部配置参数后运行：

- `RAW_JSON_PATH`: 步骤 3B-a 下载/保存的 JSON 文件路径
- `OUTPUT_DIR`: 输出目录
- `ORIGINAL_NAME`: 原始文件名前缀
- `MERGED_CELLS`: 步骤 3B-b 返回的合并单元格列表

处理逻辑（**不涉及任何列字段调整**）：
1. 解析 CSV 为二维数组
2. 遍历 merged_cells，解析每个合并区域的起止行列，将左上角值填充到区域内所有单元格
3. 原样保留全部列与内容（不删列、不筛选、不改表头；不删除图例/备注行）
4. 删除尾部全空行
5. 保存为 xlsx

### 步骤 4：选择工作模式

- **纯导出模式**：步骤 3 的输出即最终交付，跳到步骤 6 验证。
- **增量同步模式**：需要本地已有副本作为 baseline（旧版），继续步骤 5。

### 步骤 5：Diff 海外简中列（仅增量同步模式）

对 baseline 与最新下载做 diff，对比海外简中列：

```bash
python <skill>/assets/scripts/diff_overseas_column.py \
  --old <baseline.xlsx> --new <最新下载>.xlsx \
  --sheet <SHEET_NAME> --report <报告路径>.md
```

脚本按内容键（除海外简中列外的所有列）对齐行，因此：
- 增量 = NEW 中有而 OLD 没有的行——包括**插入在文档中间**的行（不仅是追加在末尾的）
- 改量 = 两版都有、但海外简中值被修改的行
- 减量 = OLD 有而 NEW 没有的行（仅供 awareness）

### 步骤 6：验证输出

用 openpyxl 回读生成的文件，检查：
- 列数、行数与原始表格一致（原始列全部保留，图例行未删）
- 合并单元格是否已正确铺满填充（抽查多个合并区域）
- 表头与原始内容未被改动
- 尾部无空行（若执行了去尾部空行）
- 增量同步模式：diff 报告中的增量/改量与实际文件一致

验证通过后再交付给用户。

### 步骤 7：文件命名与保存

文件名格式：`{原始文件名}_{YYYYMMDD}_{HHMM}.xlsx`
- 时间戳取当前日期、小时、分钟（24小时制，分钟级精度，同一小时内多次导出互不覆盖）
- 保存到项目路径下

```python
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
filename = f"{original_name}_{timestamp}.xlsx"
```

### 步骤 8：增量同步模式的批准与覆盖

**请求用户批准**后才会覆盖本地副本（纯导出模式跳过此步）：
- **确认覆盖** → 将 `.new.xlsx` 重命名为正式文件名（自带分钟时间戳，不覆盖历史版本，作为独立文件保留）；删除临时文件
- **取消** → 删除 `.new.xlsx`，保留 baseline 不变

**未经批准不得覆盖本地副本。**

## 注意事项

1. **合并单元格填充**：填充必须在任何后续处理之前完成，保证每个单元格都携带其左上角值（便于翻译工具导入与差异比对）。
2. **结果持久化**：`get_cell_data` 返回的 CSV 数据可能因过长被系统持久化到外部 URL，必须下载完整内容后再处理，不能仅凭截断摘要操作。
3. **时间戳精度**：使用日期+小时+分钟粒度，同一天内多次导出不会互相覆盖，保留历史版本。
4. **openpyxl 依赖**：运行前确保已安装 `pip install openpyxl`。
5. **写操作确认**：本 Skill 仅涉及本地文件写入，不修改云端文档；如需修改云端表格需额外确认。增量同步模式的覆盖动作必须先经用户批准。
6. **保留原始内容**：本 Skill 不调整任何列字段、不删除图例/备注行；如后续需要删列/改列，请另行明确说明。
7. **方案选择**：Python 方案与 MCP 方案产出一致；执行时优先可用且快的方案，一种方案失败立即回退另一种。

## 故障排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| get_cell_data 返回空 csv_data | 区域参数超出实际范围 | 用 get_sheet_info 确认实际行列数，end_row/end_col 设为 count-1 |
| download_sheet.py 报 tencentdocs.py not found | tencent-docs 插件未安装/路径变化 | 改用 MCP 方案（步骤 3B） |
| 合并单元格未填充 | merged_cells 列表不完整或解析错误 | 确认 get_merged_cells 返回的完整列表，检查列字母解析逻辑 |
| 输出文件乱码 | CSV 编码问题 | 确保读取 JSON 时使用 encoding="utf-8" |
| openpyxl 未安装 | 缺少依赖 | 运行 `pip install openpyxl` |
| 文件名含特殊字符 | 原始文件名含非法字符 | 确保 ORIGINAL_NAME 不含 \ / : * ? " < > \| |
| MCP 工具不可用 | 连接器未授权或超时 | 重新授权 tencent-docs-operations 连接器，或用 get_sheet_info 复核后重试一次 |

## Resources

### assets/scripts/download_sheet.py
通过 tencentdocs.py（tdoc_call）下载腾讯文档子表到 xlsx，自动展开合并单元格、分块拉取。接受 `--file-id --sheet-id --out --sheet-name [--td --rows --cols]`。

### assets/scripts/diff_overseas_column.py
对比两个 xlsx 文件，报告海外简中列（默认 E 列）的 增量/改量/减量，支持中间插入行的检测。接受 `--old --new --sheet [--report PATH] [--e-col N]`。

### assets/process_sheet.py
将 get_cell_data 返回的 CSV（JSON 落盘）保存为本地 xlsx：拆分合并单元格并铺满填充、保留全部原始列与内容、不删图例行、删除尾部空行。
