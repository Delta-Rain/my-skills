#!/usr/bin/env python3
"""
search_glossary.py - Search the cached glossary for terms.

Usage:
    python search_glossary.py search "term1" "term2" [--lang DE,FR,ES,RU]
    python search_glossary.py scan "english text to scan" [--lang DE,FR,ES,RU]
    python search_glossary.py info
    python search_glossary.py headers

Output: JSON to stdout, human-readable messages to stderr.
"""
import csv
import os
import sys
import json
import re
import argparse

# ── Configuration ──────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(SKILL_DIR, "data")
CACHE_FILE = os.path.join(DATA_DIR, "glossary_cache.csv")

# ── Language column detection ─────────────────────────────────
# Maps language codes to possible header keywords (case-insensitive)
LANG_KEYWORDS = {
    "en": ["english", "en", "英文", "英语", "英"],
    "zh": ["chinese", "cn", "zh", "中文", "汉语", "中"],
    "de": ["german", "de", "德语", "德文", "德"],
    "fr": ["french", "fr", "法语", "法文", "法"],
    "es": ["spanish", "es", "西班牙语", "西班牙文", "西"],
    "ru": ["russian", "ru", "俄语", "俄文", "俄"],
    "ja": ["japanese", "ja", "日语", "日文", "日"],
    "ko": ["korean", "ko", "韩语", "韩文", "韩", "朝鲜语"],
    "pt": ["portuguese", "pt", "葡萄牙语", "葡"],
    "it": ["italian", "it", "意大利语", "意"],
    "th": ["thai", "th", "泰语", "泰文", "泰"],
    "id": ["indonesian", "id", "印尼语", "印尼文", "印尼"],
}

# All language codes we care about (for missing-translation detection)
ALL_LANGS = ["en", "zh", "de", "fr", "es", "ru"]


def normalize_lang(lang_input):
    """Normalize a language input to a standard code."""
    lang_input = lang_input.lower().strip()
    for code, keywords in LANG_KEYWORDS.items():
        if lang_input in keywords:
            return code
    return lang_input


