"""
腾讯文档本地化表格导出脚本
用途：将腾讯文档 get_cell_data 返回的 CSV 数据保存为本地 xlsx 文件
仅执行：拆分合并单元格并铺满填充；保留原始全部列与内容，不调整任何列字段
使用前：按下方"配置参数"区修改参数
"""
import json
import csv
import io
import re
from datetime import datetime
from openpyxl import Workbook

# ============ 配置参数（根据实际表格修改） ============
RAW_JSON_PATH = r"<raw_sheet_data.json 本地路径>"   # get_cell_data 结果保存的 JSON 路径
OUTPUT_DIR = r"<输出目录路径>"                       # 输出 xlsx 的目录
ORIGINAL_NAME = "<原始文件名前缀>"                   # 输出文件名前缀
# merged_cells 从 get_merged_cells 工具返回结果中复制（格式如 "<sheet_id>$A1:B2"）
MERGED_CELLS = ["<sheet_id>$A1:B2", "..."]
# ======================================================


def col_letter_to_index(letter):
    """列字母转0-based索引，如 A->0, B->1, J->9"""
    result = 0
    for c in letter:
        result = result * 26 + (ord(c.upper()) - ord('A') + 1)
    return result - 1


def parse_cell_ref(ref):
    """解析单元格引用，如 A5 -> (row=4, col=0) 0-based"""
    match = re.match(r'([A-Z]+)(\d+)', ref)
    if match:
        col = col_letter_to_index(match.group(1))
        row = int(match.group(2)) - 1
        return row, col
    return None, None


def main():
    # 1. 读取并解析CSV
    with open(RAW_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    reader = csv.reader(io.StringIO(data["csv_data"]))
    rows = list(reader)
    print(f"原始行数: {len(rows)}")

    # 2. 拆分合并单元格并铺满填充（左上角值填充至区域内所有单元格）
    for mc in MERGED_CELLS:
        range_part = mc.split('$')[1]
        start_ref, end_ref = range_part.split(':')
        sr, sc = parse_cell_ref(start_ref)
        er, ec = parse_cell_ref(end_ref)
        if sr is None:
            continue
        value = rows[sr][sc] if sr < len(rows) and sc < len(rows[sr]) else ""
        for r in range(sr, er + 1):
            for c in range(sc, ec + 1):
                while r >= len(rows):
                    rows.append([])
                while c >= len(rows[r]):
                    rows[r].append("")
                rows[r][c] = value

    # 3. 保留原始全部列与内容（不做任何列字段调整）

    # 4. 保存xlsx
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filepath = rf"{OUTPUT_DIR}\{ORIGINAL_NAME}_{timestamp}.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = ORIGINAL_NAME
    for row in rows:
        ws.append(row)
    wb.save(filepath)
    print(f"已保存: {filepath} ({len(rows)} 行)")
    return filepath


if __name__ == "__main__":
    main()
