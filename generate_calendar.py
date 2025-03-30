import json
import logging
import pickle
import os
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Cache file for calculated dates
CACHE_FILE = "holiday_cache.pkl"


# Load holiday definitions from JSON
def load_holidays():
    try:
        with open("holidays.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("holidays.json not found")
        exit(1)
    except json.JSONDecodeError:
        logger.error("holidays.json is malformed")
        exit(1)


# Load cached dates if available
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "rb") as f:
            return pickle.load(f)
    return {}


# Save calculated dates to cache
def save_cache(cache):
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(cache, f)


# Function to calculate Easter Sunday
def get_easter_sunday(year, cache):
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
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    date = datetime(year, month, day).date()
    cache[cache_key] = date.strftime("%Y-%m-%d")
    return date


# Function to calculate nth weekday (e.g., 3rd Monday in January)
def get_nth_weekday(year, month, weekday, nth):
    first_day = datetime(year, month, 1).date()
    first_weekday = first_day + timedelta(days=(weekday - first_day.weekday() + 7) % 7)
    return first_weekday + timedelta(weeks=nth - 1)


# Function to calculate last weekday of a month (e.g., last Monday in May)
def get_last_weekday(year, month, weekday):
    # Start from the last day of the month
    next_month = month % 12 + 1
    next_year = year if next_month != 1 else year + 1
    last_day = datetime(next_year, next_month, 1).date() - timedelta(days=1)
    # Find the last occurrence of the weekday
    days_to_subtract = (last_day.weekday() - weekday + 7) % 7
    return last_day - timedelta(days=days_to_subtract)


# Adjust holiday date for observance (e.g., if on Saturday, observe on Friday; if on Sunday, observe on Monday)
def adjust_for_observance(holiday_date, holiday_name):
    date = datetime.strptime(holiday_date, "%Y-%m-%d").date()
    if date.weekday() == 5:  # Saturday
        return (date - timedelta(days=1)).strftime("%Y-%m-%d")
    elif date.weekday() == 6:  # Sunday
        return (date + timedelta(days=1)).strftime("%Y-%m-%d")
    return holiday_date


# Calculate federal holidays
def get_federal_holidays(year, federal_holidays):
    holidays = []
    for holiday in federal_holidays:
        if "day" in holiday:
            date = datetime(year, holiday["month"], holiday["day"]).date()
        elif "last" in holiday:
            date = get_last_weekday(year, holiday["month"], holiday["weekday"])
        else:
            date = get_nth_weekday(
                year, holiday["month"], holiday["weekday"], holiday["nth"]
            )
        holidays.append({"name": holiday["name"], "date": date.strftime("%Y-%m-%d")})
    return holidays


def generate_calendar(start_year, end_year):
    # Load holidays
    holiday_config = load_holidays()
    APPROVED_HOLIDAYS = holiday_config["approved_holidays"]
    MANUAL_HOLIDAYS = holiday_config["manual_holidays"]
    CALCULATED_HOLIDAYS = holiday_config["calculated_holidays"]
    FEDERAL_HOLIDAYS = holiday_config["federal_holidays"]

    # Load cache
    cache = load_cache()

    # Generate holidays for a range of years
    holidays = []
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
                date = get_nth_weekday(
                    YEAR, holiday["month"], holiday["weekday"], holiday["nth"]
                )
            calculated_holidays_with_year.append(
                {"name": holiday["name"], "date": date.strftime("%Y-%m-%d")}
            )

        # Convert manual holidays to full dates for the year
        manual_holidays_with_year = []
        for holiday in MANUAL_HOLIDAYS:
            manual_holidays_with_year.append(
                {
                    "name": holiday["name"],
                    "date": f"{YEAR}-{holiday['month']:02d}-{holiday['day']:02d}",
                }
            )

        year_holidays.extend(manual_holidays_with_year)
        year_holidays.extend(calculated_holidays_with_year)
        holidays.extend(year_holidays)

    # Save cache
    save_cache(cache)

    # Create iCal calendar
    cal = Calendar()
    cal.add("prodid", "-//My Custom US Holidays//jetify.dev//")
    cal.add("version", "2.0")

    # Filter and add holidays
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

        if holiday_name in APPROVED_HOLIDAYS:
            event = Event()
            event.add("summary", holiday_name)
            event.add("dtstart", datetime.strptime(holiday_date, "%Y-%m-%d").date())
            event.add("uid", f"{holiday_date}-{holiday_name}@mycalendar")
            cal.add_component(event)
            logger.info(f"Added: {holiday_name} on {holiday_date}")

    # Save the iCal file
    with open("us_holidays.ics", "wb") as f:
        f.write(cal.to_ical())
    logger.info("Calendar saved as 'us_holidays.ics'")


def main():
    # Parse command-line arguments
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
        help="End year for the calendar (default: start year + 1)",
    )
    args = parser.parse_args()
    start_year = args.year
    end_year = args.end_year if args.end_year else start_year + 1

    generate_calendar(start_year, end_year)


if __name__ == "__main__":
    main()