def load_glossary():
    """Load the cached glossary CSV. Returns (headers, rows) or (None, None)."""
    if not os.path.exists(CACHE_FILE):
        return None, None

    with open(CACHE_FILE, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            return [], []
        rows = list(reader)
    return headers, rows


def detect_columns(headers):
    """Auto-detect which column index corresponds to which language.

    Uses a priority-based multi-pass approach to avoid false matches:
      Pass 1: Long keywords (3+ ASCII chars) via substring match
      Pass 2: CJK keywords via substring match on original text
      Pass 3: Short ASCII keywords (2 chars) via EXACT match only

    This prevents issues like "es" matching "Chin**es**e".
    """
    col_map = {}  # lang_code -> column_index
    mapped_cols = set()  # column indices already assigned

    # Priority 1: Long keywords — safe for substring matching
    long_keywords = [
        ("en", "english"), ("zh", "chinese"), ("de", "german"),
        ("fr", "french"), ("es", "spanish"), ("ru", "russian"),
        ("ja", "japanese"), ("ko", "korean"), ("pt", "portuguese"),
        ("it", "italian"), ("th", "thai"), ("id", "indonesian"),
        ("zh", "中文"), ("zh", "汉语"), ("en", "英文"), ("en", "英语"),
        ("de", "德语"), ("de", "德文"), ("fr", "法语"), ("fr", "法文"),
        ("es", "西班牙"), ("ru", "俄语"), ("ru", "俄文"),
        ("ja", "日语"), ("ja", "日文"), ("ko", "韩语"), ("ko", "韩文"),
        ("ko", "朝鲜语"), ("pt", "葡萄牙"), ("it", "意大利"),
        ("th", "泰语"), ("th", "泰文"), ("id", "印尼语"), ("id", "印尼文"),
    ]

    # Priority 2: Medium keywords (3-char codes)
    medium_keywords = [
        ("en", "eng"), ("de", "ger"), ("de", "deu"),
        ("fr", "fre"), ("fr", "fra"), ("es", "spa"), ("es", "esp"),
        ("ru", "rus"), ("ja", "jpn"), ("ko", "kor"), ("pt", "por"),
        ("it", "ita"), ("th", "tha"),
    ]

    # Priority 3: Short CJK keywords — safe for substring on CJK text
    cjk_keywords = [
        ("zh", "中"), ("en", "英"), ("de", "德"),
        ("fr", "法"), ("es", "西"), ("ru", "俄"),
        ("ja", "日"), ("ko", "韩"), ("pt", "葡"), ("it", "意"),
        ("th", "泰"),
    ]

    # Priority 4: Short ASCII keywords — EXACT or prefix-with-separator match
    # This handles locale codes like "ES-419", "PT-BR" via prefix matching
    short_exact = [
        ("en", "en"), ("zh", "cn"), ("zh", "zh"),
        ("de", "de"), ("fr", "fr"), ("es", "es"), ("ru", "ru"),
        ("ja", "ja"), ("ko", "ko"), ("pt", "pt"), ("it", "it"),
        ("th", "th"), ("id", "id"),
    ]

    def _try_match(keywords, match_type):
        for i, h in enumerate(headers):
            if i in mapped_cols:
                continue
            h_lower = h.lower().strip()
            for lang_code, kw in keywords:
                if lang_code in col_map:
                    continue
                if match_type == "substring":
                    if kw in h_lower:
                        col_map[lang_code] = i
                        mapped_cols.add(i)
                        break
                elif match_type == "exact":
                    # Exact match
                    if h_lower == kw:
                        col_map[lang_code] = i
                        mapped_cols.add(i)
                        break
                    # Prefix match with separator (e.g., "ES-419" matches "es")
                    if h_lower.startswith(kw + "-") or h_lower.startswith(kw + "_"):
                        col_map[lang_code] = i
                        mapped_cols.add(i)
                        break

    _try_match(long_keywords, "substring")
    _try_match(medium_keywords, "substring")
    _try_match(cjk_keywords, "substring")
    _try_match(short_exact, "exact")

    return col_map


def parse_lang_arg(lang_str):
    """Parse a comma-separated language argument into a list of codes."""
    if not lang_str:
        return ALL_LANGS
    return [normalize_lang(l) for l in lang_str.split(",") if l.strip()]


def safe_get(row, idx):
    """Safely get a value from a row by index."""
    if idx is None or idx < 0 or idx >= len(row):
        return ""
    return row[idx].strip() if row[idx] else ""


def search_terms(terms, lang_codes=None):
    """Search for specific terms in the glossary."""
    headers, rows = load_glossary()
    if headers is None:
        return {
            "error": "Glossary cache not found. Run fetch_glossary.py first.",
            "cache_file": CACHE_FILE,
        }

    col_map = detect_columns(headers)
    if lang_codes is None:
        lang_codes = ALL_LANGS

    # Columns to search in (all language columns that are detected)
    search_cols = set(col_map.values())

    results = []
    for term in terms:
        term_lower = term.lower().strip()
        if not term_lower:
            continue

        matches = []
        for row_idx, row in enumerate(rows):
            for col_idx in search_cols:
                val = safe_get(row, col_idx)
                if not val:
                    continue
                # Check for exact match or substring match
                if term_lower in val.lower():
                    # Build entry with all language columns
                    entry = {
                        "row_index": row_idx + 2,  # +2 for 1-based + header row
                        "matched_value": val,
                        "matched_column": (
                            headers[col_idx] if col_idx < len(headers) else f"col_{col_idx}"
                        ),
                        "matched_column_lang": _find_lang_for_col(col_map, col_idx),
                        "translations": {},
                    }
                    for lang, col_idx2 in col_map.items():
                        entry["translations"][lang] = safe_get(row, col_idx2)

                    # Also include non-language columns
                    for i, h in enumerate(headers):
                        if i not in col_map.values() and i < len(row):
                            entry.setdefault("extra", {})[h] = row[i]

                    # Check for missing translations
                    missing = []
                    for lang in lang_codes:
                        if lang in col_map:
                            val2 = safe_get(row, col_map[lang])
                            if not val2:
                                missing.append(lang.upper())
                    if missing:
                        entry["missing_translations"] = missing

                    matches.append(entry)

        if not matches:
            results.append(
                {"search_term": term, "found": False, "message": f'No match found for "{term}"'}
            )
        else:
            # Deduplicate matches by row index
            seen_rows = set()
            unique_matches = []
            for m in matches:
                if m["row_index"] not in seen_rows:
                    seen_rows.add(m["row_index"])
                    unique_matches.append(m)

            results.append(
                {
                    "search_term": term,
                    "found": True,
                    "match_count": len(unique_matches),
                    "matches": unique_matches,
                }
            )

    return {
        "headers": headers,
        "column_map": {k: v for k, v in col_map.items()},
        "column_map_readable": {
            k: headers[v] if v < len(headers) else f"col_{v}" for k, v in col_map.items()
        },
        "requested_langs": lang_codes,
        "results": results,
    }


def scan_text(text, lang_codes=None):
    """Scan text for any glossary terms that appear in it."""
    headers, rows = load_glossary()
    if headers is None:
        return {
            "error": "Glossary cache not found. Run fetch_glossary.py first.",
            "cache_file": CACHE_FILE,
        }

    col_map = detect_columns(headers)
    if lang_codes is None:
        lang_codes = ALL_LANGS

    text_lower = text.lower()
    # Columns to check (all language columns)
    check_cols = set(col_map.values())

    # Collect all unique terms from the glossary
    # Key: (term, col_lang, row_idx) -> row data
    found_terms = []

    for row_idx, row in enumerate(rows):
        matched_terms_in_row = []
        for col_idx in check_cols:
            val = safe_get(row, col_idx)
            if not val or len(val) < 2:
                continue
            # Check if this glossary term appears in the text
            # Use word boundary matching for ASCII terms to avoid false positives
            # (e.g., "NTE" matching "encountered", "encounter" matching "encountered")
            is_ascii = val.isascii()
            if is_ascii:
                pattern = r"\b" + re.escape(val) + r"\b"
                if re.search(pattern, text, re.IGNORECASE):
                    matched_terms_in_row.append(
                        {
                            "term": val,
                            "column": headers[col_idx] if col_idx < len(headers) else f"col_{col_idx}",
                            "column_lang": _find_lang_for_col(col_map, col_idx),
                        }
                    )
            else:
                # CJK terms: substring match (no word boundaries in CJK)
                if val in text or val.lower() in text_lower:
                    matched_terms_in_row.append(
                        {
                            "term": val,
                            "column": headers[col_idx] if col_idx < len(headers) else f"col_{col_idx}",
                            "column_lang": _find_lang_for_col(col_map, col_idx),
                        }
                    )

        if matched_terms_in_row:
            entry = {
                "row_index": row_idx + 2,
                "matched_terms": matched_terms_in_row,
                "translations": {},
            }
            for lang, col_idx2 in col_map.items():
                entry["translations"][lang] = safe_get(row, col_idx2)

            # Also include non-language columns
            for i, h in enumerate(headers):
                if i not in col_map.values() and i < len(row):
                    entry.setdefault("extra", {})[h] = row[i]

            # Check for missing translations
            missing = []
            for lang in lang_codes:
                if lang in col_map:
                    val = safe_get(row, col_map[lang])
                    if not val:
                        missing.append(lang.upper())
            if missing:
                entry["missing_translations"] = missing

            found_terms.append(entry)

    return {
        "headers": headers,
        "column_map": {k: v for k, v in col_map.items()},
        "column_map_readable": {
            k: headers[v] if v < len(headers) else f"col_{v}" for k, v in col_map.items()
        },
        "requested_langs": lang_codes,
        "total_matches": len(found_terms),
        "results": found_terms,
    }


def show_info():
    """Display glossary structure information."""
    headers, rows = load_glossary()
    if headers is None:
        return {
            "error": "Glossary cache not found. Run fetch_glossary.py first.",
            "cache_file": CACHE_FILE,
        }

    col_map = detect_columns(headers)

    return {
        "cache_file": CACHE_FILE,
        "headers": headers,
        "header_count": len(headers),
        "row_count": len(rows),
        "column_map": col_map,
        "column_map_readable": {
            k: headers[v] if v < len(headers) else f"col_{v}" for k, v in col_map.items()
        },
        "unmapped_headers": [
            h for i, h in enumerate(headers) if i not in col_map.values()
        ],
    }


def _find_lang_for_col(col_map, col_idx):
    """Find the language code for a given column index."""
    for lang, idx in col_map.items():
        if idx == col_idx:
            return lang
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Search the cached glossary for terms.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Search subcommand
    search_parser = subparsers.add_parser("search", help="Search for specific terms")
    search_parser.add_argument("terms", nargs="+", help="Terms to search for")
    search_parser.add_argument(
        "--lang", default=None, help="Comma-separated language codes (e.g., DE,FR,ES,RU)"
    )

    # Scan subcommand
    scan_parser = subparsers.add_parser("scan", help="Scan text for glossary terms")
    scan_parser.add_argument("text", help="Text to scan")
    scan_parser.add_argument(
        "--lang", default=None, help="Comma-separated language codes (e.g., DE,FR,ES,RU)"
    )

    # Info subcommand
    subparsers.add_parser("info", help="Show glossary structure information")

    # Headers subcommand
    subparsers.add_parser("headers", help="Show column headers only")

    args = parser.parse_args()

    if args.command == "search":
        lang_codes = parse_lang_arg(args.lang) if args.lang else None
        result = search_terms(args.terms, lang_codes)
    elif args.command == "scan":
        lang_codes = parse_lang_arg(args.lang) if args.lang else None
        result = scan_text(args.text, lang_codes)
    elif args.command == "info":
        result = show_info()
    elif args.command == "headers":
        headers, _ = load_glossary()
        if headers is None:
            result = {"error": "Glossary cache not found."}
        else:
            col_map = detect_columns(headers)
            result = {
                "headers": headers,
                "column_map": col_map,
                "column_map_readable": {
                    k: headers[v] if v < len(headers) else f"col_{v}"
                    for k, v in col_map.items()
                },
            }
    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
