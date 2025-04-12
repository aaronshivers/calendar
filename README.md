# Calendar Project

[![Update Calendar](https://github.com/aaronshivers/calendar/actions/workflows/update-calendar.yml/badge.svg)](https://github.com/aaronshivers/calendar/actions/workflows/update-calendar.yml)

This project generates a custom iCal (`.ics`) file containing a curated list of US holidays, including federal holidays and additional non-national holidays like Halloween and Festivus. It’s designed to be reusable for any year range and can be subscribed to for automatic updates.

## Features

- Generates a custom `.ics` file for a range of years (current year + 5 by default, configurable).
- Calculates federal holidays locally (e.g., New Year's Day, Independence Day) with observance rules (shifts to Friday/Monday if on weekends).
- Includes manually defined holidays (e.g., Groundhog Day, Mother's Day) with fixed or calculated dates from `src/holidays.json`.
- Supports recurring events for fixed holidays (e.g., Christmas Day) using `RRULE`.
- Adds optional event descriptions and reminders (e.g., 1-day or multi-day prior alarms).
- Supports subscription via a hosted URL for periodic updates in calendar apps.
- CLI commands to add/remove holidays, dry-run generation, and specify a custom holidays file.
- Caches calculated dates for performance in `holiday_cache.pkl`.

## Requirements

- Python 3.13+
- [Poetry](https://python-poetry.org/docs/) for dependency management
- Dependencies: `icalendar`, `click`

## Installation

### Using Devbox (Recommended)

This project includes a Devbox configuration for setting up the development environment. Devbox will install Python 3.13, Poetry, and all dependencies automatically.

1. Install Devbox if you haven't already: [Devbox Installation Guide](https://www.jetify.com/devbox/docs/installing_devbox/).

2. Clone the repository:

    ```shell
    git clone https://github.com/aaronshivers/calendar.git
    cd calendar
    ```

3. Set up the environment with Devbox:

    ```shell
    devbox install
    devbox shell
    ```

This will activate the environment, install dependencies via Poetry, and make the `poetry` and `python` commands available.

### Using Poetry (Alternative)

If you prefer to set up the environment manually with Poetry:

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

First, activate the Poetry virtual environment (if not using Devbox):

```shell
source $(poetry env info --path)/bin/activate
```

- **Generate for Default Year Range**:

```shell
poetry run generate_calendar generate
```

- **Generate for a Custom Year Range**:

```shell
poetry run generate_calendar generate --year 2025 --end-year 2030
```

- **Dry Run (Preview Without Writing)**:

```shell
poetry run generate_calendar generate --dry-run
```

- **Verbose Logging**:

```shell
poetry run generate_calendar generate --verbose
```

- **Use a Custom Holidays File**:

```shell
poetry run generate_calendar generate --holidays-file custom_holidays.json
```

- **Add a Holiday**:

```shell
poetry run generate_calendar add-holiday "National Pizza Day" 2 9
```

- **Remove a Holiday**:

```shell
poetry run generate_calendar remove-holiday "National Pizza Day"
```

- Output: Creates `us_holidays.ics` in the project directory (configurable).

## Holiday List

The calendar includes:

- **Federal Holidays** (calculated locally with observance rules):
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
- **Additional Holidays** (manually added or calculated in `src/holidays.json`):
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
  - `default_year_range`: The default number of years to generate if `--end-year` is not specified (default: 5).
- Edit `config/config.json` to customize these settings.

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
poetry run generate_calendar add-holiday "National Pizza Day" 2 9 --holidays-file custom_holidays.json
```

- **Remove a Holiday**:

```shell
poetry run generate_calendar remove-holiday "National Pizza Day" --holidays-file custom_holidays.json
```

## Documentation

Documentation is generated using `pdoc` and available as `generate_calendar.html` in the repository. To generate the documentation:

```shell
poetry run pdoc -o html generate_calendar
mv html/generate_calendar.html generate_calendar.html
rm -rf html/
```

## Linting and Formatting

- **Markdown Linting**: Use `pymarkdownlnt` to check Markdown files for style issues:

```shell
poetry run pymarkdownlnt scan README.md
```

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

- Run unit tests with coverage to verify holiday calculations and functionality:

```shell
poetry run coverage run -m unittest tests/test_generate_calendar.py
poetry run coverage report
```

- Tests cover date calculations, calendar generation, CLI commands, observance rules, reminders, and caching.

## Automating Updates

- The calendar is regenerated monthly on the 1st via GitHub Actions. See `.github/workflows/update-calendar.yml` for details.

## Subscription

To subscribe to the calendar for automatic updates, use the following URL in your calendar application:

<https://raw.githubusercontent.com/aaronshivers/calendar/master/us_holidays.ics>

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

- Edit `src/generate_calendar/__init__.py` to modify the core logic.
- Edit `src/holidays.json` (or a custom file) to update the holiday list.
- Test locally before pushing updates to the hosted file.

## License

MIT License - feel free to use, modify, and distribute.

## Contributing

Pull requests welcome! Please open an issue first to discuss changes.
