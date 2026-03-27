import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";
import yaml from "js-yaml";

import { buildEntries, validateHolidayConfig } from "../src/calendar.js";

const repoRoot = resolve(import.meta.dirname, "../..");
const holidaysPath = resolve(repoRoot, "src/generate_calendar/holidays.yaml");
const holidaysText = readFileSync(holidaysPath, "utf8");
const holidaysConfig = yaml.load(holidaysText);

validateHolidayConfig(holidaysConfig);

const startYear = 2025;
const endYear = 2027;
const jsEntries = buildEntries(holidaysConfig, startYear, endYear).map((entry) => ({
  name: entry.name,
  date: entry.date.toISOString().slice(0, 10),
}));

const pythonResult = spawnSync(
  "poetry",
  [
    "run",
    "python",
    "-c",
    [
      "import json",
      "from generate_calendar import build_holiday_entries",
      `entries = build_holiday_entries(${startYear}, ${endYear})`,
      "print(json.dumps([{'name': entry['name'], 'date': entry['date'].isoformat()} for entry in entries]))",
    ].join("; "),
  ],
  {
    cwd: repoRoot,
    encoding: "utf8",
  }
);

if (pythonResult.status !== 0) {
  process.stderr.write(pythonResult.stderr);
  process.exit(pythonResult.status ?? 1);
}

const pythonEntries = JSON.parse(pythonResult.stdout);

if (JSON.stringify(jsEntries) !== JSON.stringify(pythonEntries)) {
  process.stderr.write("Worker and Python holiday generation are out of sync.\n");
  process.stderr.write(`JS entries: ${JSON.stringify(jsEntries, null, 2)}\n`);
  process.stderr.write(`Python entries: ${JSON.stringify(pythonEntries, null, 2)}\n`);
  process.exit(1);
}

process.stdout.write(
  `Parity check passed for ${startYear}-${endYear} with ${jsEntries.length} holiday entries.\n`
);
