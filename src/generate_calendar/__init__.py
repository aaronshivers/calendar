from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import date as calendar_date
from datetime import datetime, timedelta
from importlib import resources
from pathlib import Path
from typing import Any, cast

import click
import yaml
from icalendar import Calendar, Event

if sys.version_info < (3, 13):
    raise SystemExit("This script requires Python 3.13 or higher.")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_FILE = Path("us_holidays.ics")
DEFAULT_YEAR_COUNT = 10
MUTATION_COMMANDS = {"add-holiday", "remove-holiday"}
OBSERVED_HOLIDAYS = {
    "New Year's Day",
    "Independence Day",
    "Veterans Day",
    "Christmas Day",
}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return cast(dict[str, Any], yaml.safe_load(path.read_text(encoding="utf-8")))
    except FileNotFoundError as exc:
        raise SystemExit(f"{path} not found") from exc
    except yaml.YAMLError as exc:
        raise SystemExit(f"{path} is malformed") from exc


def _bundled_holidays() -> dict[str, Any]:
    try:
        raw_yaml = (
            resources.files("generate_calendar")
            .joinpath("holidays.yaml")
            .read_text(encoding="utf-8")
        )
    except FileNotFoundError as exc:
        raise SystemExit("Bundled holidays.yaml not found") from exc

    try:
        return cast(dict[str, Any], yaml.safe_load(raw_yaml))
    except yaml.YAMLError as exc:
        raise SystemExit("Bundled holidays.yaml is malformed") from exc


def load_holidays(holidays_file: Path | str | None = None) -> dict[str, Any]:
    holiday_config = (
        _bundled_holidays() if holidays_file is None else _read_json(Path(holidays_file))
    )
    validate_holiday_definitions(holiday_config)
    return holiday_config


def validate_holiday_definitions(holiday_config: dict[str, Any]) -> None:
    required_sections = ("manual_holidays", "calculated_holidays", "federal_holidays")
    missing_sections = [section for section in required_sections if section not in holiday_config]
    if missing_sections:
        missing = ", ".join(sorted(missing_sections))
        raise ValueError(f"Holiday config is missing required sections: {missing}")

    seen_names: set[str] = set()
    duplicate_names: set[str] = set()
    for section in required_sections:
        for holiday in holiday_config[section]:
            holiday_name = holiday["name"]
            if holiday_name in seen_names:
                duplicate_names.add(holiday_name)
            seen_names.add(holiday_name)

    if duplicate_names:
        duplicates = ", ".join(sorted(duplicate_names))
        raise ValueError(f"Holiday names must be unique across all sections: {duplicates}")

    for holiday in holiday_config["manual_holidays"]:
        try:
            datetime(2024, holiday["month"], holiday["day"])
        except ValueError as exc:
            raise ValueError(f"Manual holiday has an invalid date: {holiday['name']}") from exc

    allowed_calculated_types = {"easter", "nth_weekday"}
    invalid_types = sorted(
        {
            holiday["type"]
            for holiday in holiday_config["calculated_holidays"]
            if holiday["type"] not in allowed_calculated_types
        }
    )
    if invalid_types:
        invalid = ", ".join(invalid_types)
        raise ValueError(f"Unsupported calculated holiday types: {invalid}")


