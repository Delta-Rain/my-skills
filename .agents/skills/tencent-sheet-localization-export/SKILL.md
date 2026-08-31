---
name: tencent-sheet-localization-export
description: 从腾讯文档在线表格（docs.qq.com）导出指定子表为本地 xlsx 文件。仅执行两项操作：拉取子表数据、将合并单元格拆分并把左上角值铺满填充至整个区域；保留原始全部列与内容、不调整任何列字段。按"原始文件名_YYYYMMDD_HHMM.xlsx"格式保存到本地，便于后续用 memoQ 等翻译工具导入及云端文档迭代。适用于游戏本地化文案表、多语言翻译素材表的定期同步场景。
---

# 腾讯文档表格本地化导出 Skill

## 概述

从腾讯文档在线表格中导出指定子表，保存为本地 xlsx 文件，供本地翻译工具（如 memoQ）导入使用。本 Skill **只做两件事**：

1. 下载/拉取指定子表的原始数据
2. 将合并单元格拆分，并把左上角的值铺满填充至该区域内每个单元格

**不做**任何列字段的调整或修改：不删除列、不筛选列、不重写表头、不修改任何原始列内容与格式。全部原始列与内容原样保留，仅合并单元格被铺满填充。

## 前置依赖

- 已安装并授权 `tencent-docs-operations` MCP 连接器（通过 tool_search 取回工具 schema 后再调用）
- Python 3.x + `openpyxl` 库（`pip install openpyxl`）
- 目标腾讯文档的 file_id（从 URL 中提取，如 `https://docs.qq.com/sheet/DYXVYdUpra29NcXpx?tab=BB08J2` 中的 `DYXVYdUpra29NcXpx`）

## 触发场景

用户说以下任何一句话时触发本 Skill：

- "获取/下载这份腾讯文档的表格内容"
- "把这个 sheet 导出来处理一下合并单元格"
- "从腾讯文档导出本地翻译素材"
- "把云表格同步到本地翻译工具"
- 提供 docs.qq.com 表格链接并要求"下载""导出""拉取""处理合并单元格"等

## 工作流

### 步骤 1：调用 tool_search 取回 MCP 工具 schema

在调用任何 `mcp__tencent_docs__*` 工具前，必须先用 tool_search 按工具能力关键词取回参数定义。涉及的工具：

- `mcp__tencent_docs__get_sheet_info` — 获取子表信息（file_id 参数）
- `mcp__tencent_docs__get_cell_data` — 获取单元格数据 CSV（file_id, sheet_id, start_row, end_row, start_col, end_col, return_csv）
- `mcp__tencent_docs__get_merged_cells` — 获取合并单元格信息（file_id, sheet_id, start_row, end_row, start_col, end_col）

### 步骤 2：获取子表信息，定位目标 sheet

调用 `mcp__tencent_docs__get_sheet_info`，传入 `file_id`，返回所有子表的 `sheet_id`、`sheet_name`、行列数。

从结果中找到目标 sheet，记录其 `sheet_id`、`row_count`、`col_count`。

### 步骤 3：并行获取单元格数据和合并单元格信息

**3a. 获取单元格数据（CSV 格式）**

调用 `mcp__tencent_docs__get_cell_data`：
- `file_id`: 文档 ID
- `sheet_id`: 目标子表 ID
- `start_row`: 0
- `end_row`: row_count - 1
- `start_col`: 0
- `end_col`: col_count - 1
- `return_csv`: true

返回结果中的 `csv_data` 字段为完整 CSV 字符串。**若结果过长被系统持久化到外部 URL**（返回 `persisted-output` 提示），必须先用 `curl.exe -L -o <本地路径> "<持久化URL>"` 下载完整内容，再读取本地文件处理，不能仅凭截断摘要操作。

**3b. 获取合并单元格信息**

调用 `mcp__tencent_docs__get_merged_cells`：
- `file_id`: 文档 ID
- `sheet_id`: 目标子表 ID
- `start_row`: 0
- `end_row`: row_count - 1
- `start_col`: 0
- `end_col`: col_count - 1

返回 `merged_cells` 数组，格式如 `BB08J2$A5:B6`（sheet_id$起始单元格:结束单元格），行号为 1-based。

### 步骤 4：本地处理（Python，仅铺满合并单元格）

将 `assets/process_sheet.py` 复制到本地，按实际情况调整顶部配置参数后运行：

- `RAW_JSON_PATH`: 步骤 3a 下载/保存的 JSON 文件路径
- `OUTPUT_DIR`: 输出目录
- `ORIGINAL_NAME`: 原始文件名前缀
- `MERGED_CELLS`: 步骤 3b 返回的合并单元格列表

处理逻辑（**不涉及任何列字段调整**）：
1. 解析 CSV 为二维数组
2. 遍历 merged_cells，解析每个合并区域的起止行列，将左上角值填充到区域内所有单元格
3. 原样保存全部列与内容（不删列、不筛选、不改表头）
4. 保存为 xlsx

### 步骤 5：文件命名与保存

文件名格式：`{原始文件名}_{YYYYMMDD}_{HHMM}.xlsx`
- 时间戳取当前日期、小时、分钟（24小时制，分钟级精度，同一小时内多次导出互不覆盖）
- 保存到项目路径下

```python
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
filename = f"{original_name}_{timestamp}.xlsx"
```

### 步骤 6：验证输出

用 openpyxl 回读生成的文件，检查：
- 列数、行数与原始表格一致（原始列全部保留）
- 合并单元格是否已正确铺满填充（抽查多个合并区域）
- 表头与原始内容未被改动

验证通过后再交付给用户。

## 注意事项

1. **合并单元格填充**：填充必须在任何后续处理之前完成，保证每个单元格都携带其左上角值（便于翻译工具导入与差异比对）。
2. **结果持久化**：`get_cell_data` 返回的 CSV 数据可能因过长被系统持久化到外部 URL，必须下载完整内容后再处理，不能仅凭截断摘要操作。
3. **时间戳精度**：使用日期+小时+分钟粒度，同一天内多次导出不会互相覆盖，保留历史版本。
4. **openpyxl 依赖**：运行前确保已安装 `pip install openpyxl`。
5. **写操作确认**：本 Skill 仅涉及本地文件写入，不修改云端文档；如需修改云端表格需额外确认。
6. **保留原始内容**：本 Skill 不调整任何列字段；如后续需要删列/改列，请另行明确说明。

## 故障排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| get_cell_data 返回空 csv_data | 区域参数超出实际范围 | 用 get_sheet_info 确认实际行列数，end_row/end_col 设为 count-1 |
| 合并单元格未填充 | merged_cells 列表不完整或解析错误 | 确认 get_merged_cells 返回的完整列表，检查列字母解析逻辑 |
| 输出文件乱码 | CSV 编码问题 | 确保读取 JSON 时使用 encoding="utf-8" |
| openpyxl 未安装 | 缺少依赖 | 运行 `pip install openpyxl` |
| 文件名含特殊字符 | 原始文件名含非法字符 | 确保 ORIGINAL_NAME 不含 \ / : * ? " < > \| |
| MCP 工具不可用 | 连接器未授权或超时 | 重新授权 tencent-docs-operations 连接器，或用 get_sheet_info 复核后重试一次 |
