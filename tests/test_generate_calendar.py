from datetime import datetime
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from generate_calendar import (
    build_holiday_entries,
    calculate_default_end_year,
    cli,
    generate_calendar,
    get_easter_sunday,
    get_last_weekday,
    get_nth_weekday,
    load_holidays,
    validate_holiday_definitions,
)


def write_holidays_file(path: Path, holidays: dict) -> None:
    path.write_text(
        yaml.safe_dump(holidays, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def test_easter_sunday() -> None:
    assert get_easter_sunday(2025) == datetime(2025, 4, 20).date()
    assert get_easter_sunday(2026) == datetime(2026, 4, 5).date()


def test_nth_weekday() -> None:
    assert get_nth_weekday(2025, 1, 0, 3) == datetime(2025, 1, 20).date()
    assert get_nth_weekday(2025, 11, 3, 4) == datetime(2025, 11, 27).date()


def test_last_weekday() -> None:
    assert get_last_weekday(2025, 5, 0) == datetime(2025, 5, 26).date()


def test_default_end_year_is_inclusive() -> None:
    assert calculate_default_end_year(2025) == 2034


def test_load_holidays_uses_bundled_data() -> None:
    holiday_config = load_holidays()
    manual_names = {holiday["name"] for holiday in holiday_config["manual_holidays"]}
    assert "National Ice Cream Day" in manual_names


def test_validate_holiday_definitions_rejects_duplicate_names() -> None:
    with pytest.raises(ValueError, match="Holiday names must be unique"):
        validate_holiday_definitions(
            {
                "manual_holidays": [{"name": "Duplicate", "month": 1, "day": 1}],
                "calculated_holidays": [{"name": "Duplicate", "type": "easter"}],
                "federal_holidays": [],
            }
        )


def test_generate_calendar_writes_expected_output(tmp_path: Path) -> None:
    output_path = tmp_path / "calendar.ics"

    result = generate_calendar(2025, 2025, output_file=output_path)

    assert result == output_path
    calendar_text = output_path.read_text(encoding="utf-8")
    assert "SUMMARY:New Year's Day" in calendar_text
    assert "SUMMARY:National Ice Cream Day" in calendar_text


def test_generate_calendar_dry_run_does_not_write_file(tmp_path: Path) -> None:
    output_path = tmp_path / "calendar.ics"

    result = generate_calendar(2025, 2025, dry_run=True, output_file=output_path)

    assert result is None
    assert not output_path.exists()


def test_build_holiday_entries_rejects_inverted_year_range() -> None:
    with pytest.raises(ValueError, match="end_year must be greater than or equal to start_year"):
        build_holiday_entries(2026, 2025)


def test_add_holiday_updates_only_target_file(tmp_path: Path) -> None:
    holiday_path = tmp_path / "holidays.yaml"
    holiday_config = load_holidays()
    write_holidays_file(holiday_path, holiday_config)
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["add-holiday", "--holidays-file", str(holiday_path), "Test Holiday", "12", "1"],
    )

    assert result.exit_code == 0
    updated_holidays = yaml.safe_load(holiday_path.read_text(encoding="utf-8"))
    assert any(holiday["name"] == "Test Holiday" for holiday in updated_holidays["manual_holidays"])


def test_remove_holiday_updates_only_target_file(tmp_path: Path) -> None:
    holiday_path = tmp_path / "holidays.yaml"
    holiday_config = load_holidays()
    holiday_config["manual_holidays"].append({"name": "Temporary Holiday", "month": 8, "day": 8})
    write_holidays_file(holiday_path, holiday_config)
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["remove-holiday", "--holidays-file", str(holiday_path), "Temporary Holiday"],
    )

    assert result.exit_code == 0
    updated_holidays = yaml.safe_load(holiday_path.read_text(encoding="utf-8"))
    assert all(
        holiday["name"] != "Temporary Holiday" for holiday in updated_holidays["manual_holidays"]
    )
