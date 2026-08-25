---
name: "glossary-translation"
description: "Fetches terminology from Google Sheets glossary for term lookup and DE/FR/ES/RU translation with glossary-based consistency. Invoke when user asks to look up terms or translate text using the glossary."
---

# Glossary Translation / 术语表翻译

This skill provides terminology lookup and translation services using a Google Sheets glossary (38K+ terms, 24 columns, 12 languages). It supports two main workflows: (1) term lookup by Chinese or English keywords, and (2) English-to-target-language translation with glossary-based terminology consistency.

## Configuration / 配置

```python
# Python executable (NOT in system PATH - must use full path)
PYTHON = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe"

# Skill directory (auto-detected from script location)
SKILL_DIR = the directory containing this SKILL.md file

# Scripts
FETCH_SCRIPT = SKILL_DIR + r"\scripts\fetch_glossary.py"
SEARCH_SCRIPT = SKILL_DIR + r"\scripts\search_glossary.py"

# Data source: Google Apps Script Web App (deployed as "Anyone" access)
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbx-EB9Mj7slUNSeKPYBpNKIXQWqZpMN0QtJfWDFGlxajtMsN1q5T9EdMTudBbd7Iv7W/exec"

# Cache location
CACHE_FILE = SKILL_DIR + r"\data\glossary_cache.csv"
```

**IMPORTANT**: Always use the full Python path when running scripts:
```powershell
& "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" "<script_path>" <args>
```

## Glossary Structure / 术语表结构

The glossary has 24 columns and 38,000+ rows. Key columns:

| Col | Header | Lang Code | Description |
|-----|--------|-----------|-------------|
| 0 | No. | — | Row number |
| 1 | Chinese (Simplified) | zh | Chinese source term |
| 2 | Type | — | Category (e.g., 世界观 Worldbuilding) |
| 4 | Note | — | Description/notes |
| 6 | EN | en | English translation |
| 7 | EN Optional | — | Alternative English |
| 8 | EN Status | — | Translation status (Confirmed/Revised) |
| 9 | JA | ja | Japanese |
| 12 | KO | ko | Korean |
| 15 | DE | de | German |
| 16 | FR | fr | French |
| 17 | ES-419 | es | Spanish (Latin America) |
| 18 | RU | ru | Russian |
| 19 | PT-BR | pt | Portuguese (Brazil) |
| 20 | TH | th | Thai |
| 21 | ID | id | Indonesian |
| 22 | IT | it | Italian |

Column detection is automatic via the `search_glossary.py` script (priority-based multi-pass matching).

## Prerequisites / 前置条件

The Google Apps Script Web App is already deployed and configured. If the web app URL changes or expires, redeploy:
1. Open the Apps Script project ("Glossary Sync")
2. Click "Deploy" > "Manage deployments"
3. Edit the deployment and re-authorize
4. Update `WEB_APP_URL` in `scripts/fetch_glossary.py`

## Workflow 1: Term Lookup / 术语查询

When the user sends Chinese or English terms and asks for translations in specific languages (DE/FR/ES/RU):

### Step 1: Ensure glossary is cached
```powershell
& "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" "<FETCH_SCRIPT>" --force
```
If the cache is fresh (less than 24 hours old), the cached version is used automatically. Skip `--force` to use cache.

### Step 2: Search for terms
```powershell
& "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" "<SEARCH_SCRIPT>" search "term1" "term2" --lang DE,FR,ES,RU
```
- The script searches ALL language columns (Chinese, English, German, etc.)
- Results include all matching rows with their translations in every detected language
- Missing translations are flagged automatically
- The search is case-insensitive and supports substring matching

### Step 3: Present results
Display results in a clear markdown table:
| Source Term | Matched Column | ZH | EN | DE | FR | ES | RU | JA | KO | Status |
- Also include Type and Note columns for context
- Flag any terms with missing translations (show "⚠ Missing: DE, FR" etc.)
- If no match found, inform the user and suggest checking the glossary directly

## Workflow 2: Translation with Glossary / 基于术语表翻译

When the user sends English text (and optionally Chinese reference text) for translation:

### Step 1: Scan for glossary terms
```powershell
& "C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe" "<SEARCH_SCRIPT>" scan "the english text here" --lang DE,FR,ES,RU
```
This scans the entire glossary (38K+ rows) and returns any entries whose terms appear in the text.
- ASCII terms use word-boundary matching (prevents false positives like "NTE" matching "encountered")
- CJK terms use substring matching
- Results include translations in all detected languages