def save_holidays(holiday_config: dict[str, Any], holidays_file: Path) -> None:
    validate_holiday_definitions(holiday_config)
    holidays_file.write_text(
        yaml.safe_dump(holiday_config, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def get_easter_sunday(year: int) -> calendar_date:
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    offset_l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * offset_l) // 451
    month = (h + offset_l - 7 * m + 114) // 31
    day = ((h + offset_l - 7 * m + 114) % 31) + 1
    return datetime(year, month, day).date()


def get_nth_weekday(year: int, month: int, weekday: int, nth: int) -> calendar_date:
    first_day = datetime(year, month, 1).date()
    first_weekday = first_day + timedelta(days=(weekday - first_day.weekday() + 7) % 7)
    return first_weekday + timedelta(weeks=nth - 1)


def get_last_weekday(year: int, month: int, weekday: int) -> calendar_date:
    next_month = month % 12 + 1
    next_year = year if next_month != 1 else year + 1
    last_day = datetime(next_year, next_month, 1).date() - timedelta(days=1)
    days_to_subtract = (last_day.weekday() - weekday + 7) % 7
    return last_day - timedelta(days=days_to_subtract)


def adjust_for_observance(holiday_date: calendar_date) -> calendar_date:
    if holiday_date.weekday() == 5:
        return holiday_date - timedelta(days=1)
    if holiday_date.weekday() == 6:
        return holiday_date + timedelta(days=1)
    return holiday_date


def get_federal_holidays(
    year: int, federal_holidays: list[dict[str, Any]]
) -> list[dict[str, calendar_date]]:
    holidays: list[dict[str, calendar_date]] = []
    for holiday in federal_holidays:
        if "day" in holiday:
            holiday_date = datetime(year, holiday["month"], holiday["day"]).date()
        elif "last" in holiday:
            holiday_date = get_last_weekday(year, holiday["month"], holiday["weekday"])
        else:
            holiday_date = get_nth_weekday(
                year, holiday["month"], holiday["weekday"], holiday["nth"]
            )
        holidays.append({"name": holiday["name"], "date": holiday_date})
    return holidays


def calculate_default_end_year(start_year: int) -> int:
    return start_year + DEFAULT_YEAR_COUNT - 1


def build_holiday_entries(
    start_year: int, end_year: int, holidays_file: Path | str | None = None
) -> list[dict[str, calendar_date]]:
    if end_year < start_year:
        raise ValueError("end_year must be greater than or equal to start_year")

    holiday_config = load_holidays(holidays_file)
    holidays: list[dict[str, calendar_date]] = []
    seen: set[tuple[str, calendar_date]] = set()

    for year in range(start_year, end_year + 1):
        year_holidays = get_federal_holidays(year, holiday_config["federal_holidays"])

        for holiday in holiday_config["manual_holidays"]:
            year_holidays.append(
                {
                    "name": holiday["name"],
                    "date": datetime(year, holiday["month"], holiday["day"]).date(),
                }
            )

        for holiday in holiday_config["calculated_holidays"]:
            if holiday["type"] == "easter":
                holiday_date = get_easter_sunday(year)
            else:
                holiday_date = get_nth_weekday(
                    year, holiday["month"], holiday["weekday"], holiday["nth"]
                )
            year_holidays.append({"name": holiday["name"], "date": holiday_date})

        for holiday in year_holidays:
            holiday_date = holiday["date"]
            if holiday["name"] in OBSERVED_HOLIDAYS:
                holiday_date = adjust_for_observance(holiday_date)

            holiday_key = (holiday["name"], holiday_date)
            if holiday_key in seen:
                logger.warning("Skipping duplicate holiday definition for %s on %s", *holiday_key)
                continue

            seen.add(holiday_key)
            holidays.append({"name": holiday["name"], "date": holiday_date})

    return holidays


def build_calendar(
    start_year: int, end_year: int, holidays_file: Path | str | None = None
) -> Calendar:
    cal = Calendar()
    cal.add("prodid", "//US Holidays Calendar//github.com/aaronshivers//")
    cal.add("version", "2.0")

    logger.info("Generating holidays for years %s to %s", start_year, end_year)
    for holiday in build_holiday_entries(start_year, end_year, holidays_file=holidays_file):
        event = Event()
        event.add("summary", holiday["name"])
        event.add("dtstart", holiday["date"])
        event.add("uid", f"{holiday['date'].isoformat()}-{holiday['name']}@us-holidays-calendar")
        cal.add_component(event)
        logger.info("Added: %s on %s", holiday["name"], holiday["date"].isoformat())

    return cal


def generate_calendar(
    start_year: int,
    end_year: int,
    dry_run: bool = False,
    verbose: bool = False,
    output_file: Path | str = DEFAULT_OUTPUT_FILE,
    holidays_file: Path | str | None = None,
) -> Path | None:
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    cal = build_calendar(start_year, end_year, holidays_file=holidays_file)
    if dry_run:
        logger.info("Dry run complete, iCal file not written.")
        return None

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(cal.to_ical())
    logger.info("Calendar saved as '%s'", output_path)
    return output_path


def resolve_mutable_holidays_file(holidays_file: Path | None) -> Path:
    if holidays_file is not None:
        return holidays_file

    default_path = Path(__file__).with_name("holidays.yaml")
    if default_path.exists() and os.access(default_path, os.W_OK):
        return default_path

    raise click.ClickException(
        "Holiday updates require --holidays-file when the bundled holidays file is read-only."
    )


@click.group()
def cli() -> None:
    """CLI for managing holidays in holidays.yaml."""


@cli.command()
@click.option("--holidays-file", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.argument("name")
@click.argument("month", type=int)
@click.argument("day", type=int)
def add_holiday(holidays_file: Path | None, name: str, month: int, day: int) -> None:
    """Add a new manual holiday to a holidays.yaml file."""
    if not (1 <= month <= 12):
        raise click.ClickException(f"Invalid month: {month}. Must be between 1 and 12.")

    try:
        datetime(2024, month, day)
    except ValueError as exc:
        raise click.ClickException(f"Invalid date: {month:02d}-{day:02d}. {exc}") from exc

    target_file = resolve_mutable_holidays_file(holidays_file)
    holiday_config = load_holidays(target_file)
    existing_names = {
        holiday["name"]
        for section in ("manual_holidays", "calculated_holidays", "federal_holidays")
        for holiday in holiday_config[section]
    }
    if name in existing_names:
        raise click.ClickException(f"Holiday '{name}' already exists.")

    holiday_config["manual_holidays"].append({"name": name, "month": month, "day": day})
    holiday_config["manual_holidays"].sort(
        key=lambda holiday: (holiday["month"], holiday["day"], holiday["name"])
    )
    save_holidays(holiday_config, target_file)
    click.echo(f"Added holiday: {name} on {month:02d}-{day:02d}")


@cli.command()
@click.option("--holidays-file", type=click.Path(path_type=Path, dir_okay=False), default=None)
@click.argument("name")
def remove_holiday(holidays_file: Path | None, name: str) -> None:
    """Remove a holiday from a holidays.yaml file."""
    target_file = resolve_mutable_holidays_file(holidays_file)
    holiday_config = load_holidays(target_file)

    removed = False
    for section in ("manual_holidays", "calculated_holidays", "federal_holidays"):
        original_count = len(holiday_config[section])
        holiday_config[section] = [
            holiday for holiday in holiday_config[section] if holiday["name"] != name
        ]
        removed = removed or len(holiday_config[section]) != original_count

    if not removed:
        raise click.ClickException(f"Holiday '{name}' was not found.")

    save_holidays(holiday_config, target_file)
    click.echo(f"Removed holiday: {name}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a static US holidays iCal file.")
    parser.add_argument(
        "--year",
        type=int,
        default=datetime.now().year,
        help="Start year for the calendar (default: current year)",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=None,
        help=f"End year for the calendar (default: {DEFAULT_YEAR_COUNT} calendar years total)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Build the calendar without writing a file"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help=f"Output iCal file path (default: {DEFAULT_OUTPUT_FILE})",
    )
    parser.add_argument(
        "--holidays-file",
        type=Path,
        default=None,
        help="Optional path to an alternate holidays.yaml file",
    )
    return parser


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] in MUTATION_COMMANDS:
        cli()
        return

    parser = build_parser()
    args = parser.parse_args()
    end_year = args.end_year if args.end_year is not None else calculate_default_end_year(args.year)
    generate_calendar(
        start_year=args.year,
        end_year=end_year,
        dry_run=args.dry_run,
        verbose=args.verbose,
        output_file=args.output,
        holidays_file=args.holidays_file,
    )


__all__ = [
    "DEFAULT_OUTPUT_FILE",
    "DEFAULT_YEAR_COUNT",
    "add_holiday",
    "adjust_for_observance",
    "build_calendar",
    "build_holiday_entries",
    "calculate_default_end_year",
    "cli",
    "generate_calendar",
    "get_easter_sunday",
    "get_federal_holidays",
    "get_last_weekday",
    "get_nth_weekday",
    "load_holidays",
    "main",
    "remove_holiday",
    "validate_holiday_definitions",
]
