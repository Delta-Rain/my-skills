#!/usr/bin/env python3
"""
字幕多语言译文断句填充 - 参考实现
Subtitle Translation Splitter - Reference Implementation

将多语言译文 Excel 中的完整译文，按英文断句版 SRT 的断句结构和时间轴，
拆分并生成各语言的 SRT 字幕文件。

核心规则：仅拆分译文，不修改译文本身。拆分后各段拼接（空格连接）必须等于原始译文。

Usage:
    python split_translations.py <excel> <en_srt> <output_dir> [options]

Options:
    --excel-sheet <name>     Excel 工作表名 (默认: 自动检测第一个)
    --languages <codes>      目标语言列表 (默认: DE FR ES RU)
    --keep-en-on-unmatched   未匹配条目保留英文原文 (默认: 留空)
    --check-only             仅检测边缘情况，不生成 SRT 文件
"""

import os
import re
import json
import argparse
import pandas as pd


# ============================================================
# 1. 表头自动检测列映射
# ============================================================

LANG_PATTERNS = {
    'EN': ['英文', '英语', '英文原文', 'en', 'eng', 'english', '英 en', '英en', '英en'],
    'DE': ['德语', '德文', 'de', 'deu', 'ger', 'german', 'deutsch'],
    'FR': ['法语', '法文', 'fr', 'fra', 'fre', 'french', 'français', 'francais'],
    'ES': ['西班牙语', '西语', 'es', 'esp', 'spanish', 'español', 'espanol'],
    'RU': ['俄语', '俄文', 'ru', 'rus', 'russian', 'русский'],
    'JA': ['日语', '日文', 'ja', 'jpn', 'japanese', '日本語'],
    'KO': ['韩语', '韩文', 'ko', 'kor', 'korean', '한국어'],
    'PT': ['葡萄牙语', '葡语', 'pt', 'por', 'portuguese', 'português'],
    'IT': ['意大利语', '意语', 'it', 'ita', 'italian', 'italiano'],
    'ZH': ['中文', '汉语', 'zh', 'chi', 'chinese', '国服台本'],
}

def detect_columns(df, languages):
    """
    读取 Excel 表头行，通过模糊/语义匹配自动检测各语言列号。

    匹配策略（按优先级）:
      1. 精确匹配（不区分大小写）
      2. 包含匹配（表头包含语言关键词）
      3. 语言 code 前缀匹配（如 "英 EN" -> EN）

    Returns:
        dict: {"EN": col_idx, "DE": col_idx, ...}
    Raises:
        ValueError: 如果 EN 列或任何目标语言列未找到
    """
    # 读取表头行
    header = {}
    for col in range(df.shape[1]):
        val = df.iloc[0, col]
        if pd.notna(val) and str(val).strip():
            header[col] = str(val).strip()

    all_langs = ['EN'] + languages
    result = {}

    for lang in all_langs:
        patterns = [p.lower() for p in LANG_PATTERNS.get(lang, [lang.lower()])]
        found_col = None

        # Pass 1: exact match (case-insensitive)
        for col, text in header.items():
            if col in result.values():
                continue
            if text.lower().strip() in patterns:
                found_col = col
                break

        # Pass 2: contains match
        if found_col is None:
            for col, text in header.items():
                if col in result.values():
                    continue
                text_lower = text.lower()
                for p in patterns:
                    if len(p) >= 2 and p in text_lower:
                        found_col = col
                        break
                if found_col is not None:
                    break

        # Pass 3: language code as standalone word
        if found_col is None:
            for col, text in header.items():
                if col in result.values():
                    continue
                words = re.split(r'[\s/|·\-]', text.lower())
                if lang.lower() in words:
                    found_col = col
                    break

        if found_col is None:
            if lang == 'EN':
                raise ValueError(f"Cannot find English column in Excel header. Headers: {header}")
            else:
                raise ValueError(f"Cannot find '{lang}' column in Excel header. Headers: {header}")

        result[lang] = found_col

    return result


# ============================================================
# 2. SRT 解析与生成
# ============================================================

