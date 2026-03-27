# Repository Guidelines

## Project Structure & Module Organization
- `src/generate_calendar/`: Python source of truth for holiday generation and CLI behavior. `holidays.yaml` lives here.
- `tests/`: Pytest coverage for generator behavior, validation, and edge cases.
- `cloudflare/src/`: Worker runtime code. `calendar.js` contains shared Worker calendar logic; `index.js` handles HTTP and scheduled execution.
- `cloudflare/scripts/`: deploy/build helpers such as fallback calendar generation and parity checks.
- `.github/workflows/`: validation workflow run on pushes and pull requests.

## Build, Test, and Development Commands
- `poetry install`: install Python dependencies.
- `npm install`: install Worker/Wrangler dependencies.
- `poetry run pytest -q`: run Python tests.
- `poetry run black --check .`: verify Python formatting.
- `poetry run flake8 .`: run Python linting.
- `poetry run mypy .`: run Python type checks.
- `npm run worker:verify`: check Worker syntax, compare Worker/Python parity, and run a Wrangler dry-run bundle.
- `npx wrangler deploy`: deploy the Worker manually if needed. GitHub-connected Cloudflare builds remain the normal deployment path.

## Coding Style & Naming Conventions
- Use 4-space indentation in Python and standard ES module style in JavaScript.
- Keep logic small and explicit; this repo favors simple data flow over abstraction.
- Python formatting is enforced by Black, linting by Flake8, and typing by MyPy.
- Use descriptive snake_case for Python names and camelCase for JavaScript helpers.
- Keep holiday metadata in YAML, not hard-coded lists, when possible.

## Testing Guidelines
- Tests use `pytest`; name files `test_*.py` and test functions `test_*`.
- Add regression coverage for date logic changes, especially observance, leap-year behavior, and config validation.
- Run `poetry run pytest -q` and `npm run worker:verify` before pushing.

## Commit & Pull Request Guidelines
- Follow Conventional Commits, as seen in history: `fix(worker): ...`, `feat(calendar): ...`.
- Keep commits scoped to one logical change.
- PRs should briefly describe the behavior change, note any Cloudflare config impacts, and include verification commands with outcomes.

## Security & Configuration Tips
- `wrangler.toml` contains Worker routes, cron schedule, and KV bindings. Treat binding changes carefully.
- `CALENDAR_CACHE` must be configured in Cloudflare for scheduled refreshes to populate KV.
- Avoid committing generated output, local caches, secrets, or Cloudflare tokens.
