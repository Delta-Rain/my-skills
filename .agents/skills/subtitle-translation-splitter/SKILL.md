---
name: "subtitle-translation-splitter"
description: "将多语言完整译文按英文断句版 SRT 拆分，生成各语言 SRT 字幕文件。Invoke when user provides a multilingual translation Excel and a segmented English SRT, and needs per-language SRT files with split translations."
---

# 字幕多语言译文断句填充 / Subtitle Translation Splitter

## 概述 / Overview

本 Skill 用于将「多语言译文 Excel」中的完整译文，按照「英文断句版 SRT」的断句结构和时间轴，拆分并生成各语言的 SRT 字幕文件。
This Skill splits complete translations from a multilingual Excel into per-language SRT subtitle files, following the segmentation structure and timecodes of a source English SRT.

**典型场景 / Typical Scenario**: 视频制作中，英文台本已按字幕时长断句并生成带时间轴的 SRT，但其他语言（德/法/西/俄等）的翻译仍是完整句子。需要将译文按同样的段数拆开，填入对应的时间轴，生成各语言的 SRT 字幕。
In video production, the English script has been segmented for subtitle timing and exported as a timecode-based SRT, while other languages (DE/FR/ES/RU etc.) remain as complete sentences. The translations need to be split into the same number of segments and filled into the corresponding timecodes to generate per-language SRT files.

---

## 核心规则 / Core Rule

> **仅将译文拆句，然后根据英文填入即可，不要修改译文本身。**
>
> **Only split the translation sentences and fill them according to the English segments. Do not modify the translation text itself.**
>
> 译文的文字内容必须与 Excel 中的完全一致，只能做拆分（断句），不能增删改任何字符。拆分后的各段拼接（以空格连接）必须等于原始译文。
> The translation text must be identical to the Excel source. Only splitting (segmentation) is allowed — no characters may be added, deleted, or modified. The concatenation of all split parts (joined by spaces) must equal the original translation.

---

## 输入 / 输出规格 / Input / Output

### 输入文件 / Input Files

| 文件 / File | 说明 / Description | 关键内容 / Key Content |
|------|------|----------|
| 多语言译文 Excel | 完整英文句子 + 多语言翻译，表头按语言区分 | EN, ZH, DE, FR, ES, RU 等列 |
| 英文断句版 SRT | 英文已断句，含序号、时间轴、文本 | 序号, `00:00:00,000 --> 00:00:00,000`, 英文文本 |

### 输出文件 / Output Files

每个目标语言生成一个独立 SRT 文件，命名规范: **`<源SRT文件名>-<LANG>.srt`**
Each target language generates an independent SRT file, naming convention: **`<source_srt_name>-<LANG>.srt`**

例如源 SRT 为 `1.0版本PV.srt`，则输出:
For example, if the source SRT is `1.0版本PV.srt`, the outputs are:

```
1.0版本PV-DE.srt
1.0版本PV-FR.srt
1.0版本PV-ES.srt
1.0版本PV-RU.srt
```

- 使用与英文 SRT 完全相同的序号和时间轴
- Uses identical sequence numbers and timecodes as the English SRT
- 编码: UTF-8 with BOM
- Encoding: UTF-8 with BOM

### 语种配置（可扩展） / Language Configuration (Extensible)

> 默认生成 DE/FR/ES/RU 四个语种，后续可按需新增。
> Default: DE/FR/ES/RU. Can be extended with additional languages.

新增语种只需 / To add a new language:
1. 确认 Excel 中有对应语言列 / Verify the language column exists in Excel
2. 将语言 code 传入 `--languages` 参数 / Pass the language code to `--languages`
3. 脚本自动通过表头匹配定位列 / The script auto-detects the column via header matching

### 列映射（自动检测） / Column Mapping (Auto-Detected)

> 列位置不固定，脚本通过表头自动匹配。无需手动指定列号。
> Column positions are not fixed. The script auto-detects columns via header text. No manual column numbers needed.

**匹配策略 / Matching Strategy**:

| 优先级 / Priority | 策略 / Strategy | 示例 / Example |
|--------|------|------|
| 1 | 精确匹配（不区分大小写）/ Exact match (case-insensitive) | `EN` → `en`, `DE` → `de` |
| 2 | 包含匹配 / Contains match | `英 EN` → EN, `德语翻译` → DE |
| 3 | 分词匹配 / Word-boundary match | `英/EN/备注` → EN |

