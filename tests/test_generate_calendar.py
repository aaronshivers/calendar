import unittest
from datetime import datetime
import json
from generate_calendar import (
    get_easter_sunday,
    get_nth_weekday,
    get_last_weekday,
    get_federal_holidays,
    load_cache,
)


class TestHolidayCalculations(unittest.TestCase):
    def setUp(self):
        # Load holidays.json for federal holidays
        with open("src/holidays.json", "r") as f:
            self.holiday_config = json.load(f)
        self.federal_holidays = self.holiday_config["federal_holidays"]
        self.cache = load_cache()

    def test_easter_sunday(self):
        # Test Easter Sunday for 2025 (known date: April 20, 2025)
        easter_2025 = get_easter_sunday(2025, self.cache)
        self.assertEqual(easter_2025, datetime(2025, 4, 20).date())

        # Test Easter Sunday for 2026 (known date: April 5, 2026)
        easter_2026 = get_easter_sunday(2026, self.cache)
        self.assertEqual(easter_2026, datetime(2026, 4, 5).date())

    def test_nth_weekday(self):
        # Test 3rd Monday in January 2025 (MLK Jr. Day: Jan 20, 2025)
        mlk_2025 = get_nth_weekday(2025, 1, 0, 3)
        self.assertEqual(mlk_2025, datetime(2025, 1, 20).date())

        # Test 4th Thursday in November 2025 (Thanksgiving: Nov 27, 2025)
        thanksgiving_2025 = get_nth_weekday(2025, 11, 3, 4)
        self.assertEqual(thanksgiving_2025, datetime(2025, 11, 27).date())

    def test_last_weekday(self):
        # Test last Monday in May 2025 (Memorial Day: May 26, 2025)
        memorial_2025 = get_last_weekday(2025, 5, 0)
        self.assertEqual(memorial_2025, datetime(2025, 5, 26).date())

    def test_federal_holidays(self):
        # Test federal holidays for 2025
        holidays_2025 = get_federal_holidays(2025, self.federal_holidays)
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
        for holiday in holidays_2025:
            if holiday["name"] in expected_dates:
                self.assertEqual(holiday["date"], expected_dates[holiday["name"]])


if __name__ == "__main__":
    unittest.main()
