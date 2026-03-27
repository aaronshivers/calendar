# US Holidays Calendar

This project builds a static iCalendar (`.ics`) file for a curated set of US holidays. The repository is optimized around generating a long-lived calendar file that can be hosted from a stable URL and subscribed to by calendar clients such as Apple Calendar, Google Calendar, and Outlook.

## What This Repo Does
- Generates a static `us_holidays.ics` file.
- Bundles the holiday definitions with the Python package so the CLI works outside the repo root.
- Ships enough years by default to avoid depending on a monthly automation job.
- Supports editing the holiday definition file with `add-holiday` and `remove-holiday`.

## Requirements
- Python 3.13+
- Poetry

## Installation
```shell
poetry install
```

## Generate the Calendar
Generate the current year plus the next 9 years into `us_holidays.ics`:

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

## Cloudflare Deployment
The permanent automation path lives in [cloudflare/](/Users/as082003/IdeaProjects/calendar/cloudflare):
- [wrangler.toml](/Users/as082003/IdeaProjects/calendar/cloudflare/wrangler.toml) configures the Worker, monthly cron trigger, and KV binding.
- [src/index.js](/Users/as082003/IdeaProjects/calendar/cloudflare/src/index.js) serves the current `.ics` file over HTTP and refreshes it on Cloudflare's cron trigger.
- [package.json](/Users/as082003/IdeaProjects/calendar/cloudflare/package.json) provides local Worker scripts via Wrangler.

How it works:
- the Worker fetches [holidays.yaml](/Users/as082003/IdeaProjects/calendar/src/generate_calendar/holidays.yaml) from a raw URL you configure in `HOLIDAYS_YAML_URL`
- on the first day of each month, Cloudflare regenerates the calendar and stores it in Workers KV
- normal HTTP requests return the cached `text/calendar` payload from KV

Setup steps:
1. Create a Workers KV namespace for the calendar payload.
2. Replace the placeholder values in [wrangler.toml](/Users/as082003/IdeaProjects/calendar/cloudflare/wrangler.toml):
   `HOLIDAYS_YAML_URL` should point at the raw hosted `src/generate_calendar/holidays.yaml` file in this repo, and the KV `id` / `preview_id` should be your namespace IDs.
3. In [cloudflare/](/Users/as082003/IdeaProjects/calendar/cloudflare), run `npm install`.
4. Deploy with `npx wrangler deploy`.
5. Subscribe iCloud or any other calendar client to the Worker URL.

For local cron testing, run `npx wrangler dev --test-scheduled` and then trigger the cron endpoint locally.

## Static Hosting
[app.py](/Users/as082003/IdeaProjects/calendar/app.py) still works if you want to serve a generated local file yourself, but the recommended automated path is now Cloudflare Workers rather than GitHub Actions scheduling.

## Repository Automation
[update-calendar.yml](/Users/as082003/IdeaProjects/calendar/.github/workflows/update-calendar.yml) is now validation-only. It checks formatting, linting, typing, tests, and a dry-run calendar build on pushes and pull requests.

## Quality Checks
```shell
poetry run black --check .
poetry run flake8 .
poetry run mypy .
poetry run pytest -q
```

## Project Layout
- [src/generate_calendar/__init__.py](/Users/as082003/IdeaProjects/calendar/src/generate_calendar/__init__.py): calendar generation logic and CLI entrypoint
- [src/generate_calendar/holidays.yaml](/Users/as082003/IdeaProjects/calendar/src/generate_calendar/holidays.yaml): bundled holiday definitions
- [cloudflare/src/index.js](/Users/as082003/IdeaProjects/calendar/cloudflare/src/index.js): Worker runtime for scheduled refresh and HTTP serving
- [tests/test_generate_calendar.py](/Users/as082003/IdeaProjects/calendar/tests/test_generate_calendar.py): hermetic tests

## License
MIT