**支持的表头写法 / Supported Header Variants**:

| 语言 / Language | 可识别表头 / Recognizable Headers |
|------|------|
| EN | `英文`, `英语`, `EN`, `en`, `ENG`, `English`, `英 EN` |
| DE | `德语`, `德文`, `DE`, `de`, `DEU`, `German`, `Deutsch` |
| FR | `法语`, `法文`, `FR`, `fr`, `FRA`, `French`, `Français` |
| ES | `西班牙语`, `西语`, `ES`, `es`, `ESP`, `Spanish`, `Español` |
| RU | `俄语`, `俄文`, `RU`, `ru`, `RUS`, `Russian`, `Русский` |
| JA | `日语`, `日文`, `JA`, `ja`, `JPN`, `Japanese`, `日本語` |
| KO | `韩语`, `韩文`, `KO`, `ko`, `KOR`, `Korean`, `한국어` |

<!-- 此处可补充特定项目的表头差异 / Add project-specific header variants here -->

---

## 工作流程 / Workflow

### 推荐执行方式 / Recommended Execution

为节省 token，建议按以下两步执行 / To save tokens, execute in two steps:

**Step 1: 检测模式 / Check-only mode** — 先检测边缘情况，不生成文件
```bash
python split_translations.py <excel> <srt> <output_dir> --check-only
```

- 脚本输出边缘情况报告 / The script outputs an edge case report
- 如有阻塞项，通知用户确认后再继续 / If blocking issues exist, notify user and wait for approval
- 如无阻塞项，直接进入 Step 2 / If no blocking issues, proceed to Step 2

**Step 2: 完整执行 / Full run** — 生成各语言 SRT 并验证
```bash
python split_translations.py <excel> <srt> <output_dir>
```

### Step 1: 加载数据 + 自动检测列 / Load Data & Auto-Detect Columns

1. 自动检测 Excel 工作表（取第一个）/ Auto-detect Excel sheet (use first one)
2. 通过表头文本自动匹配各语言列号 / Auto-detect column indices via header text matching
3. 解析英文 SRT，提取序号、时间轴、文本 / Parse English SRT for index, timecodes, text
4. 打印检测结果确认 / Print detection results for confirmation

### Step 2: 英文断句匹配 / English Segment Matching

将 SRT 断句段匹配回 Excel 完整句。
Match SRT segments back to Excel complete sentences.

**匹配算法（四级回退） / Matching Algorithm (4-Level Fallback)**:

| 优先级 / Priority | 策略 / Strategy | 说明 / Description |
|--------|------|------|
| 1 | 标准归一化前缀匹配 / Standard normalized prefix match | 转小写、去标点、合并空格 / Lowercase, strip punctuation, collapse spaces |
| 2 | 激进归一化前缀匹配 / Aggressive normalized prefix match | 去所有非单词字符 / Remove all non-word characters |
| 3 | 回查已使用行 / Re-check used rows | 处理重复字幕行 / Handle duplicate subtitle entries |
| 4 | 激进归一化 + 回查 / Aggressive + re-check | 兜底组合策略 / Last-resort combination |

### Step 3: 边缘情况检测 / Edge Case Detection

检测后分为**阻塞项**和**非阻塞项**，阻塞项需用户确认后方可继续。
Detected issues are categorized as **blocking** or **non-blocking**. Blocking issues require user approval before proceeding.

| 类型 / Type | 说明 / Description | 阻塞? / Blocking? |
|------|------|------|
| Excel-only / Excel 有 SRT 无 | Excel 中有但 SRT 中没有的英文（可能视频制作时删去）/ EN in Excel but not in SRT (likely cut during editing) | 否 / No |
| SRT-only / SRT 有 Excel 无 | SRT 中有但 Excel 中没有的英文 / EN in SRT but not in Excel | **是 / Yes** |
| Partial / 不完全匹配 | Excel 与 SRT 英文不完全一致（拼写差异等）/ Excel and SRT text not exactly matching (spelling differences etc.) | **是 / Yes** |
| Short split / 译文过短 | 译文词数 < 拆分段数，难以拆分 / Translation word count < segment count, hard to split | **是 / Yes** |

**非阻塞项处理 / Non-blocking handling**: Excel-only 条目可继续执行，执行完毕后通知用户。
Excel-only entries can proceed; notify user after completion.

