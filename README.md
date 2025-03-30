# US Holidays Calendar

This project generates a custom iCal (`.ics`) file containing a curated list of US holidays, including federal holidays and additional non-national holidays like Halloween and Festivus. It’s designed to be reusable for any year range and can be subscribed to for automatic updates.

## Features
- Generates a custom `.ics` file for a range of years (current year and next year by default).
- Calculates federal holidays locally (e.g., New Year's Day, Independence Day) without external API dependencies.
- Includes manually defined holidays (e.g., Groundhog Day, Mother's Day) with fixed or calculated dates from `src/holidays.json`.
- Supports subscription via a hosted URL for periodic updates in calendar apps.
- CLI commands to add/remove holidays and dry-run generation.

## Requirements
- Python 3.13+
- [Poetry](https://python-poetry.org/) for dependency management
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
   poetry run python generate_calendar.py
```
- **Generate for a Custom Year Range**:
```shell
poetry run python generate_calendar.py --year 2025 --end-year 2030
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
- **Additional Holidays** (manually added in `holidays.json`):
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

## Adding New Holidays
- Edit `holidays.json` to add new holidays:
  - **Fixed-Date Holiday**: Add to `manual_holidays` (e.g., `{"name": "National Ice Cream Day", "month": 7, "day": 21}`).
  - **Calculated Holiday**: Add to `calculated_holidays` (e.g., `{"name": "Grandparents' Day", "type": "nth_weekday", "month": 9, "weekday": 6, "nth": 1}`).
  - **Federal Holiday**: Add to `federal_holidays` (e.g., `{"name": "New Federal Holiday", "month": 8, "day": 15}`).

## Subscribing to the Calendar
1. **Host the File**:
   - The calendar is hosted on GitHub Pages at `https://aaronshivers.github.io/calendar/us_holidays.ics`.
2. **Subscribe**:
   - **Apple Calendar (iCal)**: Use `File > New Calendar Subscription`, enter the URL, and set auto-refresh to "Every day."
   - **Google Calendar**: Add via "Other calendars > From URL."
   - **Outlook**: Add via "Add calendar > Subscribe from web."
3. **Updates**: The calendar is updated monthly on the 1st via GitHub Actions. Calendar apps will refresh periodically (e.g., daily for iCal if set to "Every day").

## Automating Updates
- **GitHub Actions**:
   The calendar is regenerated monthly on the 1st and on pushes to the `master` branch. See `.github/workflows/update-calendar.yml` for details.

## Testing
- Run unit tests to verify holiday calculations:
```shell
poetry run python -m unittest tests/test_generate_calendar
```

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

## Type Checking
- **Type Checking**: Use `mypy` to check for type-related issues:
```shell
poetry run mypy .
```

## Managing Holidays
- **Add a Holiday**:
```shell
poetry run python generate_calendar.py add-holiday "National Pizza Day" 2 9
```
- **Remove a Holiday**:
```shell
poetry run python generate_calendar.py remove-holiday "National Pizza Day"
```

## Documentation
- Documentation is generated using `pydoc` and available as `generate_calendar.html` in the repository.

## Configuration
- The script uses `config.json` to configure runtime options:
  - `output_file`: The name of the generated iCal file (default: `us_holidays.ics`).
  - `cache_file`: The name of the cache file (default: `holiday_cache.pkl`).
  - `default_year_range`: The default number of years to generate if `--end-year` is not specified (default: 2).
- Edit `config.json` to customize these settings.

## Development
- Edit `generate_calendar.py` to modify the core logic.
- Edit `holidays.json` to update the holiday list.
- Test locally before pushing updates to the hosted file.

## Dry Run
- Use the `--dry-run` flag to preview the holidays without writing the iCal file:
  ```bash
  poetry run python generate_calendar.py --dry-run
  
## License
MIT License - feel free to use, modify, and distribute.

## Contributing
Pull requests welcome! Please open an issue first to discuss changes.