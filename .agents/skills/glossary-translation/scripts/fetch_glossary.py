#!/usr/bin/env python3
"""
fetch_glossary.py - Download and cache glossary from Google Apps Script Web App.

The Apps Script returns a JSON 2D array (rows of cells). This script downloads
the JSON, converts it to CSV, and caches it locally for the search script.

Usage:
    python fetch_glossary.py              # Use cache if fresh, otherwise download
    python fetch_glossary.py --force      # Force re-download
    python fetch_glossary.py --info       # Show cache info only
"""
import urllib.request
import urllib.error
import os
import sys
import json
import csv
import io
from datetime import datetime, timedelta

# ── Configuration ──────────────────────────────────────────────
# Google Apps Script Web App URL (deployed as "Anyone" access)
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbx-EB9Mj7slUNSeKPYBpNKIXQWqZpMN0QtJfWDFGlxajtMsN1q5T9EdMTudBbd7Iv7W/exec"

# Original Google Sheet (for reference)
SHEET_ID = "1r1IempqDsfDtzHTmUpBGf0j1HCOXk2XP9TD7UUI64EA"
GID = "1957346467"

# Cache location: skill_dir/data/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(SKILL_DIR, "data")
CACHE_FILE = os.path.join(DATA_DIR, "glossary_cache.csv")
META_FILE = os.path.join(DATA_DIR, "glossary_meta.json")

CACHE_DURATION_HOURS = 24
REQUEST_TIMEOUT = 120  # Large glossary (~38K rows, ~5MB), needs longer timeout


def is_cache_fresh():
    """Check if the cache file exists and is within the refresh window."""
    if not os.path.exists(CACHE_FILE) or not os.path.exists(META_FILE):
        return False
    try:
        with open(META_FILE, "r", encoding="utf-8") as f:
            meta = json.load(f)
        last_fetch = datetime.fromisoformat(meta["last_fetch"])
        return datetime.now() - last_fetch < timedelta(hours=CACHE_DURATION_HOURS)
    except (KeyError, ValueError, json.JSONDecodeError):
        return False


def download_glossary():
    """Download glossary data from Google Apps Script Web App."""
    os.makedirs(DATA_DIR, exist_ok=True)

    print(f"Downloading glossary from Google Apps Script...")
    print(f"URL: {WEB_APP_URL}")

    req = urllib.request.Request(
        WEB_APP_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json,text/plain,*/*",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            raw_data = response.read()
    except urllib.error.HTTPError as e:
        print(f"ERROR: HTTP {e.code} - {e.reason}", file=sys.stderr)
        if e.code == 401 or e.code == 403:
            print(
                "The Apps Script Web App is not accessible. "
                "Please re-deploy with 'Anyone' access.",
                file=sys.stderr,
            )
        return False
    except urllib.error.URLError as e:
        print(f"ERROR: URL error - {e.reason}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return False

    # Decode response
    text = raw_data.decode("utf-8", errors="replace")

    # Check for HTML error page (auth redirect)
    if text.strip().startswith("<!DOCTYPE") or text.strip().startswith("<html"):
        print(
            "ERROR: Received HTML instead of JSON. The web app may need re-authorization.\n"
            "Go to the Apps Script editor, click 'Deploy' > 'Manage deployments', "
            "and re-authorize the web app.",
            file=sys.stderr,
        )
        return False

    # Parse JSON (expected: 2D array of values)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON response: {e}", file=sys.stderr)
        print(f"First 200 chars: {text[:200]}", file=sys.stderr)
        return False

    if not isinstance(data, list) or len(data) == 0:
        print("ERROR: Empty or invalid data received.", file=sys.stderr)
        return False

    # Convert 2D array to CSV
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    for row in data:
        # Convert all values to strings, handle None
        str_row = [str(cell) if cell is not None else "" for cell in row]
        writer.writerow(str_row)

    csv_text = output.getvalue()

    # Write cache file
    with open(CACHE_FILE, "w", encoding="utf-8-sig", newline="") as f:
        f.write(csv_text)

    # Write metadata
    headers = data[0] if data else []
    meta = {
        "last_fetch": datetime.now().isoformat(),
        "encoding": "utf-8",
        "source": "google_apps_script",
        "web_app_url": WEB_APP_URL,
        "sheet_id": SHEET_ID,
        "gid": GID,
        "row_count": len(data),
        "column_count": len(headers),
        "headers": headers,
    }
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"Successfully downloaded glossary.")
    print(f"  Source: Google Apps Script")
    print(f"  Rows: {len(data)}")
    print(f"  Columns: {len(headers)}")
    print(f"  Headers: {headers}")
    print(f"  Cache file: {CACHE_FILE}")

    return True


def show_cache_info():
    """Display cache information without downloading."""
    if not os.path.exists(CACHE_FILE):
        print("No cache file found. Run with --force to download.")
        return

    if os.path.exists(META_FILE):
        with open(META_FILE, "r", encoding="utf-8") as f:
            meta = json.load(f)
        print(f"Cache info:")
        print(f"  Last fetch: {meta.get('last_fetch', 'unknown')}")
        print(f"  Source: {meta.get('source', 'unknown')}")
        print(f"  Rows: {meta.get('row_count', 'unknown')}")
        print(f"  Columns: {meta.get('column_count', 'unknown')}")
        if meta.get("headers"):
            print(f"  Headers: {meta['headers']}")

    # Also verify cache file is readable
    with open(CACHE_FILE, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            first_row = next(reader)
            print(f"  Cache file headers: {first_row}")
        except StopIteration:
            print(f"  WARNING: Cache file appears to be empty.")

    print(f"  Fresh: {'Yes' if is_cache_fresh() else 'No (needs refresh)'}")
    print(f"  Cache file: {CACHE_FILE}")


def main():
    force = "--force" in sys.argv
    info_only = "--info" in sys.argv

    if info_only:
        show_cache_info()
        return

    if not force and is_cache_fresh():
        print("Using cached glossary (fresh, less than 24 hours old).")
        show_cache_info()
        return

    success = download_glossary()
    if not success:
        # Try to use existing cache as fallback
        if os.path.exists(CACHE_FILE):
            print("\nFalling back to existing cache (may be outdated).")
            show_cache_info()
            return
        sys.exit(1)


if __name__ == "__main__":
    main()