def parse_srt(srt_path, encoding='utf-8'):
    """解析 SRT 文件，返回字幕条目列表。"""
    content = None
    for enc in [encoding, 'utf-8-sig', 'utf-8', 'gbk', 'latin-1']:
        try:
            with open(srt_path, 'r', encoding=enc) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    if content is None:
        raise FileNotFoundError(f"Cannot read SRT file: {srt_path}")

    content = content.replace('\r\n', '\n').replace('\r', '\n')
    content = content.lstrip('\ufeff')
    entries = []
    blocks = re.split(r'\n\s*\n', content.strip())
    time_pattern = re.compile(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})')

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.split('\n')
        if len(lines) < 2:
            continue
        idx = None
        line_offset = 0
        try:
            idx = int(lines[0].strip())
            line_offset = 1
        except ValueError:
            line_offset = 0

        time_line_idx = None
        start = end = None
        for i in range(line_offset, min(line_offset + 3, len(lines))):
            m = time_pattern.search(lines[i])
            if m:
                start = m.group(1)
                end = m.group(2)
                time_line_idx = i
                break
        if time_line_idx is None:
            continue

        text = '\n'.join(lines[time_line_idx + 1:]).strip()
        entries.append({
            'index': idx if idx is not None else len(entries) + 1,
            'start': start, 'end': end, 'text': text,
        })
    return entries


def generate_srt(entries, output_path, encoding='utf-8-sig'):
    """生成 SRT 文件 (UTF-8 BOM, \\r\\n 换行)。"""
    lines = []
    for entry in entries:
        lines.append(str(entry['index']))
        lines.append(f"{entry['start']} --> {entry['end']}")
        lines.append(entry['text'])
        lines.append('')
    content = '\r\n'.join(lines)
    content = content.rstrip('\r\n') + '\r\n'
    with open(output_path, 'w', encoding=encoding, newline='') as f:
        f.write(content)


def get_output_filename(srt_path, lang):
    """根据源 SRT 文件名生成输出文件名: <源名>-<LANG>.srt"""
    basename = os.path.basename(srt_path)
    name_without_ext = os.path.splitext(basename)[0]
    return f"{name_without_ext}-{lang}.srt"


# ============================================================
# 3. 文本归一化
# ============================================================

