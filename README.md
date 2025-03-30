# My Custom US Holidays Calendar

This project generates a custom iCal (`.ics`) file containing a curated list of US holidays, including federal holidays from the Nager.Date API and additional non-national holidays like Halloween and Festivus. It’s designed to be reusable for any year and can be subscribed to for automatic updates.

## Features
- Generates a custom `.ics` file for any specified year (defaults to current year).
- Includes federal holidays (e.g., New Year's Day, Independence Day) from [Nager.Date API](https://date.nager.at/).
- Adds manually defined holidays (e.g., Groundhog Day, Mother's Day) with fixed or calculated dates.
- Supports subscription via a hosted URL for periodic updates in calendar apps.

## Requirements
- Python 3.13+
- [Poetry](https://python-poetry.org/) for dependency management
- Dependencies: `requests`, `icalendar`

## Installation
1. Clone the repository:
```shell
   git clone https://github.com/yourusername/my-holiday-calendar.git
   cd my-holiday-calendar
```
2. Install dependencies with Poetry:
```shell
   poetry install
```

## Usage
- **Generate for Current Year**:
```shell
   poetry run python generate_calendar.py
```
- **Generate for Specific Year**:
```shell
   poetry run python generate_calendar.py --year 2026
```
- Output: Creates `us_holidays_{YEAR}.ics` in the project directory.


## Holiday List
The calendar includes:
- **Federal Holidays** (from Nager.Date):
  - New Year's Day
  - Martin Luther King Jr. Day
  - Presidents' Day
  - Memorial Day
  - Juneteenth
  - Independence Day
  - Labor Day
  - Columbus Day
  - Veterans Day
  - Thanksgiving Day
  - Christmas Day
- **Additional Holidays** (manually added):
  - Groundhog Day (Feb 2)
  - Valentine's Day (Feb 14)
  - St. Patrick's Day (Mar 17)
  - April Fool's Day (Apr 1)
  - Easter Sunday (calculated)
  - Earth Day (Apr 22)
  - Cinco de Mayo (May 5)
  - Mother's Day (2nd Sunday in May)
  - Father's Day (3rd Sunday in June)
  - Halloween (Oct 31)
  - Festivus (Dec 23)

## Subscribing to the Calendar
1. **Host the File**:
   - Upload `us_holidays_{YEAR}.ics` to a public URL (e.g., GitHub Pages: `https://yourusername.github.io/my-holiday-calendar/us_holidays_2025.ics`).
2. **Subscribe**:
   - **Google Calendar**: Add via "Other calendars > From URL."
   - **Apple Calendar**: Use `File > New Calendar Subscription` and set auto-refresh.
   - **Outlook**: Add via "Add calendar > Subscribe from web."
3. **Updates**: Calendar apps will refresh periodically (e.g., daily for Google, configurable in Apple Calendar).


## Automating Updates
- **Local Cron Job**:
```
# Run daily at 1 AM
0 1 * * * /path/to/poetry run python /path/to/generate_calendar.py
```
- **GitHub Actions**:
See `.github/workflows/update-calendar.yml` for a monthly update workflow.

## Development
- Edit `generate_calendar.py` to modify the holiday list or logic.
- Test locally before pushing updates to the hosted file.

## License
MIT License - feel free to use, modify, and distribute.

## Contributing
Pull requests welcome! Please open an issue first to discuss changes.