from pathlib import Path

from flask import Flask, Response, abort, send_file

from generate_calendar import DEFAULT_OUTPUT_FILE

app = Flask(__name__)
OUTPUT_FILE = Path(DEFAULT_OUTPUT_FILE)


@app.get("/")  # type: ignore[misc]
def index() -> Response:
    if not OUTPUT_FILE.exists():
        abort(404, description="Calendar file not found. Run `generate_calendar` first.")
    return send_file(OUTPUT_FILE, mimetype="text/calendar")


if __name__ == "__main__":
    app.run()
