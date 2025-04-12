"""Generate a custom iCal file for US holidays.

This module provides functionality to create an iCal (.ics) file containing US federal holidays and
additional holidays like Halloween and Festivus. It includes a CLI for generating the calendar,
adding/removing holidays, and supports features like recurring events.
"""

import json
import logging
import pickle
import os
import sys
from typing import Dict, List, Tuple, Any
from datetime import datetime, date as datetime_date, timedelta
from icalendar import Calendar, Event, Alarm
import click

# Ensure Python version is 3.13 or higher
if sys.version_info < (3, 13):
    print("This script requires Python 3.13 or higher.")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# Load configuration
def load_config() -> Dict[str, Any]:
    """Load configuration from config/config.json."""
    try:
        with open("config/config.json", "r") as f:
            config: Dict[str, Any] = json.load(f)
            return config
    except FileNotFoundError:
        logger.error("config/config.json not found")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error("config/config.json is malformed")
        sys.exit(1)


CONFIG = load_config()
OUTPUT_FILE: str = CONFIG["output_file"]
CACHE_FILE: str = CONFIG["cache_file"]
DEFAULT_YEAR_RANGE: int = CONFIG["default_year_range"]


def load_holidays(holidays_file: str = "src/holidays.json") -> Dict[str, Any]:
    """Load holiday definitions from the specified file."""
    try:
        with open(holidays_file, "r") as f:
            holidays: Dict[str, Any] = json.load(f)
            return holidays
    except FileNotFoundError:
        logger.error(f"{holidays_file} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"{holidays_file} is malformed")
        sys.exit(1)


def load_cache() -> Dict[str, str]:
    """Load cached holiday dates from a pickle file."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "rb") as f:
                cache: Dict[str, str] = pickle.load(f)
                return cache
        except (pickle.PickleError, EOFError) as e:
            logger.warning(f"Failed to load cache: {e}. Starting with empty cache.")
    return {}


def save_cache(cache: Dict[str, str]) -> None:
    """Save calculated holiday dates to a pickle file."""
    try:
        with open(CACHE_FILE, "wb") as f:
            pickle.dump(cache, f)
    except IOError as e:
        logger.error(f"Failed to save cache: {e}")


def get_easter_sunday(year: int, cache: Dict[str, str]) -> datetime_date:
    """Calculate the date of Easter Sunday for a given year."""
    cache_key = f"easter_{year}"
    if cache_key in cache:
        return datetime.strptime(cache[cache_key], "%Y-%m-%d").date()

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
    date = datetime(year, month, day).date()
    cache[cache_key] = date.strftime("%Y-%m-%d")
    return date


def get_nth_weekday(
    year: int, month: int, weekday: int, nth: int, cache: Dict[str, str]
) -> datetime_date:
    """Calculate the nth weekday of a month (e.g., 3rd Monday in January)."""
    cache_key = f"nth_{year}_{month}_{weekday}_{nth}"
    if cache_key in cache:
        return datetime.strptime(cache[cache_key], "%Y-%m-%d").date()

    first_day = datetime(year, month, 1).date()
    first_weekday = first_day + timedelta(days=(weekday - first_day.weekday() + 7) % 7)
    date = first_weekday + timedelta(weeks=nth - 1)
    cache[cache_key] = date.strftime("%Y-%m-%d")
    return date


def get_last_weekday(year: int, month: int, weekday: int, cache: Dict[str, str]) -> datetime_date:
    """Calculate the last weekday of a month (e.g., last Monday in May)."""
    cache_key = f"last_{year}_{month}_{weekday}"
    if cache_key in cache:
        return datetime.strptime(cache[cache_key], "%Y-%m-%d").date()

    next_month = month % 12 + 1
    next_year = year if next_month != 1 else year + 1
    last_day = datetime(next_year, next_month, 1).date() - timedelta(days=1)
    days_to_subtract = (last_day.weekday() - weekday + 7) % 7
    date = last_day - timedelta(days=days_to_subtract)
    cache[cache_key] = date.strftime("%Y-%m-%d")
    return date


def get_federal_holidays(year: int, federal_holidays: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Calculate federal holidays for a given year."""
    holidays = []
    cache = load_cache()
    for holiday in federal_holidays:
        if "day" in holiday:
            date = datetime(year, holiday["month"], holiday["day"]).date()
        elif "last" in holiday:
            date = get_last_weekday(year, holiday["month"], holiday["weekday"], cache)
        else:
            date = get_nth_weekday(
                year, holiday["month"], holiday["weekday"], holiday["nth"], cache
            )
        holidays.append({"name": holiday["name"], "date": date.strftime("%Y-%m-%d")})
    return holidays


def generate_calendar(
    start_year: int,
    end_year: int,
    dry_run: bool = False,
    verbose: bool = False,
    holidays_file: str = "src/holidays.json",
) -> None:
    """Generate an iCal file with holidays for the specified year range."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if start_year > end_year or start_year < 1900 or end_year > 2100:
        logger.error(
            f"Invalid year range: {start_year} to {end_year}. Must be 1900-2100 and start <= end."
        )
        sys.exit(1)

    holiday_config = load_holidays(holidays_file)
    APPROVED_HOLIDAYS = holiday_config["approved_holidays"]
    MANUAL_HOLIDAYS = holiday_config["manual_holidays"]
    CALCULATED_HOLIDAYS = holiday_config["calculated_holidays"]
    FEDERAL_HOLIDAYS = holiday_config["federal_holidays"]

    cache = load_cache()
    logger.debug(f"Loaded cache with {len(cache)} entries")

    holidays: List[Dict[str, Any]] = []
    seen: set[Tuple[str, str]] = set()
    logger.info(f"Generating holidays for years {start_year} to {end_year}")
    for YEAR in range(start_year, end_year + 1):
        logger.debug(f"Processing year {YEAR}")
        year_holidays = get_federal_holidays(YEAR, FEDERAL_HOLIDAYS)
        logger.debug(f"Calculated {len(year_holidays)} federal holidays for {YEAR}")

        calculated_holidays_with_year = []
        for holiday in CALCULATED_HOLIDAYS:
            if holiday["type"] == "easter":
                date = get_easter_sunday(YEAR, cache)
            elif holiday["type"] == "nth_weekday":
                date = get_nth_weekday(
                    YEAR, holiday["month"], holiday["weekday"], holiday["nth"], cache
                )
            holiday_data = {"name": holiday["name"], "date": date.strftime("%Y-%m-%d")}
            if "description" in holiday:
                holiday_data["description"] = holiday["description"]
            if "reminder_days" in holiday:
                holiday_data["reminder_days"] = holiday["reminder_days"]
            calculated_holidays_with_year.append(holiday_data)
            logger.debug(f"Calculated {holiday['name']} for {YEAR}: {date}")

        manual_holidays_with_year = []
        for holiday in MANUAL_HOLIDAYS:
            date_str = f"{YEAR}-{holiday['month']:02d}-{holiday['day']:02d}"
            holiday_data = {"name": holiday["name"], "date": date_str}
            if "description" in holiday:
                holiday_data["description"] = holiday["description"]
            if "reminder_days" in holiday:
                holiday_data["reminder_days"] = holiday["reminder_days"]
            manual_holidays_with_year.append(holiday_data)
            logger.debug(f"Added manual holiday {holiday['name']} for {YEAR}: {date_str}")

        year_holidays.extend(manual_holidays_with_year)
        year_holidays.extend(calculated_holidays_with_year)
        holidays.extend(year_holidays)

    save_cache(cache)
    logger.debug(f"Saved cache with {len(cache)} entries")

    cal = Calendar()
    cal.add("prodid", "//US Holidays Calendar//github.com/aaronshivers//")
    cal.add("version", "2.0")
    cal.add("refresh-interval", {"value": "P1M"})

    fixed_holidays = ["New Year's Day", "Independence Day", "Christmas Day"]
    for holiday in holidays:
        holiday_name = holiday["name"]
        holiday_date = holiday["date"]

        try:
            dtstart = datetime.strptime(holiday_date, "%Y-%m-%d").date()
        except ValueError as e:
            logger.error(f"Invalid date format for {holiday_name}: {holiday_date}. Error: {e}")
            continue

        holiday_key = (holiday_name, holiday_date)
        if holiday_key in seen:
            logger.warning(f"Skipping duplicate: {holiday_name} on {holiday_date}")
            continue
        seen.add(holiday_key)

        if holiday_name in APPROVED_HOLIDAYS:
            event = Event()
            event.add("summary", holiday_name)
            event.add("dtstart", dtstart)
            event.add("uid", f"{holiday_date}-{holiday_name}@mycalendar")
            if "description" in holiday:
                event.add("description", holiday["description"])
            if "reminder_days" in holiday:
                alarm = Alarm()
                alarm.add("trigger", timedelta(days=-holiday["reminder_days"]))
                alarm.add("action", "DISPLAY")
                alarm.add("description", f"Reminder: {holiday_name} is tomorrow")
                event.add_component(alarm)
            if holiday_name in fixed_holidays and "reminder_days" not in holiday:
                event.add("rrule", {"freq": "yearly"})
            cal.add_component(event)
            logger.info(f"Added: {holiday_name} on {holiday_date}")

    if dry_run:
        logger.info("Dry run complete, iCal file not written.")
        return

    try:
        with open(OUTPUT_FILE, "wb") as f:
            f.write(cal.to_ical())
        logger.info(f"Calendar saved as '{OUTPUT_FILE}'")
    except IOError as e:
        logger.error(f"Failed to save iCal file: {e}")
        sys.exit(1)


@click.group()  # type: ignore[misc]
def cli() -> None:
    """CLI for generating calendars and managing holidays."""
    pass


@cli.command()  # type: ignore[misc]
@click.option(
    "--year", type=int, default=datetime.now().year, help="Start year for the calendar"
)  # type: ignore[misc]
@click.option(
    "--end-year",
    type=int,
    default=None,
    help="End year for the calendar (default: start_year + range - 1)",
)  # type: ignore[misc]
@click.option(
    "--dry-run", is_flag=True, help="Preview without writing the iCal file"
)  # type: ignore[misc]
@click.option("--verbose", is_flag=True, help="Enable verbose logging")  # type: ignore[misc]
@click.option(
    "--holidays-file", default="src/holidays.json", help="Path to holidays JSON file"
)  # type: ignore[misc]
def generate(
    year: int, end_year: int | None, dry_run: bool, verbose: bool, holidays_file: str
) -> None:
    """Generate a custom US holidays iCal file."""
    effective_end_year = end_year if end_year is not None else year + DEFAULT_YEAR_RANGE - 1
    generate_calendar(year, effective_end_year, dry_run, verbose, holidays_file)


@cli.command()  # type: ignore[misc]
@click.argument("name")  # type: ignore[misc]
@click.argument("month", type=int)  # type: ignore[misc]
@click.argument("day", type=int)  # type: ignore[misc]
@click.option(
    "--holidays-file", default="src/holidays.json", help="Path to holidays JSON file"
)  # type: ignore[misc]
def add_holiday(name: str, month: int, day: int, holidays_file: str) -> None:
    """Add a new manual holiday to holidays.json."""
    if not (1 <= month <= 12):
        logger.error(f"Invalid month: {month}. Must be between 1 and 12.")
        sys.exit(1)
    try:
        # Use a leap year like 2024 to validate Feb 29
        datetime(2024, month, day)
    except ValueError as e:
        logger.error(f"Invalid date: {month:02d}-{day:02d}. {str(e)}")
        sys.exit(1)

    holiday_config = load_holidays(holidays_file)
    # Check if holiday already exists
    for holiday_list_key in ["manual_holidays", "calculated_holidays", "federal_holidays"]:
        if any(h["name"] == name for h in holiday_config.get(holiday_list_key, [])):
            logger.error(f"Holiday '{name}' already exists.")
            sys.exit(1)

    new_holiday = {"name": name, "month": month, "day": day}
    holiday_config["manual_holidays"].append(new_holiday)
    # Also add to approved list if not already there
    if name not in holiday_config["approved_holidays"]:
        holiday_config["approved_holidays"].append(name)
    with open(holidays_file, "w") as f:
        json.dump(holiday_config, f, indent=2)  # Use indent=2 for consistency
    logger.info(f"Added holiday: {name} on {month:02d}-{day:02d}")


@cli.command()  # type: ignore[misc]
@click.argument("name")  # type: ignore[misc]
@click.option(
    "--holidays-file", default="src/holidays.json", help="Path to holidays JSON file"
)  # type: ignore[misc]
def remove_holiday(name: str, holidays_file: str) -> None:
    """Remove a holiday from holidays.json."""
    holiday_config = load_holidays(holidays_file)
    initial_length = len(holiday_config["approved_holidays"])
    holiday_config["manual_holidays"] = [
        h for h in holiday_config["manual_holidays"] if h["name"] != name
    ]
    holiday_config["calculated_holidays"] = [
        h for h in holiday_config["calculated_holidays"] if h["name"] != name
    ]
    holiday_config["federal_holidays"] = [
        h for h in holiday_config["federal_holidays"] if h["name"] != name
    ]
    holiday_config["approved_holidays"] = [
        h for h in holiday_config["approved_holidays"] if h != name
    ]

    if len(holiday_config["approved_holidays"]) == initial_length:
        logger.warning(f"Holiday '{name}' not found in any list.")
        # Optionally exit if holiday not found, or just log warning
        # sys.exit(1) # Uncomment to exit if holiday not found

    with open(holidays_file, "w") as f:
        json.dump(holiday_config, f, indent=2)  # Use indent=2 for consistency
    logger.info(f"Removed holiday: {name} (if it existed)")


if __name__ == "__main__":
    cli()
