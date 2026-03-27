from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from generate_calendar import DEFAULT_YEAR_COUNT, build_calendar

ROOT = Path(__file__).resolve().parents[2]
WRANGLER_PATH = ROOT / "wrangler.toml"
OUTPUT_DIR = ROOT / "cloudflare" / "generated"
CALENDAR_PATH = OUTPUT_DIR / "us_holidays.ics"
GENERATED_AT_PATH = OUTPUT_DIR / "generated_at.txt"


def read_year_count() -> int:
    wrangler_text = WRANGLER_PATH.read_text(encoding="utf-8")
    match = re.search(r'^YEAR_COUNT = "(\d+)"$', wrangler_text, re.MULTILINE)
    if match is None:
        return DEFAULT_YEAR_COUNT
    return max(1, int(match.group(1)))


def main() -> None:
    year_count = read_year_count()
    now = datetime.now(timezone.utc)
    start_year = now.year
    end_year = start_year + year_count - 1
    calendar_text = build_calendar(start_year, end_year).to_ical().decode("utf-8")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CALENDAR_PATH.write_text(calendar_text, encoding="utf-8")
    GENERATED_AT_PATH.write_text(now.isoformat(), encoding="utf-8")


if __name__ == "__main__":
    main()
