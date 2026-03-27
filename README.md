# US Holidays Calendar

This project builds an iCalendar (`.ics`) feed for a curated set of US holidays. The repository is optimized around serving that calendar from a stable URL that clients such as Apple Calendar, Google Calendar, and Outlook can subscribe to directly.

## What This Repo Does
- Generates a static `us_holidays.ics` file.
- Bundles the holiday definitions with the Python package so the CLI works outside the repo root.
- Serves the current year plus the next year by default, which keeps the feed practical without overcommitting to a long forecasting window.
- Supports editing the holiday definition file with `add-holiday` and `remove-holiday`.
- Treats weekend observance and per-holiday enable/disable switches as data in [holidays.yaml](/Users/as082003/IdeaProjects/calendar/src/generate_calendar/holidays.yaml), including leap-day safety.

## Requirements
- Python 3.13+
- Poetry

## Installation
```shell
poetry install
```

## Generate the Calendar
Generate the current year plus the next year into `us_holidays.ics`:

```shell
poetry run generate_calendar
```

Generate a custom range:

```shell
poetry run generate_calendar --year 2025 --end-year 2030
```

Write to a different path:

```shell
poetry run generate_calendar --output /tmp/us-holidays.ics
```

Preview the build without writing a file:

```shell
poetry run generate_calendar --dry-run
```

## Manage Holiday Definitions
The bundled holiday definitions live at [src/generate_calendar/holidays.yaml](/Users/as082003/IdeaProjects/calendar/src/generate_calendar/holidays.yaml).

Add a holiday to a specific YAML file:

```shell
poetry run generate_calendar add-holiday --holidays-file src/generate_calendar/holidays.yaml "National Pizza Day" 2 9
```

Remove a holiday from a specific YAML file:

```shell
poetry run generate_calendar remove-holiday --holidays-file src/generate_calendar/holidays.yaml "National Pizza Day"
```

If you run these commands against an installed, read-only package, pass `--holidays-file` so the CLI knows which editable YAML file to modify.

You can also disable a holiday without deleting it:

```yaml
manual_holidays:
  - name: National Ice Cream Day
    month: 7
    day: 21
    enabled: false
```

If `enabled` is omitted, the holiday is included by default.

## Cloudflare Deployment
The recommended permanent deployment path is Cloudflare Workers using the root-level [wrangler.toml](/Users/as082003/IdeaProjects/calendar/wrangler.toml) and [package.json](/Users/as082003/IdeaProjects/calendar/package.json).

How it works:
- Wrangler runs [build_static_calendar.py](/Users/as082003/IdeaProjects/calendar/cloudflare/scripts/build_static_calendar.py) at deploy time to generate a bundled `.ics` fallback artifact
- the Worker serves the most recently stored calendar from Cloudflare KV and only falls back to the deploy-built artifact if KV is empty
- a monthly Cloudflare cron trigger refreshes the stored calendar on the schedule in [wrangler.toml](/Users/as082003/IdeaProjects/calendar/wrangler.toml)
- subscriber traffic only reads the stored calendar; it does not regenerate the feed
- the Worker returns the file with `text/calendar` headers from a stable HTTPS URL

The monthly cron runs at `00:00 UTC` on the first day of each month (`0 0 1 * *`).

Setup steps:
1. From the repo root, run `npm install`.
2. Create the KV namespace once with `npx wrangler kv namespace create CALENDAR_CACHE`.
3. Copy the returned IDs into the commented `[[kv_namespaces]]` block in [wrangler.toml](/Users/as082003/IdeaProjects/calendar/wrangler.toml).
4. Deploy from the repo root with `npx wrangler deploy`.
5. Subscribe iCloud or any other calendar client to the Worker URL.

## Static Hosting
[app.py](/Users/as082003/IdeaProjects/calendar/app.py) still works if you want to serve a generated local file yourself, but the recommended automated path is now Cloudflare Workers rather than GitHub Actions scheduling.

## Repository Automation
[update-calendar.yml](/Users/as082003/IdeaProjects/calendar/.github/workflows/update-calendar.yml) is validation-only. It checks formatting, linting, typing, tests, and a dry-run calendar build on pushes and pull requests.

## Quality Checks
```shell
poetry run black --check .
poetry run flake8 .
poetry run mypy .
poetry run pytest -q
npm run worker:verify
```

## Project Layout
- [src/generate_calendar/__init__.py](/Users/as082003/IdeaProjects/calendar/src/generate_calendar/__init__.py): calendar generation logic and CLI entrypoint
- [src/generate_calendar/holidays.yaml](/Users/as082003/IdeaProjects/calendar/src/generate_calendar/holidays.yaml): bundled holiday definitions
- [cloudflare/src/calendar.js](/Users/as082003/IdeaProjects/calendar/cloudflare/src/calendar.js): shared Worker calendar logic used by deploys and parity checks
- [cloudflare/src/index.js](/Users/as082003/IdeaProjects/calendar/cloudflare/src/index.js): Worker runtime for KV-backed serving and scheduled refresh
- [cloudflare/scripts/check-parity.mjs](/Users/as082003/IdeaProjects/calendar/cloudflare/scripts/check-parity.mjs): parity check between Worker and Python holiday generation
- [cloudflare/scripts/build_static_calendar.py](/Users/as082003/IdeaProjects/calendar/cloudflare/scripts/build_static_calendar.py): deploy-time build step for the bundled fallback `.ics`
- [tests/test_generate_calendar.py](/Users/as082003/IdeaProjects/calendar/tests/test_generate_calendar.py): hermetic tests

## License
MIT