### Step 2: Extract additional potential terms
Beyond the scan results, identify additional potential glossary terms from the English text:
- Proper nouns (character names, place names, organization names)
- Technical/game-specific terminology
- Key phrases that might have established translations
- Search for these additional terms using the `search` command

### Step 3: Cross-check with Chinese reference (if provided)
If the user also provided Chinese text:
1. Search the glossary for key Chinese terms from the Chinese text
2. Check if different Chinese terms map to the same English term in the glossary
3. Check if the same Chinese term maps to different English terms
4. Use the Chinese text to identify terms the English scan might have missed
5. Report any conflicts found (different ZH → same EN, or same ZH → different EN)

### Step 4: Present terms for confirmation (CRITICAL - do NOT skip)
Present ALL identified terms in a confirmation table:

**确认术语表 / Confirm Glossary Terms**

| # | English Term | ZH (Glossary) | ZH (User Text) | DE | FR | ES | RU | Type | Status |
|---|-------------|---------------|-----------------|----|----|----|----|------|--------|
| 1 | ... | ... | ... | ... | ... | ... | ... | ... | OK / ⚠ Missing DE,FR |

- Flag terms where: glossary has English but no DE/FR/ES/RU translation
- Flag terms where: Chinese from user text differs from glossary Chinese
- Flag terms where: same English maps to different Chinese entries
- Flag terms where: EN Status is not "Confirmed" (still in draft)
- Ask the user: "请确认以上术语是否正确，如有需要修改或补充的请告知。/ Please confirm these terms are correct. Let me know if any need correction."

### Step 5: WAIT for user confirmation
**DO NOT proceed with translation until the user confirms the terms.** This is a mandatory checkpoint.

### Step 6: Translate
After user confirmation:
1. Translate the **English** text to the target language(s) — NOT the Chinese
2. Use confirmed glossary terms consistently throughout the translation
3. Chinese text is ONLY for reference and term verification, never as translation source
4. If the user requested multiple languages, translate to each separately
5. Present translations clearly, highlighting where glossary terms were used

### Step 7: Note any unresolved terms
If any terms could not be resolved (not in glossary, user didn't provide translation), list them at the end for the user to add to the glossary later.

## Script Usage / 脚本使用

### fetch_glossary.py
Downloads glossary data from Google Apps Script Web App and caches as CSV.
```
python fetch_glossary.py              # Use cache if fresh, otherwise download
python fetch_glossary.py --force      # Force re-download
python fetch_glossary.py --info       # Show cache info only
```

### search_glossary.py
Searches the cached glossary for terms. Outputs JSON.
```
python search_glossary.py search "term1" "term2" --lang DE,FR    # Search specific terms
python search_glossary.py scan "english text to scan" --lang DE  # Scan text for glossary terms
python search_glossary.py info                                    # Show glossary structure
python search_glossary.py headers                                 # Show column headers
```

**Output format**: JSON with the following structure:
```json
{
  "headers": ["No.", "Chinese (Simplified)", ...],
  "column_map": {"zh": 1, "en": 6, "de": 15, ...},
  "results": [
    {
      "search_term": "...",
      "found": true,
      "matches": [{
        "row_index": 123,
        "matched_value": "...",
        "translations": {"zh": "...", "en": "...", "de": "...", ...},
        "extra": {"Type": "...", "Note": "..."},
        "missing_translations": ["DE", "FR"]
      }]
    }
  ]
}
```

## Error Handling / 错误处理

1. **Web app not accessible**: If the download fails with HTTP error, the Apps Script web app may need re-authorization. Go to the Apps Script editor > Deploy > Manage deployments > Edit > Re-authorize.
2. **Cache not found**: Run `fetch_glossary.py --force` to download a fresh copy.
3. **Column detection failure**: If language columns cannot be auto-detected, ask the user to specify column indices.
4. **Python not found**: Use the full path `C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe`.
5. **Large response timeout**: The glossary is ~5MB. Timeout is set to 120 seconds. If it times out, retry.

## Important Notes / 重要说明

- The glossary cache is stored in the skill's `data/` directory and refreshed every 24 hours (or on `--force`)
- All DE/FR/ES/RU translations are based on English, not Chinese
- Chinese text is ONLY used as reference for term verification
- The term confirmation step is MANDATORY before translation — never skip it
- If a glossary term has no DE/FR/ES/RU translation, always ask the user before proceeding
- The glossary also contains JA, KO, PT, TH, ID, IT columns — use `--lang` to specify which to check
- Some rows have EN Status = "Revised" (not yet confirmed) — flag these for the user's attention
