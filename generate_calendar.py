from icalendar import Calendar, Event
from datetime import datetime, timedelta
import argparse
import json

# Parse command-line argument for year
parser = argparse.ArgumentParser(description="Generate a custom US holidays iCal file.")
parser.add_argument("--year", type=int, default=datetime.now().year, help="Year for the calendar (default: current year)")
args = parser.parse_args()
START_YEAR = args.year
END_YEAR = START_YEAR + 1  # Include the next year

# Load holiday definitions from JSON
with open("holidays.json", "r") as f:
    holiday_config = json.load(f)

APPROVED_HOLIDAYS = holiday_config["approved_holidays"]
MANUAL_HOLIDAYS = holiday_config["manual_holidays"]
CALCULATED_HOLIDAYS = holiday_config["calculated_holidays"]

# Function to calculate Easter Sunday
def get_easter_sunday(year):
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
    return datetime(year, month, day).date()

# Function to calculate nth weekday (e.g., 3rd Monday in January)
def get_nth_weekday(year, month, weekday, nth):
    first_day = datetime(year, month, 1).date()
    first_weekday = first_day + timedelta(days=(weekday - first_day.weekday() + 7) % 7)
    return first_weekday + timedelta(weeks=nth-1)

# Function to calculate last weekday of a month (e.g., last Monday in May)
def get_last_weekday(year, month, weekday):
    # Start from the last day of the month
    next_month = month % 12 + 1
    next_year = year if next_month != 1 else year + 1
    last_day = (datetime(next_year, next_month, 1).date() - timedelta(days=1))
    # Find the last occurrence of the weekday
    days_to_subtract = (last_day.weekday() - weekday + 7) % 7
    return last_day - timedelta(days=days_to_subtract)

# Calculate federal holidays
def get_federal_holidays(year):
    federal_holidays = [
        {"name": "New Year's Day", "month": 1, "day": 1},
        {"name": "Martin Luther King Jr. Day", "month": 1, "weekday": 0, "nth": 3},  # 3rd Monday
        {"name": "Presidents' Day", "month": 2, "weekday": 0, "nth": 3},  # 3rd Monday
        {"name": "Memorial Day", "month": 5, "weekday": 0, "last": True},  # Last Monday
        {"name": "Juneteenth", "month": 6, "day": 19},
        {"name": "Independence Day", "month": 7, "day": 4},
        {"name": "Labor Day", "month": 9, "weekday": 0, "nth": 1},  # 1st Monday
        {"name": "Columbus Day", "month": 10, "weekday": 0, "nth": 2},  # 2nd Monday
        {"name": "Veterans Day", "month": 11, "day": 11},
        {"name": "Thanksgiving Day", "month": 11, "weekday": 3, "nth": 4},  # 4th Thursday
        {"name": "Christmas Day", "month": 12, "day": 25}
    ]

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
            "date": date.strftime('%Y-%m-%d')
        })
    return holidays

# Generate holidays for a range of years
holidays = []
for YEAR in range(START_YEAR, END_YEAR + 1):
    # Calculate federal holidays
    year_holidays = get_federal_holidays(YEAR)

    # Calculate variable holidays (e.g., Easter, Mother's Day)
    calculated_holidays_with_year = []
    for holiday in CALCULATED_HOLIDAYS:
        if holiday["type"] == "easter":
            date = get_easter_sunday(YEAR)
        elif holiday["type"] == "nth_weekday":
            date = get_nth_weekday(YEAR, holiday["month"], holiday["weekday"], holiday["nth"])
        calculated_holidays_with_year.append({
            "name": holiday["name"],
            "date": date.strftime('%Y-%m-%d')
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

# Create iCal calendar
cal = Calendar()
cal.add('prodid', '-//My Custom US Holidays//jetify.dev//')
cal.add('version', '2.0')

# Filter and add holidays
for holiday in holidays:
    holiday_name = holiday["name"]
    holiday_date = holiday["date"]

    if holiday_name in APPROVED_HOLIDAYS:
        event = Event()
        event.add('summary', holiday_name)
        event.add('dtstart', datetime.strptime(holiday_date, '%Y-%m-%d').date())
        event.add('dtend', datetime.strptime(holiday_date, '%Y-%m-%d').date())
        event.add('uid', f"{holiday_date}-{holiday_name}@mycalendar")
        cal.add_component(event)
        print(f"Added: {holiday_name} on {holiday_date}")

# Save the iCal file
with open(f"us_holidays_{START_YEAR}_to_{END_YEAR}.ics", "wb") as f:
    f.write(cal.to_ical())
print(f"Calendar saved as 'us_holidays_{START_YEAR}_to_{END_YEAR}.ics'")