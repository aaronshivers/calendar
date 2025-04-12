import sys
import unittest
from datetime import datetime, timedelta
import logging
import json
import os
import shutil
import tempfile
from icalendar import Calendar
from click.testing import CliRunner
from generate_calendar import (
    get_easter_sunday,
    get_nth_weekday,
    get_last_weekday,
    load_cache,
    save_cache,
    get_federal_holidays,
    generate_calendar,
    cli,
)


# Add src/ to the Python path to import generate_calendar
sys.path.insert(0, "/Users/aaron/repos/calendar/src")


class TestHolidayCalculations(unittest.TestCase):
    def setUp(self):
        self.cache = load_cache()
        # Load holidays for federal holidays test
        with open("src/holidays.json", "r") as f:
            self.holiday_config = json.load(f)
        self.federal_holidays = self.holiday_config["federal_holidays"]
        # Clean up any existing output file
        if os.path.exists("us_holidays.ics"):
            os.remove("us_holidays.ics")
        self.runner = CliRunner()
        # Create a temporary holidays.json
        self.temp_dir = tempfile.mkdtemp()
        self.temp_holidays_json = os.path.join(self.temp_dir, "holidays.json")
        shutil.copy("src/holidays.json", self.temp_holidays_json)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def load_temp_holidays(self):
        with open(self.temp_holidays_json, "r") as f:
            return json.load(f)

    def save_temp_holidays(self, holidays):
        with open(self.temp_holidays_json, "w") as f:
            json.dump(holidays, f, indent=4)

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

    def test_invalid_year_range(self):
        with self.assertRaises(SystemExit):
            generate_calendar(2026, 2025, holidays_file=self.temp_holidays_json)
        with self.assertRaises(SystemExit):
            generate_calendar(1800, 2025, holidays_file=self.temp_holidays_json)

    def test_federal_holidays(self):
        year = 2025
        federal_holidays = get_federal_holidays(year, self.federal_holidays)
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
        for holiday in federal_holidays:
            if holiday["name"] in expected_dates:
                self.assertEqual(holiday["date"], expected_dates[holiday["name"]])

    def test_generate_calendar_main(self):
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
            ],
        )
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(os.path.exists("us_holidays.ics"))
        with open("us_holidays.ics", "rb") as f:
            cal = Calendar.from_ical(f.read())
            refresh_interval = cal.get("REFRESH-INTERVAL")
            self.assertIsNotNone(refresh_interval)
            self.assertEqual(str(refresh_interval), "{'value': 'P1M'}")
            for event in cal.walk("VEVENT"):
                if event.get("SUMMARY") == "Christmas Day":
                    self.assertIn("RRULE", event)
                    self.assertEqual(event["RRULE"]["FREQ"], ["YEARLY"])
                    break

    def test_generate_calendar_dry_run(self):
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
        self.assertEqual(result.exit_code, 0)
        self.assertFalse(os.path.exists("us_holidays.ics"))

    def test_generate_calendar_verbose(self):
        result = self.runner.invoke(
            cli,
            [
                "generate",
                "--year",
                "2025",
                "--end-year",
                "2025",
                "--verbose",
                "--holidays-file",
                self.temp_holidays_json,
            ],
        )
        self.assertEqual(result.exit_code, 0)
        with self.assertLogs(level=logging.DEBUG) as cm:
            self.runner.invoke(
                cli,
                [
                    "generate",
                    "--year",
                    "2025",
                    "--end-year",
                    "2025",
                    "--verbose",
                    "--holidays-file",
                    self.temp_holidays_json,
                ],
            )
        self.assertTrue(any("DEBUG" in log for log in cm.output))

    def test_add_holiday_valid(self):
        result = self.runner.invoke(
            cli,
            [
                "add-holiday",
                "Test Holiday",
                "12",
                "1",
                "--holidays-file",
                self.temp_holidays_json,
            ],
        )
        self.assertEqual(result.exit_code, 0)
        holidays = self.load_temp_holidays()
        manual_holidays = holidays.get("manual_holidays", [])
        self.assertIn("Test Holiday", [h["name"] for h in manual_holidays])
        # Clean up
        holidays["manual_holidays"] = [h for h in manual_holidays if h["name"] != "Test Holiday"]
        holidays["approved_holidays"] = [
            h for h in holidays["approved_holidays"] if h != "Test Holiday"
        ]
        self.save_temp_holidays(holidays)

    def test_add_holiday_with_details(self):
        holiday_name = "Test Detailed Holiday Unique"
        result = self.runner.invoke(
            cli,
            [
                "add-holiday",
                holiday_name,
                "12",
                "2",
                "--holidays-file",
                self.temp_holidays_json,
            ],
        )
        self.assertEqual(result.exit_code, 0)
        holidays = self.load_temp_holidays()
        for holiday in holidays["manual_holidays"]:
            if holiday["name"] == holiday_name:
                holiday["description"] = "Test description"
                holiday["reminder_days"] = 1
                break
        self.save_temp_holidays(holidays)

        generate_calendar(2025, 2025, holidays_file=self.temp_holidays_json)
        with open("us_holidays.ics", "rb") as f:
            cal = Calendar.from_ical(f.read())
            found = False
            for event in cal.walk("VEVENT"):
                if event.get("SUMMARY") == holiday_name:
                    self.assertEqual(event.get("DESCRIPTION"), "Test description")
                    self.assertTrue(len(event.subcomponents) > 0)
                    alarm = event.subcomponents[0]
                    self.assertEqual(alarm["ACTION"], "DISPLAY")
                    self.assertEqual(
                        alarm["DESCRIPTION"],
                        f"Reminder: {holiday_name} is tomorrow",
                    )
                    found = True
                    break
            self.assertTrue(found, "Event with alarm not found")
        # Clean up
        holidays["manual_holidays"] = [
            h for h in holidays["manual_holidays"] if h["name"] != holiday_name
        ]
        holidays["approved_holidays"] = [
            h for h in holidays["approved_holidays"] if h != holiday_name
        ]
        self.save_temp_holidays(holidays)

    def test_add_holiday_invalid_date(self):
        result = self.runner.invoke(
            cli,
            [
                "add-holiday",
                "Invalid Holiday",
                "13",
                "1",
                "--holidays-file",
                self.temp_holidays_json,
            ],
        )
        self.assertNotEqual(result.exit_code, 0)

    def test_multiple_day_reminder(self):
        holiday_name = "Test Multi-Day Reminder"
        result = self.runner.invoke(
            cli,
            [
                "add-holiday",
                holiday_name,
                "12",
                "3",
                "--holidays-file",
                self.temp_holidays_json,
            ],
        )
        self.assertEqual(result.exit_code, 0)
        holidays = self.load_temp_holidays()
        for holiday in holidays["manual_holidays"]:
            if holiday["name"] == holiday_name:
                holiday["reminder_days"] = 2
                break
        self.save_temp_holidays(holidays)
        generate_calendar(2025, 2025, holidays_file=self.temp_holidays_json)
        with open("us_holidays.ics", "rb") as f:
            cal = Calendar.from_ical(f.read())
            for event in cal.walk("VEVENT"):
                if event.get("SUMMARY") == holiday_name:
                    alarm = event.subcomponents[0]
                    self.assertEqual(alarm["TRIGGER"].dt, timedelta(days=-2))
                    break
        holidays["manual_holidays"] = [
            h for h in holidays["manual_holidays"] if h["name"] != holiday_name
        ]
        holidays["approved_holidays"] = [
            h for h in holidays["approved_holidays"] if h != holiday_name
        ]
        self.save_temp_holidays(holidays)

    def test_observance_adjustment(self):
        result = self.runner.invoke(
            cli,
            [
                "generate",
                "--year",
                "2026",
                "--end-year",
                "2026",
                "--holidays-file",
                self.temp_holidays_json,
            ],
        )
        self.assertEqual(result.exit_code, 0)
        with open("us_holidays.ics", "rb") as f:
            cal = Calendar.from_ical(f.read())
            for event in cal.walk("VEVENT"):
                if event.get("SUMMARY") == "Independence Day":
                    dtstart = event.get("DTSTART")
                    self.assertEqual(dtstart.dt, datetime(2026, 7, 4).date())  # Always July 4th
                    break
            else:
                self.fail("Independence Day event not found in calendar")

    def test_cache_usage(self):
        cache = load_cache()
        easter_2025 = get_easter_sunday(2025, cache)
        self.assertIn("easter_2025", cache)
        save_cache(cache)
        new_cache = load_cache()
        self.assertEqual(new_cache["easter_2025"], easter_2025.strftime("%Y-%m-%d"))


if __name__ == "__main__":
    unittest.main()