**阻塞项处理 / Blocking handling**: 必须通知用户，获得批准后再继续（或跳过该条目）。
Must notify user and obtain approval before continuing (or skip the entry).

### Step 4: 译文拆分 / Translation Splitting

对每个匹配组（1 条完整句 → N 条 SRT 段），将各语言译文拆成 N 段。
For each match group (1 complete sentence → N SRT segments), split each language's translation into N parts.

**拆分算法 / Splitting Algorithm**:
1. 按英文断句段的字符长度比例计算目标分割位置 / Calculate target split positions based on English segment character-length proportions
2. 优先在标点后空格处断句 / Prefer breaking at post-punctuation spaces
3. 回退到最近空格 / Fall back to nearest space
4. 确保各段最小长度 / Ensure minimum part length
5. 过短段从相邻段借词 / Redistribute words from adjacent parts for too-short segments

**约束 / Constraints**:
- 拆分后各段拼接（空格连接）必须等于原始译文 / Concatenation of parts must equal original
- 不增删改任何字符，仅在空格处拆分 / No character modification, split only at spaces

### Step 5: 生成 SRT / Generate SRT

1. 遍历目标语言列表 / Iterate target languages
2. 使用英文 SRT 的序号和时间轴，文本替换为拆分后译文 / Use source SRT index/timecodes, replace text with split translations
3. 输出文件命名: `<源SRT名>-<LANG>.srt` / Output naming: `<source_name>-<LANG>.srt`
4. 编码 UTF-8 BOM，换行 `\r\n` / Encoding UTF-8 BOM, line ending `\r\n`

### Step 6: 验证（完整验证清单，不可省略） / Verification (Full Checklist, Mandatory)

运行完整验证清单（不可省略）。所有检查均通过回读输出文件进行实际验证，不使用硬编码值。
Run the full verification checklist (mandatory). All checks perform actual file read-back verification — no hardcoded values.

| 编号 / ID | 检查项 / Check | 说明 / Description |
|--------|------|------|
| 6a | 译文完整性 / Translation integrity | 拼接归一化文本 == 原文归一化文本 / Concatenated normalized text == original normalized text |
| 6b | 空值检查 / Empty cell check | 统计空译文条目数 / Count empty translation cells |
| 6c | 填充率 / Fill rate | 译文条目填充率（目标 100%）/ Translation fill rate (target 100%) |
| 6d | 匹配率 / Match rate | SRT 匹配率（目标 100%）/ SRT match rate (target 100%) |
| 6e | 文件存在性 / File existence | 回读检查所有输出文件存在 / Read-back verify all output files exist |
| 6f | 条目数 + 时间轴 / Entry count + timecodes | 回读各语言 SRT，验证条目数和时间轴与源 SRT 完全一致 / Read back each SRT, verify entry count and timecodes match source |
| 6g | UTF-8 BOM / Encoding | 读取文件头 3 字节验证 BOM 标记 / Read first 3 bytes to verify BOM marker |
| 6h | CRLF 换行 / Line endings | 二进制模式读取，验证所有换行为 CRLF / Binary read, verify all line endings are CRLF |

---

## 边缘情况详细说明 / Edge Case Details

### Excel-only（非阻塞）/ Excel-only (Non-blocking)

Excel 中有但 SRT 中没有的英文句子。通常是因为视频/字幕制作时删去了某些台词。
EN sentences in Excel but not in SRT. Usually because lines were cut during video/subtitle production.

**处理 / Handling**: 继续执行，完成后通知用户。不影响 SRT 生成质量。
Proceed, notify user after completion. Does not affect SRT quality.

### SRT-only（阻塞）/ SRT-only (Blocking)

SRT 中有但 Excel 中没有的英文。可能是字幕中临时添加了新台词。
EN in SRT but not in Excel. Possibly new lines added to subtitles.

**处理 / Handling**: 通知用户，该条目译文留空或保留英文原文（按 `--keep-en-on-unmatched` 配置）。
Notify user. The entry's translation is left empty or kept as English (per `--keep-en-on-unmatched`).

### Partial match（阻塞）/ Partial Match (Blocking)

Excel 与 SRT 英文不完全一致，通常因拼写差异（如 `converts into` vs `convertsinto`）。
Excel and SRT text not exactly matching, usually due to spelling differences.

