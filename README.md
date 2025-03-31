# US Holidays Calendar

[![Update Calendar](https://github.com/aaronshivers/calendar/actions/workflows/update-calendar.yml/badge.svg)](https://github.com/aaronshivers/calendar/actions/workflows/update-calendar.yml)

This project generates a custom iCal (`.ics`) file containing a curated list of US holidays, including federal holidays and additional non-national holidays like Halloween and Festivus. It’s designed to be reusable for any year range and can be subscribed to for automatic updates.

## Features
- Generates a custom `.ics` file for a range of years (current year and next year by default).
- Calculates federal holidays locally (e.g., New Year's Day, Independence Day) without external API dependencies.
- Includes manually defined holidays (e.g., Groundhog Day, Mother's Day) with fixed or calculated dates from `src/holidays.json`.
- Supports subscription via a hosted URL for periodic updates in calendar apps.
- CLI commands to add/remove holidays and dry-run generation.

## Requirements
- Python 3.13+
- [Poetry](https://python-poetry.org/docs/) for dependency management
- Dependencies: `icalendar`, `click`

## Installation
1. Clone the repository:
```shell
git clone https://github.com/aaronshivers/calendar.git
cd calendar
```
2. Install dependencies with Poetry:
```shell
poetry install
```

## Usage
- **Generate for Current Year and Next Year**:
```shell
poetry run python src/generate_calendar.py
```
- **Generate for a Custom Year Range**:
```shell
poetry run python src/generate_calendar.py --year 2025 --end-year 2030
```
- **Dry Run (Preview Without Writing)**:
```shell
poetry run python src/generate_calendar.py --dry-run
```
- **Add a Holiday**:
```shell
poetry run python src/generate_calendar.py add-holiday "National Pizza Day" 2 9
```
- **Remove a Holiday**:
```shell
poetry run python src/generate_calendar.py remove-holiday "National Pizza Day"
```
- Output: Creates `us_holidays.ics` in the project directory.

## Holiday List
The calendar includes:
- **Federal Holidays** (calculated locally):
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
- **Additional Holidays** (manually added in `src/holidays.json`):
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

## Configuration
- The script uses `config/config.json` to configure runtime options:
  - `output_file`: The name of the generated iCal file (default: `us_holidays.ics`).
  - `cache_file`: The name of the cache file (default: `holiday_cache.pkl`).
  - `default_year_range`: The default number of years to generate if `--end-year` is not specified (default: 2).
- Edit `config/config.json` to customize these settings.

## Dry Run
- Use the `--dry-run` flag to preview the holidays without writing the iCal file:
```shell
poetry run python src/generate_calendar.py --dry-run
```

## Input Validation
- The `add-holiday` command validates the month and day to ensure they form a valid date. For example, invalid dates like February 30th will be rejected.
## Type Checking
- Use `mypy` to check for type-related issues:
```shell
poetry run mypy .
```

## Managing Holidays
- **Add a Holiday**:
```shell
poetry run python src/generate_calendar.py add-holiday "National Pizza Day" 2 9
```
- **Remove a Holiday**:
```shell
poetry run python src/generate_calendar.py remove-holiday "National Pizza Day"
```

## Documentation
- Documentation is generated using `pydoc` and available as `generate_calendar.html` in the repository.

## Linting and Formatting
- **Linting**: Use `flake8` to check for style issues and potential errors:
```shell
poetry run flake8 .
```
- **Formatting**: Use `black` to auto-format the code:
```shell
poetry run black .
```
- These steps are also run in the GitHub Actions workflow to ensure code quality.

## Testing
- Run unit tests to verify holiday calculations:
```shell
poetry run python -m unittest discover -s tests
```

## Automating Updates
- The calendar is regenerated monthly on the 1st via GitHub Actions. See `.github/workflows/update-calendar.yml` for details.

## Automating Updates
- The calendar is regenerated monthly on the 1st via GitHub Actions. See `.github/workflows/update-calendar.yml` for details.

## Subscription
To subscribe to the calendar for automatic updates, use the following URL in your calendar application:

https://raw.githubusercontent.com/aaronshivers/calendar/master/us_holidays.ics

### Instructions for Popular Calendar Apps

#### Google Calendar
1. Open Google Calendar.
2. Click on "Add calendar" in the left-hand menu.
3. Select "From URL".
4. Enter the URL: `https://raw.githubusercontent.com/aaronshivers/calendar/master/us_holidays.ics`
5. Click "Add calendar".

#### Apple Calendar (macOS/iOS)
1. Open the Calendar app.
2. Go to "File" > "New Calendar Subscription".
3. Enter the URL: `https://raw.githubusercontent.com/aaronshivers/calendar/master/us_holidays.ics`
4. Click "Subscribe".

#### Microsoft Outlook
1. Open Outlook.
2. Go to "File" > "Account Settings" > "Account Settings".
3. Click on "Internet Calendars" tab.
4. Click "Add".
5. Enter the URL: `https://raw.githubusercontent.com/aaronshivers/calendar/master/us_holidays.ics`
6. Click "Add".

## Development
- Edit `src/generate_calendar.py` to modify the core logic.
- Edit `src/holidays.json` to update the holiday list.
- Test locally before pushing updates to the hosted file.

## License
MIT License - feel free to use, modify, and distribute.

## Contributing
Pull requests welcome! Please open an issue first to discuss changes.

## Development
- Edit `src/generate_calendar.py` to modify the core logic.
- Edit `src/holidays.json` to update the holiday list.
- Test locally before pushing updates to the hosted file.

## License
MIT License - feel free to use, modify, and distribute.

## Contributing
Pull requests welcome! Please open an issue first to discuss changes.