def normalize(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def normalize_aggressive(text):
    text = text.lower()
    text = re.sub(r'[^\w]', '', text)
    return text


# ============================================================
# 4. 英文断句匹配
# ============================================================

def match_segments(en1_list, en2_list, max_en1_combine=4, max_remaining_tol=8):
    """将 SRT 断句段匹配回 Excel 完整句。返回 (groups, unmatched_srt_indices, partial_matches)。"""
    en1_n = [normalize(s) for s in en1_list]
    en2_n = [normalize(s) for s in en2_list]
    en1_na = [normalize_aggressive(s) for s in en1_list]
    en2_na = [normalize_aggressive(s) for s in en2_list]

    def try_match(search_idx, seg_idx, use_aggressive=False):
        src_n = en1_na if use_aggressive else en1_n
        seg_src_n = en2_na if use_aggressive else en2_n
        seg = seg_src_n[seg_idx]
        for num_en1 in range(1, min(max_en1_combine, len(en1_list) - search_idx + 1)):
            if use_aggressive:
                combined = ''.join(src_n[search_idx + j] for j in range(num_en1))
            else:
                combined = ' '.join(src_n[search_idx + j] for j in range(num_en1))
            en1_indices = list(range(search_idx, search_idx + num_en1))
            if not combined.startswith(seg):
                continue
            consumed = [seg_idx]
            remaining = combined[len(seg):]
            if not use_aggressive:
                remaining = remaining.strip()
            j = seg_idx + 1
            if not remaining:
                return (en1_indices, consumed, False)  # perfect match
            while j < len(en2_list):
                next_seg = seg_src_n[j]
                if remaining.startswith(next_seg):
                    remaining = remaining[len(next_seg):]
                    if not use_aggressive:
                        remaining = remaining.strip()
                    consumed.append(j)
                    j += 1
                    if not remaining:
                        return (en1_indices, consumed, False)  # perfect
                else:
                    break
            if len(remaining) < max_remaining_tol:
                return (en1_indices, consumed, True)  # partial (tolerance)
        return None

    groups = []
    partial_matches = []  # (en1_indices, srt_indices, remaining_text)
    en1_idx = 0
    en2_idx = 0

    while en2_idx < len(en2_list):
        matched = False
        for si in range(en1_idx, len(en1_list)):
            result = try_match(si, en2_idx)
            if result:
                groups.append((result[0], result[1]))
                if result[2]:  # partial
                    partial_matches.append((result[0], result[1]))
                en1_idx = max(result[0]) + 1
                en2_idx = max(result[1]) + 1
                matched = True
                break
        if not matched:
            for si in range(en1_idx, len(en1_list)):
                result = try_match(si, en2_idx, use_aggressive=True)
                if result:
                    groups.append((result[0], result[1]))
                    if result[2]:
                        partial_matches.append((result[0], result[1]))
                    en1_idx = max(result[0]) + 1
                    en2_idx = max(result[1]) + 1
                    matched = True
                    break
        if not matched:
            for ei in range(min(en1_idx, len(en1_list))):
                result = try_match(ei, en2_idx)
                if result:
                    groups.append((result[0], result[1]))
                    if result[2]:
                        partial_matches.append((result[0], result[1]))
                    en2_idx = max(result[1]) + 1
                    matched = True
                    break
        if not matched:
            for ei in range(min(en1_idx, len(en1_list))):
                result = try_match(ei, en2_idx, use_aggressive=True)
                if result:
                    groups.append((result[0], result[1]))
                    if result[2]:
                        partial_matches.append((result[0], result[1]))
                    en2_idx = max(result[1]) + 1
                    matched = True
                    break
        if not matched:
            en2_idx += 1

    matched_srt = set()
    for g in groups:
        matched_srt.update(g[1])
    unmatched_srt = [i for i in range(len(en2_list)) if i not in matched_srt]

    return groups, unmatched_srt, partial_matches


# ============================================================
# 5. 译文拆分
# ============================================================

PUNCT_CHARS = '.,;:!?)]}\u3002\u3001\uff0c\uff1b\uff01\uff1f\u201d\u00bb\u203a\u2013\u2014\u201e\u00ab'

def split_translation(translation, num_parts, en_segments):
    """将译文按英文断句段的比例拆分成 num_parts 段。"""
    if num_parts == 1:
        return [translation]
    if not translation or not translation.strip():
        return [''] * num_parts

    translation = translation.strip()
    spaces = [i for i in range(len(translation)) if translation[i] == ' ']
    if len(spaces) < num_parts - 1:
        return [translation] + [''] * (num_parts - 1)

    punct_spaces = {sp for sp in spaces if sp > 0 and translation[sp - 1] in PUNCT_CHARS}
    seg_lengths = [len(s) for s in en_segments]
    total_len = sum(seg_lengths) if sum(seg_lengths) > 0 else num_parts
    targets = []
    cumsum = 0
    for i in range(num_parts - 1):
        cumsum += seg_lengths[i]
        targets.append(int(cumsum / total_len * len(translation)))

    min_part = max(3, len(translation) // (num_parts * 5))
    used = set()
    break_points = []

    for idx, target in enumerate(targets):
        min_pos = (break_points[-1] + min_part) if break_points else min_part
        remaining_breaks = len(targets) - idx - 1
        max_pos = len(translation) - remaining_breaks * min_part - min_part
        best = None
        best_dist = float('inf')
        for sp in punct_spaces:
            if sp in used or sp < min_pos or sp > max_pos:
                continue
            dist = abs(sp - target)
            if dist < best_dist:
                best_dist = dist
                best = sp
        if best is None or best_dist > len(translation) * 0.2:
            for sp in spaces:
                if sp in used or sp < min_pos or sp > max_pos:
                    continue
                dist = abs(sp - target)
                if dist < best_dist:
                    best_dist = dist
                    best = sp
        if best is None:
            for sp in spaces:
                if sp in used or sp <= (break_points[-1] if break_points else 0):
                    continue
                dist = abs(sp - target)
                if dist < best_dist:
                    best_dist = dist
                    best = sp
        if best is not None:
            break_points.append(best)
            used.add(best)

    break_points.sort()
    parts = []
    prev = 0
    for bp in break_points:
        parts.append(translation[prev:bp].strip())
        prev = bp + 1
    parts.append(translation[prev:].strip())

    for i in range(len(parts)):
        if len(parts[i]) < 2:
            if i > 0 and parts[i - 1]:
                words = parts[i - 1].rsplit(' ', 1)
                if len(words) == 2 and len(words[0]) >= 2:
                    parts[i - 1] = words[0]
                    parts[i] = (words[1] + ' ' + parts[i]).strip() if parts[i] else words[1]
            elif i < len(parts) - 1 and parts[i + 1]:
                words = parts[i + 1].split(' ', 1)
                if len(words) == 2 and len(words[1]) >= 2:
                    parts[i] = (parts[i] + ' ' + words[0]).strip() if parts[i] else words[0]
                    parts[i + 1] = words[1]
    return parts


# ============================================================
# 6. 边缘情况检测
# ============================================================

def detect_edge_cases(groups, unmatched_srt, partial_matches,
                      en_list, srt_texts, translations, languages):
    """
    检测所有边缘情况，返回结构化报告。

    Returns:
        dict with keys:
          - excel_only: Excel 中有但 SRT 中没有的英文 (非阻塞)
          - srt_only: SRT 中有但 Excel 中没有的英文 (阻塞)
          - partial: 匹配但不完全一致 (阻塞)
          - short_split: 译文过短难以拆分 (阻塞)
          - has_blocking: 是否存在阻塞项
    """
    report = {
        'excel_only': [],
        'srt_only': [],
        'partial': [],
        'short_split': [],
        'has_blocking': False,
    }

    # 1. Excel-only: EN entries not used by any match
    used_en = set()
    for en_indices, _ in groups:
        used_en.update(en_indices)
    for i in range(len(en_list)):
        if i not in used_en:
            report['excel_only'].append({
                'excel_row': i + 1,
                'en_text': en_list[i][:120],
            })

    # 2. SRT-only: unmatched SRT entries
    for idx in unmatched_srt:
        report['srt_only'].append({
            'srt_index': idx + 1,
            'srt_text': srt_texts[idx][:120],
        })

    # 3. Partial matches
    for en_indices, srt_indices in partial_matches:
        en_combined = ' '.join(en_list[i] for i in en_indices)
        srt_combined = ' '.join(srt_texts[i] for i in srt_indices)
        report['partial'].append({
            'excel_rows': [i + 1 for i in en_indices],
            'en_text': en_combined[:150],
            'srt_indices': [i + 1 for i in srt_indices],
            'srt_text': srt_combined[:150],
        })

    # 4. Short translations: need to split into >1 parts but translation too short
    for en_indices, srt_indices in groups:
        num_parts = len(srt_indices)
        if num_parts <= 1:
            continue
        for lang in languages:
            text = ' '.join(translations[lang][i] for i in en_indices if translations[lang][i])
            word_count = len(text.split())
            if word_count < num_parts:
                report['short_split'].append({
                    'excel_rows': [i + 1 for i in en_indices],
                    'srt_indices': [i + 1 for i in srt_indices],
                    'lang': lang,
                    'translation': text[:120],
                    'word_count': word_count,
                    'num_parts': num_parts,
                })

    report['has_blocking'] = bool(
        report['srt_only'] or report['partial'] or report['short_split']
    )
    return report


def print_edge_case_report(report):
    """打印边缘情况报告（紧凑格式，节省 token）。"""
    print('\n=== Edge Case Report / 边缘情况报告 ===')

    # Excel-only (non-blocking)
    if report['excel_only']:
        print(f'\n[INFO] Excel-only entries (non-blocking): {len(report["excel_only"])}')
        print(f'  Excel 中有但 SRT 中没有的英文（可能视频制作时删去）:')
        for item in report['excel_only'][:10]:
            print(f'    Row {item["excel_row"]}: {item["en_text"]}')
        if len(report['excel_only']) > 10:
            print(f'    ... and {len(report["excel_only"]) - 10} more')
    else:
        print('\n[OK] No Excel-only entries')

    # SRT-only (blocking)
    if report['srt_only']:
        print(f'\n[BLOCKING] SRT-only entries: {len(report["srt_only"])}')
        print(f'  SRT 中有但 Excel 中没有的英文（需确认）:')
        for item in report['srt_only'][:10]:
            print(f'    SRT#{item["srt_index"]}: {item["srt_text"]}')
        if len(report['srt_only']) > 10:
            print(f'    ... and {len(report["srt_only"]) - 10} more')
    else:
        print('[OK] No SRT-only entries')

    # Partial matches (blocking)
    if report['partial']:
        print(f'\n[BLOCKING] Partial matches: {len(report["partial"])}')
        print(f'  Excel 与 SRT 英文不完全一致（需确认）:')
        for item in report['partial'][:10]:
            print(f'    Excel rows {item["excel_rows"]}: {item["en_text"]}')
            print(f'    SRT #{item["srt_indices"]}: {item["srt_text"]}')
        if len(report['partial']) > 10:
            print(f'    ... and {len(report["partial"]) - 10} more')
    else:
        print('[OK] No partial matches')

    # Short splits (blocking)
    if report['short_split']:
        print(f'\n[BLOCKING] Short translation splits: {len(report["short_split"])}')
        print(f'  译文过短难以拆分（需确认）:')
        for item in report['short_split'][:10]:
            print(f'    {item["lang"]} (rows {item["excel_rows"]}, {item["word_count"]} words -> {item["num_parts"]} parts): {item["translation"]}')
        if len(report['short_split']) > 10:
            print(f'    ... and {len(report["short_split"]) - 10} more')
    else:
        print('[OK] No short translation splits')

    if report['has_blocking']:
        print('\n>>> BLOCKING issues detected. Approval needed before generating SRT.')
    else:
        print('\n>>> No blocking issues. Safe to proceed.')


# ============================================================
# 7. 主流程
# ============================================================

def run(excel_path, srt_path, output_dir,
        excel_sheet=None, languages=None,
        keep_en_on_unmatched=False, check_only=False):
    """
    执行完整流程：加载 -> 检测列 -> 匹配 -> 边缘检测 -> 拆分 -> 生成SRT -> 验证

    Args:
        excel_path:           多语言译文 Excel 路径
        srt_path:             英文断句版 SRT 路径
        output_dir:           输出目录
        excel_sheet:          Excel 工作表名 (None=自动检测第一个)
        languages:            目标语言代码列表
        keep_en_on_unmatched: 未匹配条目保留英文原文
        check_only:           仅检测边缘情况，不生成 SRT
    """
    if languages is None:
        languages = ['DE', 'FR', 'ES', 'RU']

    os.makedirs(output_dir, exist_ok=True)

    # --- Step 1: 加载数据 + 自动检测列 ---
    print('=== Step 1: Loading data & detecting columns ===')
    if excel_sheet:
        df = pd.read_excel(excel_path, sheet_name=excel_sheet, header=None)
    else:
        df_dict = pd.read_excel(excel_path, sheet_name=None, header=None)
        first_sheet = list(df_dict.keys())[0]
        excel_sheet = first_sheet
        df = df_dict[first_sheet]
        print(f'  Auto-detected sheet: {excel_sheet}')

    # 自动检测列映射
    col_map = detect_columns(df, languages)
    en_col = col_map['EN']
    print(f'  Column mapping: {col_map}')
    print(f'  EN -> col {en_col} ({df.iloc[0, en_col]})')
    for lang in languages:
        print(f'  {lang} -> col {col_map[lang]} ({df.iloc[0, col_map[lang]]})')

    # 提取数据
    en_list = []
    translations = {lang: [] for lang in languages}
    for i in range(1, len(df)):
        val = df.iloc[i, en_col]
        if pd.notna(val) and str(val).strip():
            en_list.append(str(val).strip())
            for lang in languages:
                col = col_map[lang]
                v = df.iloc[i, col]
                translations[lang].append(str(v).strip() if pd.notna(v) else '')

    srt_entries = parse_srt(srt_path)
    srt_texts = [e['text'] for e in srt_entries]
    print(f'  Excel: {len(en_list)} sentences | SRT: {len(srt_entries)} entries | Languages: {languages}')

    # --- Step 2: 匹配 ---
    print('\n=== Step 2: Matching segments ===')
    groups, unmatched_srt, partial_matches = match_segments(en_list, srt_texts)
    matched_srt = set()
    for g in groups:
        matched_srt.update(g[1])
    print(f'  {len(groups)} groups | {len(matched_srt)}/{len(srt_texts)} matched | {len(unmatched_srt)} unmatched | {len(partial_matches)} partial')

    # --- Step 3: 边缘情况检测 ---
    report = detect_edge_cases(groups, unmatched_srt, partial_matches,
                               en_list, srt_texts, translations, languages)
    print_edge_case_report(report)

    if check_only:
        print('\n=== Check-only mode: stopping before SRT generation ===')
        return report

    # --- Step 4: 拆分译文 ---
    print('\n=== Step 3: Splitting translations ===')
    srt_translations = {}
    for en_indices, srt_indices in groups:
        num_parts = len(srt_indices)
        segments = [srt_texts[i] for i in srt_indices]
        for lang in languages:
            text = ' '.join(translations[lang][i] for i in en_indices if translations[lang][i])
            parts = split_translation(text, num_parts, segments)
            for j, srt_i in enumerate(srt_indices):
                if srt_i not in srt_translations:
                    srt_translations[srt_i] = {}
                srt_translations[srt_i][lang] = parts[j] if j < len(parts) else ''
    print(f'  Translations assigned to {len(srt_translations)} SRT entries')

    # --- Step 5: 生成各语言 SRT ---
    print('\n=== Step 4: Generating SRT files ===')
    srt_basename = os.path.splitext(os.path.basename(srt_path))[0]
    for lang in languages:
        lang_entries = []
        for i, entry in enumerate(srt_entries):
            new_entry = {'index': entry['index'], 'start': entry['start'], 'end': entry['end'], 'text': ''}
            if i in srt_translations and lang in srt_translations[i]:
                new_entry['text'] = srt_translations[i][lang]
            elif keep_en_on_unmatched:
                new_entry['text'] = entry['text']
            lang_entries.append(new_entry)
        output_filename = f'{srt_basename}-{lang}.srt'
        output_path = os.path.join(output_dir, output_filename)
        generate_srt(lang_entries, output_path)
        filled = sum(1 for e in lang_entries if e['text'])
        print(f'  {lang}: {filled}/{len(lang_entries)} -> {output_filename}')

    # --- Step 6: 验证（完整验证清单，不可省略） ---
    print('\n=== Step 5: Verification (Full Checklist) ===')

    # 6a. 译文完整性检查：拼接归一化文本 == 原文归一化文本
    integrity_errors = 0
    for en_indices, srt_indices in groups:
        for lang in languages:
            orig = ' '.join(translations[lang][i] for i in en_indices if translations[lang][i])
            parts = [srt_translations[ei][lang] for ei in srt_indices if ei in srt_translations]
            reconstructed = ' '.join(p for p in parts if p)
            if normalize(reconstructed) != normalize(orig):
                integrity_errors += 1
                if integrity_errors <= 5:
                    print(f'  [FAIL] Integrity: Excel rows {[i+1 for i in en_indices]} {lang}')
                    print(f'    Original:    {orig[:120]}')
                    print(f'    Reconstruct: {reconstructed[:120]}')
    print(f'  [6a] Integrity errors: {integrity_errors}')

    # 6b. 空值检查：统计空译文条目数
    empty_cells = 0
    for srt_i in srt_translations:
        for lang in languages:
            if not srt_translations[srt_i].get(lang):
                empty_cells += 1
    print(f'  [6b] Empty translation cells: {empty_cells}')

    # 6c. 填充率：译文条目填充率
    total_cells = len(srt_entries) * len(languages)
    filled_cells = total_cells - empty_cells - (len(unmatched_srt) * len(languages))
    fill_rate = filled_cells / total_cells * 100 if total_cells > 0 else 0
    print(f'  [6c] Fill rate: {filled_cells}/{total_cells} = {fill_rate:.1f}%')

    # 6d. 匹配率：SRT 匹配率
    match_rate = len(matched_srt) / len(srt_texts) * 100 if srt_texts else 0
    print(f'  [6d] Match rate: {len(matched_srt)}/{len(srt_texts)} = {match_rate:.1f}%')

    # 6e. 输出文件存在性检查
    output_files = {}
    files_exist = True
    for lang in languages:
        output_filename = f'{srt_basename}-{lang}.srt'
        output_path = os.path.join(output_dir, output_filename)
        exists = os.path.exists(output_path)
        output_files[lang] = (output_path, exists)
        if not exists:
            files_exist = False
            print(f'  [FAIL] Output file missing: {output_filename}')
    print(f'  [6e] Output files exist: {sum(1 for _, e in output_files.values() if e)}/{len(languages)}')

    # 6f. 输出文件回读验证：条目数 + 时间轴一致性
    entry_count_ok = True
    timecode_ok = True
    for lang in languages:
        output_path, exists = output_files[lang]
        if not exists:
            entry_count_ok = False
            timecode_ok = False
            continue
        out_entries = parse_srt(output_path)
        # 条目数检查
        if len(out_entries) != len(srt_entries):
            entry_count_ok = False
            print(f'  [FAIL] {lang}: entry count {len(out_entries)} != source {len(srt_entries)}')
        # 时间轴检查
        for i, (out_e, src_e) in enumerate(zip(out_entries, srt_entries)):
            if out_e['start'] != src_e['start'] or out_e['end'] != src_e['end']:
                timecode_ok = False
                if i < 3:
                    print(f'  [FAIL] {lang} entry {i+1}: timecode mismatch')
                    print(f'    Output: {out_e["start"]} -> {out_e["end"]}')
                    print(f'    Source: {src_e["start"]} -> {src_e["end"]}')
                break
    print(f'  [6f] Entry count consistent: {entry_count_ok}')
    print(f'  [6f] Timecodes identical: {timecode_ok}')

    # 6g. 编码验证：UTF-8 BOM
    bom_ok = True
    for lang in languages:
        output_path, exists = output_files[lang]
        if not exists:
            bom_ok = False
            continue
        with open(output_path, 'rb') as f:
            header = f.read(3)
        if header != b'\xef\xbb\xbf':
            bom_ok = False
            print(f'  [FAIL] {lang}: missing UTF-8 BOM, got {header.hex()}')
    print(f'  [6g] UTF-8 BOM verified: {bom_ok}')

    # 6h. 换行符验证：CRLF
    crlf_ok = True
    for lang in languages:
        output_path, exists = output_files[lang]
        if not exists:
            crlf_ok = False
            continue
        with open(output_path, 'rb') as f:
            raw = f.read()
        if b'\r\n' not in raw:
            crlf_ok = False
            print(f'  [FAIL] {lang}: no CRLF line endings found')
        elif b'\n' in raw.replace(b'\r\n', b''):
            bare_lf = raw.replace(b'\r\n', b'').count(b'\n')
            crlf_ok = False
            print(f'  [FAIL] {lang}: found {bare_lf} bare LF (non-CRLF) line endings')
    print(f'  [6h] CRLF line endings verified: {crlf_ok}')

    # --- 验证清单汇总 ---
    print('\n=== Verification Checklist ===')
    checks = [
        ('All SRT segments matched (100%)', match_rate == 100),
        ('SRT entry count consistent across languages', entry_count_ok),
        ('Timecodes identical to source SRT', timecode_ok),
        ('Translation integrity (0 errors)', integrity_errors == 0),
        ('No empty translation cells', empty_cells == 0),
        ('Fill rate 100%', fill_rate == 100),
        ('All output files exist', files_exist),
        ('Output encoding correct (UTF-8 BOM)', bom_ok),
        ('Output line ending correct (CRLF)', crlf_ok),
    ]
    all_passed = True
    for desc, passed in checks:
        status = '[x]' if passed else '[ ]'
        if not passed:
            all_passed = False
        print(f'  {status} {desc}')

    if all_passed:
        print('\n  >>> ALL CHECKS PASSED <<<')
    else:
        print('\n  >>> SOME CHECKS FAILED - REVIEW OUTPUT ABOVE <<<')

    print(f'\n=== Done | Output dir: {output_dir} ===')
    return report


# ============================================================
# CLI
# ============================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='字幕多语言译文断句填充 (Excel + SRT -> 多语言 SRT)'
    )
    parser.add_argument('excel', help='多语言译文 Excel 路径')
    parser.add_argument('srt', help='英文断句版 SRT 路径')
    parser.add_argument('output_dir', help='输出目录')
    parser.add_argument('--excel-sheet', default=None, help='Excel 工作表名 (默认: 自动检测)')
    parser.add_argument('--languages', nargs='+', default=['DE', 'FR', 'ES', 'RU'],
                        help='目标语言列表 (默认: DE FR ES RU)')
    parser.add_argument('--keep-en-on-unmatched', action='store_true',
                        help='未匹配条目保留英文原文 (默认: 留空)')
    parser.add_argument('--check-only', action='store_true',
                        help='仅检测边缘情况，不生成 SRT 文件')
    args = parser.parse_args()

    run(
        excel_path=args.excel,
        srt_path=args.srt,
        output_dir=args.output_dir,
        excel_sheet=args.excel_sheet,
        languages=args.languages,
        keep_en_on_unmatched=args.keep_en_on_unmatched,
        check_only=args.check_only,
    )
