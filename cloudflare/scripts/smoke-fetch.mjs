import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { createWorker } from "../src/runtime.js";

class InMemoryKvNamespace {
  constructor() {
    this.values = new Map();
  }

  async get(key) {
    return this.values.get(key) ?? null;
  }

  async put(key, value) {
    this.values.set(key, value);
  }
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

const repoRoot = resolve(import.meta.dirname, "../..");
const worker = createWorker({
  bundledHolidayYaml: readFileSync(resolve(repoRoot, "src/generate_calendar/holidays.yaml"), "utf8"),
  bundledCalendar: readFileSync(resolve(repoRoot, "cloudflare/generated/us_holidays.ics"), "utf8"),
  bundledGeneratedAt: readFileSync(resolve(repoRoot, "cloudflare/generated/generated_at.txt"), "utf8"),
});

const kv = new InMemoryKvNamespace();
const env = {
  CALENDAR_CACHE: kv,
  YEAR_COUNT: "2",
};

const bundleResponse = await worker.fetch(new Request("https://calendar.corncob.app"), env);
assert(bundleResponse.status === 200, "Expected GET / to succeed");
assert(
  bundleResponse.headers.get("content-type") === "text/calendar; charset=utf-8",
  "Expected calendar content type"
);
assert(bundleResponse.headers.get("x-calendar-source") === "bundle", "Expected bundle fallback");
assert((await bundleResponse.text()).includes("BEGIN:VCALENDAR"), "Expected iCalendar body");

const headResponse = await worker.fetch(new Request("https://calendar.corncob.app", { method: "HEAD" }), env);
assert(headResponse.status === 200, "Expected HEAD / to succeed");
assert((await headResponse.text()) === "", "Expected empty HEAD body");

const scheduledTasks = [];
await worker.scheduled(
  { cron: "0 0 1 * *" },
  env,
  {
    waitUntil(promise) {
      scheduledTasks.push(promise);
    },
  }
);
await Promise.all(scheduledTasks);

const kvResponse = await worker.fetch(new Request("https://calendar.corncob.app"), env);
assert(kvResponse.headers.get("x-calendar-source") === "kv", "Expected KV-backed response after schedule");
assert((await kvResponse.text()).includes("BEGIN:VCALENDAR"), "Expected stored iCalendar body");

const healthResponse = await worker.fetch(new Request("https://calendar.corncob.app/healthz"), env);
assert((await healthResponse.text()) === "ok", "Expected healthz response");

console.log("Worker smoke test passed.");