**处理 / Handling**: 通知用户显示 diff，用户确认后继续。匹配仍会通过容差机制完成。
Notify user with diff. Proceed after user confirms. Matching still completes via tolerance mechanism.

### Short split（阻塞）/ Short Split (Blocking)

译文需要拆成多段，但词数不足。例如德语译文只有 1 个词但需要拆成 2 段。
Translation needs splitting into multiple parts but has too few words. E.g., German translation has 1 word but needs 2 parts.

**处理 / Handling**: 通知用户，整句放入第一段，其余段为空。
Notify user. Entire translation goes to first part, remaining parts are empty.

---

## 参考实现 / Reference Implementation

```bash
# 检测模式（先跑）/ Check-only mode (run first)
python split_translations.py "translations.xlsx" "en.srt" "./output/" --check-only

# 完整执行 / Full run
python split_translations.py "translations.xlsx" "en.srt" "./output/"

# 自定义语种 / Custom languages
python split_translations.py "translations.xlsx" "en.srt" "./output/" --languages DE FR ES RU JA

# 未匹配条目保留英文 / Keep English for unmatched
python split_translations.py "translations.xlsx" "en.srt" "./output/" --keep-en-on-unmatched
```

---

## SRT 格式规范 / SRT Format Specification

### SRT 结构 / SRT Structure

```
序号 / Index
HH:MM:SS,mmm --> HH:MM:SS,mmm
字幕文本 / Subtitle text

序号 / Index
...
```

- 时间轴格式: `HH:MM:SS,mmm`（逗号分隔毫秒）/ Timecode: `HH:MM:SS,mmm` (comma for milliseconds)
- 条目间用空行分隔 / Entries separated by blank lines

### 输出规范 / Output Specification

- 编码 / Encoding: UTF-8 with BOM
- 换行符 / Line ending: `\r\n` (Windows CRLF)
- 文件命名 / Filename: `<源SRT名>-<LANG>.srt`
- 空译文 / Empty translation: 保留时间轴，文本留空 / Keep timecode, text empty

---

## 断句比例计算详细规则 / Split Ratio Calculation Rules

> 以下规则描述译文拆分时如何根据英文断句段计算各段的目标位置与断点。
> The following rules describe how target positions and break points are calculated based on English segment proportions.

**1. 目标位置计算 / Target Position Calculation**

- 以英文断句段的字符长度作为权重 / Weight by English segment character length
- 累计比例映射到译文长度 / Cumulative proportion mapped to translation length
- 公式 / Formula: `target[i] = int(cumsum_len[0..i] / total_en_len * len(translation))`
- 若英文总长度为 0，退化为均分 / If total EN length is 0, fallback to even split

**2. 断点选择优先级 / Break Point Priority**

| 优先级 / Priority | 策略 / Strategy | 条件 / Condition |
|--------|------|------|
| 1 | 标点后空格 / Post-punctuation space | 空格前一字符属于 `PUNCT_CHARS`，在有效范围内 / Previous char in `PUNCT_CHARS`, within valid range |
| 2 | 任意空格 / Any space | 标点空格距离目标 > 20% 时回退 / Fall back if punctuation space > 20% away |
| 3 | 放宽约束 / Relaxed | 忽略 `max_pos`，取最近空格 / Ignore `max_pos`, take nearest space |

**3. 最小段长度 / Minimum Part Length**

- `min_part = max(3, len(translation) // (num_parts * 5))`
- 防止单字/双字字幕段 / Prevent single/double-character subtitle parts

**4. 过短段借词 / Short Part Word Redistribution**

- 段长度 < 2 字符时触发 / Triggered when part length < 2 chars
- 向前借: 从前一段末尾拆词 / Borrow from previous part's end
- 向后借: 从后一段开头拆词 / Borrow from next part's start

**5. 完整性约束 / Integrity Constraint**

- 断点仅选在空格位置 / Break points only at space positions
- 拼接后归一化文本必须等于原始译文归一化文本 / Concatenated normalized text must equal original normalized text
- 不允许在词中间断开 / No mid-word breaks

**6. 边界情况 / Edge Cases**

| 情况 / Case | 处理 / Handling |
|------|----------|
| `num_parts == 1` | 原文整段返回 / Return as-is |
| 译文为空 / Empty translation | 返回空段列表 / Return empty parts |
| 空格数不足 / Insufficient spaces | 整段放第一段 / All text in first part |

