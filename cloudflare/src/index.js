import yaml from "js-yaml";

const DEFAULT_CACHE_KEY = "us_holidays.ics";
const DEFAULT_YEAR_COUNT = 10;
const OBSERVED_HOLIDAYS = new Set([
  "New Year's Day",
  "Independence Day",
  "Veterans Day",
  "Christmas Day",
]);

function getCacheKey(env) {
  return env.CALENDAR_CACHE_KEY || DEFAULT_CACHE_KEY;
}

function getYearCount(env) {
  const parsed = Number.parseInt(env.YEAR_COUNT || String(DEFAULT_YEAR_COUNT), 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_YEAR_COUNT;
}

function utcDate(year, month, day) {
  return new Date(Date.UTC(year, month - 1, day));
}

function formatDate(date) {
  return date.toISOString().slice(0, 10).replaceAll("-", "");
}

function formatIsoDate(date) {
  return date.toISOString().slice(0, 10);
}

function pythonWeekday(date) {
  return (date.getUTCDay() + 6) % 7;
}

function getNthWeekday(year, month, weekday, nth) {
  const firstDay = utcDate(year, month, 1);
  const offset = (weekday - pythonWeekday(firstDay) + 7) % 7;
  return utcDate(year, month, 1 + offset + (nth - 1) * 7);
}

function getLastWeekday(year, month, weekday) {
  const nextMonth = month === 12 ? 1 : month + 1;
  const nextYear = month === 12 ? year + 1 : year;
  const lastDay = new Date(Date.UTC(nextYear, nextMonth - 1, 0));
  const daysToSubtract = (pythonWeekday(lastDay) - weekday + 7) % 7;
  return utcDate(
    lastDay.getUTCFullYear(),
    lastDay.getUTCMonth() + 1,
    lastDay.getUTCDate() - daysToSubtract
  );
}

function getEasterSunday(year) {
  const a = year % 19;
  const b = Math.floor(year / 100);
  const c = year % 100;
  const d = Math.floor(b / 4);
  const e = b % 4;
  const f = Math.floor((b + 8) / 25);
  const g = Math.floor((b - f + 1) / 3);
  const h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4);
  const k = c % 4;
  const offsetL = (32 + 2 * e + 2 * i - h - k) % 7;
  const m = Math.floor((a + 11 * h + 22 * offsetL) / 451);
  const month = Math.floor((h + offsetL - 7 * m + 114) / 31);
  const day = ((h + offsetL - 7 * m + 114) % 31) + 1;
  return utcDate(year, month, day);
}

function adjustForObservance(date) {
  if (date.getUTCDay() === 6) {
    return utcDate(date.getUTCFullYear(), date.getUTCMonth() + 1, date.getUTCDate() - 1);
  }

  if (date.getUTCDay() === 0) {
    return utcDate(date.getUTCFullYear(), date.getUTCMonth() + 1, date.getUTCDate() + 1);
  }

  return date;
}

function validateHolidayConfig(config) {
  for (const section of ["manual_holidays", "calculated_holidays", "federal_holidays"]) {
    if (!Array.isArray(config?.[section])) {
      throw new Error(`Holiday config is missing section: ${section}`);
    }
  }
}

async function loadHolidayConfig(env) {
  const response = await fetch(env.HOLIDAYS_YAML_URL, {
    headers: {
      "User-Agent": "us-holidays-calendar-worker",
    },
  });

  if (!response.ok) {
    throw new Error(`Unable to fetch holidays.yaml: ${response.status} ${response.statusText}`);
  }

  const text = await response.text();
  const config = yaml.load(text);
  validateHolidayConfig(config);
  return config;
}

function buildEntries(config, startYear, endYear) {
  const entries = [];
  const seen = new Set();

  for (let year = startYear; year <= endYear; year += 1) {
    for (const holiday of config.federal_holidays) {
      let date;
      if (holiday.day) {
        date = utcDate(year, holiday.month, holiday.day);
      } else if (holiday.last) {
        date = getLastWeekday(year, holiday.month, holiday.weekday);
      } else {
        date = getNthWeekday(year, holiday.month, holiday.weekday, holiday.nth);
      }

      if (OBSERVED_HOLIDAYS.has(holiday.name)) {
        date = adjustForObservance(date);
      }

      const dedupeKey = `${holiday.name}:${formatIsoDate(date)}`;
      if (!seen.has(dedupeKey)) {
        seen.add(dedupeKey);
        entries.push({ name: holiday.name, date });
      }
    }

    for (const holiday of config.manual_holidays) {
      const date = utcDate(year, holiday.month, holiday.day);
      const dedupeKey = `${holiday.name}:${formatIsoDate(date)}`;
      if (!seen.has(dedupeKey)) {
        seen.add(dedupeKey);
        entries.push({ name: holiday.name, date });
      }
    }

    for (const holiday of config.calculated_holidays) {
      const date =
        holiday.type === "easter"
          ? getEasterSunday(year)
          : getNthWeekday(year, holiday.month, holiday.weekday, holiday.nth);
      const dedupeKey = `${holiday.name}:${formatIsoDate(date)}`;
      if (!seen.has(dedupeKey)) {
        seen.add(dedupeKey);
        entries.push({ name: holiday.name, date });
      }
    }
  }

  return entries;
}

function escapeIcsText(value) {
  return value
    .replaceAll("\\", "\\\\")
    .replaceAll(";", "\\;")
    .replaceAll(",", "\\,")
    .replaceAll("\n", "\\n");
}

function buildCalendar(entries) {
  const lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID://US Holidays Calendar//Cloudflare//"];

  for (const entry of entries) {
    const isoDate = formatIsoDate(entry.date);
    lines.push("BEGIN:VEVENT");
    lines.push(`SUMMARY:${escapeIcsText(entry.name)}`);
    lines.push(`DTSTART;VALUE=DATE:${formatDate(entry.date)}`);
    lines.push(`UID:${isoDate}-${escapeIcsText(entry.name)}@us-holidays-calendar`);
    lines.push("END:VEVENT");
  }

  lines.push("END:VCALENDAR");
  return `${lines.join("\r\n")}\r\n`;
}

async function generateCalendar(env) {
  const config = await loadHolidayConfig(env);
  const currentYear = new Date().getUTCFullYear();
  const endYear = currentYear + getYearCount(env) - 1;
  const ics = buildCalendar(buildEntries(config, currentYear, endYear));
  await env.CALENDAR_CACHE.put(getCacheKey(env), ics);
  return ics;
}

function calendarResponse(body, generatedAt = null) {
  const headers = new Headers({
    "content-type": "text/calendar; charset=utf-8",
    "cache-control": "public, max-age=300",
  });

  if (generatedAt) {
    headers.set("x-calendar-generated-at", generatedAt);
  }

  return new Response(body, { headers });
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    if (url.pathname === "/healthz") {
      return new Response("ok");
    }

    const cacheKey = getCacheKey(env);
    let calendar = await env.CALENDAR_CACHE.get(cacheKey);

    if (!calendar) {
      calendar = await generateCalendar(env);
    }

    if (request.method === "HEAD") {
      return calendarResponse("", new Date().toISOString());
    }

    ctx.waitUntil(Promise.resolve());
    return calendarResponse(calendar, new Date().toISOString());
  },

  async scheduled(_controller, env, ctx) {
    ctx.waitUntil(generateCalendar(env));
  },
};
