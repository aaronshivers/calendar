from flask import Flask, send_file
from generate_calendar import generate_calendar

app = Flask(__name__)


def generate_calendar_file():
    # Assuming some default values for start_year and end_year
    start_year = 2025
    end_year = 2026
    generate_calendar(start_year, end_year)


# Generate the calendar before serving
generate_calendar_file()

# Serve the generated calendar file
app.add_url_rule("/", "index", lambda: send_file("us_holidays.ics", as_attachment=True))

if __name__ == "__main__":
    app.run()
