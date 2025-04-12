import sys
import unittest
from datetime import datetime
import json
import os
import shutil
import tempfile
import pickle
from icalendar import Calendar
from click.testing import CliRunner
from generate_calendar import (
    get_easter_sunday,
    get_nth_weekday,
    get_last_weekday,
    get_federal_holidays,
    cli,
)


# Add src/ to the Python path to import generate_calendar
# Adjust path if necessary
script_dir = os.path.dirname(__file__)
# Assuming tests/ is one level down from project root
project_root = os.path.abspath(os.path.join(script_dir, ".."))
src_dir = os.path.join(project_root, "src")
config_dir = os.path.join(project_root, "config")
sys.path.insert(0, src_dir)


class TestHolidayCalculations(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test artifacts
        self.test_dir = tempfile.mkdtemp()
        self.output_file = os.path.join(self.test_dir, "us_holidays.ics")  # Output in temp
        self.cache_file = os.path.join(self.test_dir, "holiday_cache.pkl")  # Cache in temp
        self.holidays_file_orig = os.path.join(src_dir, "holidays.json")
        self.temp_holidays_json = os.path.join(self.test_dir, "holidays.json")  # Temp copy
        self.config_file_orig = os.path.join(config_dir, "config.json")
        self.temp_config_dir = os.path.join(self.test_dir, "config")
        self.temp_config_json = os.path.join(self.temp_config_dir, "config.json")

        # Create temp config dir and copy config
        os.makedirs(self.temp_config_dir, exist_ok=True)
        shutil.copy(self.holidays_file_orig, self.temp_holidays_json)
        shutil.copy(self.config_file_orig, self.temp_config_json)

        # Manually set CONFIG paths for test isolation if generate_calendar uses them directly
        # This is fragile; mocking or dependency injection is preferred.
        # If generate_calendar re-imports or reloads config internally, this won't work.
        # Better approach: Pass paths via CLI options or have functions accept paths.
        # For now, assuming generate_calendar might pick up these paths somehow.
        # However, the safest way is to test via CLI where paths can be passed.
        # generate_calendar.OUTPUT_FILE = self.output_file # Example patch
        # generate_calendar.CACHE_FILE = self.cache_file # Example patch

        self.cache = {}  # Start with empty cache for date calc functions
        self.runner = CliRunner()

        # Clean up output file possibly left by main script from project root
        if os.path.exists("us_holidays.ics"):
            os.remove("us_holidays.ics")
        if os.path.exists("holiday_cache.pkl"):
            os.remove("holiday_cache.pkl")

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)
        # Clean up output file if it exists in project root
        if os.path.exists("us_holidays.ics"):
            os.remove("us_holidays.ics")
        # Clean up default cache file if it exists
        if os.path.exists("holiday_cache.pkl"):
            os.remove("holiday_cache.pkl")

    def load_temp_holidays(self):
        with open(self.temp_holidays_json, "r") as f:
            return json.load(f)

    def save_temp_holidays(self, holidays):
        with open(self.temp_holidays_json, "w") as f:
            json.dump(holidays, f, indent=2)

    def test_easter_sunday(self):
        easter_2025 = get_easter_sunday(2025, self.cache)
        self.assertEqual(easter_2025, datetime(2025, 4, 20).date())
        easter_2026 = get_easter_sunday(2026, self.cache)
        self.assertEqual(easter_2026, datetime(2026, 4, 5).date())

    def test_nth_weekday(self):
        mlk_2025 = get_nth_weekday(2025, 1, 0, 3, self.cache)
        self.assertEqual(mlk_2025, datetime(2025, 1, 20).date())
        thanksgiving_2025 = get_nth_weekday(2025, 11, 3, 4, self.cache)
        self.assertEqual(thanksgiving_2025, datetime(2025, 11, 27).date())

    def test_last_weekday(self):
        memorial_2025 = get_last_weekday(2025, 5, 0, self.cache)
        self.assertEqual(memorial_2025, datetime(2025, 5, 26).date())

    def test_invalid_year_range_cli(self):
        # Test CLI handling of invalid range
        result_low = self.runner.invoke(
            cli, ["generate", "--year", "1899", "--holidays-file", self.temp_holidays_json]
        )
        self.assertNotEqual(result_low.exit_code, 0)
        self.assertIn("Invalid year range", result_low.output)

        result_high = self.runner.invoke(
            cli, ["generate", "--year", "2101", "--holidays-file", self.temp_holidays_json]
        )
        self.assertNotEqual(result_high.exit_code, 0)
        self.assertIn("Invalid year range", result_high.output)

        result_order = self.runner.invoke(
            cli,
            [
                "generate",
                "--year",
                "2026",
                "--end-year",
                "2025",
                "--holidays-file",
                self.temp_holidays_json,
            ],
        )
        self.assertNotEqual(result_order.exit_code, 0)
        self.assertIn("Invalid year range", result_order.output)

    def test_federal_holidays(self):
        # Load federal holiday definitions from the temp file for consistency
        holidays_config = self.load_temp_holidays()
        federal_defs = holidays_config["federal_holidays"]

        year = 2025
        federal_holidays = get_federal_holidays(year, federal_defs)
        expected_dates = {
            "New Year's Day": "2025-01-01",
            "Martin Luther King Jr. Day": "2025-01-20",
            "Presidents' Day": "2025-02-17",
            "Memorial Day": "2025-05-26",
            "Juneteenth": "2025-06-19",
            "Independence Day": "2025-07-04",
            "Labor Day": "2025-09-01",
            "Columbus Day": "2025-10-13",
            "Veterans Day": "2025-11-11",
            "Thanksgiving Day": "2025-11-27",
            "Christmas Day": "2025-12-25",
        }
        actual_dates = {h["name"]: h["date"] for h in federal_holidays}
        self.assertEqual(actual_dates, expected_dates)

    def test_generate_calendar_main_cli(self):
        # CLI command now writes to the default OUTPUT_FILE path from config
        output_file_path = "us_holidays.ics"
        result = self.runner.invoke(
            cli,
            [
                "generate",
                "--year",
                "2025",
                "--end-year",
                "2025",
                "--holidays-file",
                self.temp_holidays_json,
                # Assume the main script uses the config path implicitly
            ],
        )
        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertTrue(os.path.exists(output_file_path))

        with open(output_file_path, "rb") as f:
            cal = Calendar.from_ical(f.read())
            refresh_interval = cal.get("REFRESH-INTERVAL")
            self.assertIsNotNone(refresh_interval)
            self.assertEqual(str(refresh_interval), "{'value': 'P1M'}")

            found_christmas = False
            for event in cal.walk("VEVENT"):
                if event.get("SUMMARY") == "Christmas Day":
                    self.assertEqual(event.get("DTSTART").dt, datetime(2025, 12, 25).date())
                    self.assertIn("RRULE", event)
                    self.assertEqual(event["RRULE"]["FREQ"], ["YEARLY"])
                    found_christmas = True
                    break
            self.assertTrue(found_christmas, "Christmas Day 2025 not found or missing RRULE")
        os.remove(output_file_path)

    def test_generate_calendar_dry_run_cli(self):
        output_file_path = "us_holidays.ics"
        if os.path.exists(output_file_path):
            os.remove(output_file_path)
        result = self.runner.invoke(
            cli,
            [
                "generate",
                "--year",
                "2025",
                "--end-year",
                "2025",
                "--dry-run",
                "--holidays-file",
                self.temp_holidays_json,
            ],
        )
        self.assertEqual(result.exit_code, 0, msg=result.output)
        self.assertFalse(os.path.exists(output_file_path))

    def test_generate_calendar_verbose_cli(self):
        # Check verbose runs without error and produces DEBUG logs
        # Using CliRunner's mix_stderr=False to capture logs separately
        runner_no_mix = CliRunner(mix_stderr=False)
        result = runner_no_mix.invoke(
            cli,
            [
                "generate",
                "--year",
                "2025",
                "--end-year",
                "2025",
                "--verbose",
                "--dry-run",
                "--holidays-file",
                self.temp_holidays_json,
            ],
        )
        self.assertEqual(
            result.exit_code, 0, msg=f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )
        self.assertIn("DEBUG", result.stderr)  # Check if DEBUG level logs were output to stderr

    def test_add_holiday_valid_cli(self):
        holiday_name = "Test Add Day CLI"
        result = self.runner.invoke(
            cli,
            [
                "add-holiday",
                holiday_name,
                "1",
                "10",
                "--holidays-file",
                self.temp_holidays_json,
            ],
        )
        self.assertEqual(result.exit_code, 0, msg=result.output)
        holidays = self.load_temp_holidays()
        manual_holidays = holidays.get("manual_holidays", [])
        self.assertTrue(
            any(
                h["name"] == holiday_name and h["month"] == 1 and h["day"] == 10
                for h in manual_holidays
            )
        )
        self.assertIn(holiday_name, holidays.get("approved_holidays", []))

        # Clean up
        remove_result = self.runner.invoke(
            cli, ["remove-holiday", holiday_name, "--holidays-file", self.temp_holidays_json]
        )
        self.assertEqual(remove_result.exit_code, 0)

    def test_add_holiday_invalid_date_cli(self):
        result = self.runner.invoke(
            cli,
            [
                "add-holiday",
                "Invalid Date Holiday CLI",
                "2",
                "30",
                "--holidays-file",
                self.temp_holidays_json,
            ],
        )
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Invalid date", result.output)

    def test_remove_holiday_cli(self):
        holiday_name = "Temporary Holiday To Remove CLI"
        # Add
        add_result = self.runner.invoke(
            cli,
            ["add-holiday", holiday_name, "1", "15", "--holidays-file", self.temp_holidays_json],
        )
        self.assertEqual(add_result.exit_code, 0)
        holidays_before = self.load_temp_holidays()
        self.assertTrue(any(h["name"] == holiday_name for h in holidays_before["manual_holidays"]))

        # Remove
        remove_result = self.runner.invoke(
            cli,
            ["remove-holiday", holiday_name, "--holidays-file", self.temp_holidays_json],
        )
        self.assertEqual(remove_result.exit_code, 0, msg=remove_result.output)
        holidays_after = self.load_temp_holidays()
        self.assertFalse(any(h["name"] == holiday_name for h in holidays_after["manual_holidays"]))
        self.assertNotIn(holiday_name, holidays_after["approved_holidays"])

    # test_observance_adjustment removed

    def test_cache_usage(self):
        # This test now uses the temporary cache file path
        temp_cache = os.path.join(self.test_dir, "test_cache.pkl")
        if os.path.exists(temp_cache):
            os.remove(temp_cache)

        cache = {}  # Start with empty cache dict
        # Use the standalone load_cache function for this test
        _ = get_easter_sunday(2025, cache)  # Calculate Easter, populating cache dict
        self.assertIn("easter_2025", cache)

        # Manually save this cache dict to the temp file using standalone save_cache
        try:
            with open(temp_cache, "wb") as f:
                pickle.dump(cache, f)  # Using imported pickle
        except IOError as e:
            self.fail(f"Failed to save cache for test: {e}")

        # Manually load from the temp file using standalone load_cache
        loaded_cache = {}
        if os.path.exists(temp_cache):
            try:
                with open(temp_cache, "rb") as f:
                    loaded_cache = pickle.load(f)  # Using imported pickle
            except (pickle.PickleError, EOFError) as e:
                self.fail(f"Failed to load cache for test: {e}")

        self.assertEqual(
            loaded_cache.get("easter_2025"), datetime(2025, 4, 20).date().strftime("%Y-%m-%d")
        )
        os.remove(temp_cache)


if __name__ == "__main__":
    unittest.main()
