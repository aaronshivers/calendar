import json
import logging
import pickle
import os
import sys
from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta, date as datetime_date
from icalendar import Calendar, Event
import argparse
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
    """Load configuration from config.json."""
    try:
        with open("config/config.json", "r") as f:
            return json.load(f)
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


def load_holidays() -> Dict[str, Any]:
    """Load holiday definitions from holidays.json."""
    try:
        with open("src/holidays.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("src/holidays.json not found")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error("src/holidays.json is malformed")
        sys.exit(1)


def load_cache() -> Dict[str, str]:
    """Load cached holiday dates from a pickle file."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            return pickle.load(f)
    return {}


def save_cache(cache: Dict[str, str]) -> None:
    """Save calculated holiday dates to a pickle file."""
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(cache, f)


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


def get_nth_weekday(year: int, month: int, weekday: int, nth: int) -> datetime_date:
    """Calculate the nth weekday of a month (e.g., 3rd Monday in January)."""
    first_day = datetime(year, month, 1).date()
    first_weekday = first_day + timedelta(days=(weekday - first_day.weekday() + 7) % 7)
    return first_weekday + timedelta(weeks=nth - 1)


def get_last_weekday(year: int, month: int, weekday: int) -> datetime_date:
    """Calculate the last weekday of a month (e.g., last Monday in May)."""
    next_month = month % 12 + 1
    next_year = year if next_month != 1 else year + 1
    last_day = (datetime(next_year, next_month, 1).date() - timedelta(days=1))
    days_to_subtract = (last_day.weekday() - weekday + 7) % 7
    return last_day - timedelta(days=days_to_subtract)


def adjust_for_observance(holiday_date: str, holiday_name: str) -> str:
    """Adjust holiday date for observance (e.g., if on Saturday, observe on Friday)."""
    date = datetime.strptime(holiday_date, "%Y-%m-%d").date()
    if date.weekday() == 5:  # Saturday
        return (date - timedelta(days=1)).strftime("%Y-%m-%d")
    elif date.weekday() == 6:  # Sunday
        return (date + timedelta(days=1)).strftime("%Y-%m-%d")
    return holiday_date


def get_federal_holidays(year: int, federal_holidays: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Calculate federal holidays for a given year."""
    holidays = []
    for holiday in federal_holidays:
        if "day" in holiday:
            date = datetime(year, holiday["month"], holiday["day"]).date()
        elif "last" in holiday:
            date = get_last_weekday(year, holiday["month"], holiday["weekday"])
        else:
            date = get_nth_weekday(year, holiday["month"], holiday["weekday"], holiday["nth"])
        holidays.append({
            "name": holiday["name"],
            "date": date.strftime("%Y-%m-%d")
        })
    return holidays


def generate_calendar(start_year: int, end_year: int, dry_run: bool = False) -> None:
    """Generate an iCal file with holidays for the specified year range.

    Args:
        start_year: The starting year for the calendar.
        end_year: The ending year for the calendar.
        dry_run: If True, log holidays without writing the iCal file.
    """
    # Load holidays
    holiday_config = load_holidays()
    APPROVED_HOLIDAYS = holiday_config["approved_holidays"]
    MANUAL_HOLIDAYS = holiday_config["manual_holidays"]
    CALCULATED_HOLIDAYS = holiday_config["calculated_holidays"]
    FEDERAL_HOLIDAYS = holiday_config["federal_holidays"]

    # Load cache
    cache = load_cache()

    # Generate holidays for a range of years
    holidays: List[Dict[str, str]] = []
    seen: set[Tuple[str, str]] = set()  # Track (name, date) to avoid duplicates
    logger.info(f"Generating holidays for years {start_year} to {end_year}")
    for YEAR in range(start_year, end_year + 1):
        # Calculate federal holidays
        year_holidays = get_federal_holidays(YEAR, FEDERAL_HOLIDAYS)

        # Calculate variable holidays (e.g., Easter, Mother's Day)
        calculated_holidays_with_year = []
        for holiday in CALCULATED_HOLIDAYS:
            if holiday["type"] == "easter":
                date = get_easter_sunday(YEAR, cache)
            elif holiday["type"] == "nth_weekday":
                date = get_nth_weekday(YEAR, holiday["month"], holiday["weekday"], holiday["nth"])
            calculated_holidays_with_year.append({
                "name": holiday["name"],
                "date": date.strftime("%Y-%m-%d")
            })

        # Convert manual holidays to full dates for the year
        manual_holidays_with_year = []
        for holiday in MANUAL_HOLIDAYS:
            manual_holidays_with_year.append({
                "name": holiday["name"],
                "date": f"{YEAR}-{holiday['month']:02d}-{holiday['day']:02d}"
            })

        year_holidays.extend(manual_holidays_with_year)
        year_holidays.extend(calculated_holidays_with_year)
        holidays.extend(year_holidays)

    # Save cache
    save_cache(cache)

    # Create iCal calendar
    cal = Calendar()
    cal.add("prodid", "-//Aaron Shivers//calendar.aaronshivers.com//")
    cal.add("version", "2.0")

    # Filter and add holidays, avoiding duplicates
    for holiday in holidays:
        holiday_name = holiday["name"]
        holiday_date = holiday["date"]

        # Apply observance rules for specific holidays
        if holiday_name in [
            "New Year's Day",
            "Independence Day",
            "Veterans Day",
            "Christmas Day",
        ]:
            holiday_date = adjust_for_observance(holiday_date, holiday_name)

        # Skip duplicates
        holiday_key = (holiday_name, holiday_date)
        if holiday_key in seen:
            logger.warning(
                f"Skipping duplicate: {holiday_name} on {holiday_date}"
            )
            continue
        seen.add(holiday_key)

        if holiday_name in APPROVED_HOLIDAYS:
            event = Event()
            event.add("summary", holiday_name)
            event.add("dtstart", datetime.strptime(holiday_date, "%Y-%m-%d").date())
            event.add("uid", f"{holiday_date}-{holiday_name}@mycalendar")
            cal.add_component(event)
            logger.info(f"Added: {holiday_name} on {holiday_date}")

    if dry_run:
        logger.info("Dry run complete, iCal file not written.")
        return

    # Save the iCal file
    with open(OUTPUT_FILE, "wb") as f:
        f.write(cal.to_ical())
    logger.info(f"Calendar saved as '{OUTPUT_FILE}'")


@click.group()
def cli():
    """CLI for managing holidays in holidays.json."""
    pass


@cli.command()
@click.argument("name")
@click.argument("month", type=int)
@click.argument("day", type=int)
def add_holiday(name: str, month: int, day: int) -> None:
    """Add a new manual holiday to holidays.json."""
    # Validate month and day
    if not (1 <= month <= 12):
        logger.error(f"Invalid month: {month}. Must be between 1 and 12.")
        sys.exit(1)
    try:
        # Check if the date is valid for the current year
        datetime(2025, month, day)  # Use a fixed year for validation
    except ValueError as e:
        logger.error(f"Invalid date: {month:02d}-{day:02d}. {str(e)}")
        sys.exit(1)

    holiday_config = load_holidays()
    new_holiday = {"name": name, "month": month, "day": day}
    holiday_config["manual_holidays"].append(new_holiday)
    holiday_config["approved_holidays"].append(name)
    with open("src/holidays.json", "w") as f:
        json.dump(holiday_config, f, indent=2)
    logger.info(f"Added holiday: {name} on {month:02d}-{day:02d}")


@cli.command()
@click.argument("name")
def remove_holiday(name: str) -> None:
    """Remove a holiday from holidays.json."""
    holiday_config = load_holidays()
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
    with open("src/holidays.json", "w") as f:
        json.dump(holiday_config, f, indent=2)
    logger.info(f"Removed holiday: {name}")


def main() -> None:
    """Main function to generate the calendar or run CLI commands."""
    # Check if we're running a CLI command
    if len(sys.argv) > 1 and sys.argv[1] in ["add-holiday", "remove-holiday"]:
        cli()
    else:
        # Parse command-line arguments for calendar generation
        parser = argparse.ArgumentParser(
            description="Generate a custom US holidays iCal file."
        )
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
            help="End year for the calendar (default: start year + default range)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Log holidays without writing the iCal file",
        )
        args = parser.parse_args()
        start_year = args.year
        end_year = args.end_year if args.end_year else start_year + DEFAULT_YEAR_RANGE

        generate_calendar(start_year, end_year, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