---

## 注意事项 / Notes

### 数据结构 / Data Structure
<!-- 此处可补充特定项目的表头格式等细节 / Add project-specific header formats here -->

- Excel 表头可能含合并单元格，脚本用 `header=None` 读取 / Excel headers may have merged cells; script reads with `header=None`
- 部分完整句在 Excel 中跨多行存储，匹配时支持组合 / Some sentences span multiple Excel rows; matching supports combining
- Excel 可能含中文列（ZH），不参与 SRT 生成但可校对参考 / Excel may have Chinese column (ZH); not used for SRT but useful for reference

### 匹配 / Matching
<!-- 此处可补充匹配难点 / Add matching difficulties here -->

- SRT 断句点可能在任意空格处，不一定在标点处 / SRT break points may be at any space, not necessarily at punctuation
- 注意 Unicode 标点差异: curly quotes, em-dash, non-breaking space / Watch for Unicode punctuation differences
- SRT 换行符 `\r\n` vs `\n` 需统一处理 / Normalize SRT line endings

### 拆分 / Splitting
<!-- 此处可补充语言拆分偏好 / Add language-specific splitting preferences here -->

- 不同语言语序不同，按英文比例拆分可能导致语义不自然 / Different word orders may cause unnatural splits
- 德语动词常在句末 / German verbs often at sentence end
- 法语标点前可能有空格（`« text »`）/ French may have spaces before punctuation
- CJK 语言无空格分隔，当前算法不适用 / CJK languages have no spaces; current algorithm not applicable

### 输出 / Output
<!-- 此处可补充输出规范细节 / Add output specification details here -->

- 输出文件保留源 SRT 的时间轴和序号 / Output files preserve source SRT timecodes and indices
- 文件命名: `<源SRT名>-<LANG>.srt` / Filename: `<source_name>-<LANG>.srt`
- 编码 UTF-8 BOM，换行 `\r\n` / Encoding UTF-8 BOM, line ending `\r\n`

### 环境 / Environment
<!-- 此处可补充环境配置 / Add environment config here -->

- Python 3.x, 依赖库: pandas, openpyxl
- 若 Python 不在 PATH，需查找安装路径 / If Python not in PATH, find install path
- pip 安装可能需要国内镜像源 / pip may need domestic mirror

---

## 验证清单 / Verification Checklist

脚本每次运行都会输出完整验证清单（回读实际文件验证，非硬编码）/ The script outputs the full checklist on every run (actual file read-back, no hardcoded values):

- [ ] [6a] 译文完整性检查通过（拼接 = 原文，0 错误）/ Translation integrity (0 errors)
- [ ] [6b] 无空译文条目 / No empty translation entries
- [ ] [6c] 填充率 100% / Fill rate 100%
- [ ] [6d] 所有 SRT 断句段都已匹配（匹配率 100%）/ All SRT segments matched (100%)
- [ ] [6e] 所有输出文件存在 / All output files exist
- [ ] [6f] 各语言 SRT 条目数与英文 SRT 一致 / SRT entry count consistent across languages
- [ ] [6f] 各语言 SRT 时间轴与英文 SRT 完全一致 / Timecodes identical to source SRT
- [ ] [6g] SRT 编码正确（UTF-8 BOM）/ SRT encoding correct (UTF-8 BOM)
- [ ] [6h] SRT 换行符正确（CRLF）/ SRT line endings correct (CRLF)
- [ ] 多段拆分抽查语义自然（人工检查）/ Multi-segment split quality acceptable (manual check)
- [ ] 边缘案例处理正确（人工检查）/ Edge cases handled correctly (manual check)

---

## 已知问题与改进方向 / Known Issues & Future Improvements
<!-- 此处可补充使用中发现的问题 / Add issues found during use here -->

- [ ] 拆分基于字符长度比例，未考虑语义边界 / Split based on character ratio, not semantic boundaries
- [ ] 未支持 CJK（中日韩）无空格语言拆分 / No CJK language support
- [ ] 未支持 ASS/SSA/VTT 等其他字幕格式 / No ASS/SSA/VTT format support
- [ ] 匹配算法时间复杂度较高，大文件可能需优化 / Matching complexity high for large files

---

## 待补充 / To Be Added

<!-- 用户可在此处继续添加注意事项、细节、规范等 / Add notes, details, conventions here -->

-
