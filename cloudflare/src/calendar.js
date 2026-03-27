export const DEFAULT_YEAR_COUNT = 2;

export function getYearCount(rawValue, defaultYearCount = DEFAULT_YEAR_COUNT) {
  const parsed = Number.parseInt(rawValue ?? String(defaultYearCount), 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : defaultYearCount;
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

function buildFixedDate(year, month, day) {
  const date = utcDate(year, month, day);
  return date.getUTCMonth() === month - 1 && date.getUTCDate() === day ? date : null;
}

function isDateInRange(date, startDate, endDate) {
  return date >= startDate && date <= endDate;
}

export function validateHolidayConfig(config) {
  for (const section of ["manual_holidays", "calculated_holidays", "federal_holidays"]) {
    if (!Array.isArray(config?.[section])) {
      throw new Error(`Holiday config is missing section: ${section}`);
    }
  }

  for (const section of ["manual_holidays", "calculated_holidays", "federal_holidays"]) {
    for (const holiday of config[section]) {
      if ("enabled" in holiday && typeof holiday.enabled !== "boolean") {
        throw new Error(`Holiday enabled flag must be true or false: ${holiday.name}`);
      }
    }
  }

  for (const holiday of config.federal_holidays) {
    if (holiday.observed && !("day" in holiday)) {
      throw new Error(`Observed federal holiday must use a fixed date: ${holiday.name}`);
    }
  }
}

export function buildEntries(config, startYear, endYear) {
  const entries = [];
  const seen = new Set();
  const startDate = utcDate(startYear, 1, 1);
  const endDate = utcDate(endYear, 12, 31);

  for (let year = startYear - 1; year <= endYear + 1; year += 1) {
    for (const holiday of config.federal_holidays) {
      if (holiday.enabled === false) {
        continue;
      }

      let date;
      if ("day" in holiday) {
        date = utcDate(year, holiday.month, holiday.day);
      } else if ("last" in holiday) {
        date = getLastWeekday(year, holiday.month, holiday.weekday);
      } else {
        date = getNthWeekday(year, holiday.month, holiday.weekday, holiday.nth);
      }

      if (holiday.observed) {
        date = adjustForObservance(date);
      }

      if (!isDateInRange(date, startDate, endDate)) {
        continue;
      }

      const dedupeKey = `${holiday.name}:${formatIsoDate(date)}`;
      if (!seen.has(dedupeKey)) {
        seen.add(dedupeKey);
        entries.push({ name: holiday.name, date });
      }
    }

    for (const holiday of config.manual_holidays) {
      if (holiday.enabled === false) {
        continue;
      }

      const date = buildFixedDate(year, holiday.month, holiday.day);
      if (!date || !isDateInRange(date, startDate, endDate)) {
        continue;
      }

      const dedupeKey = `${holiday.name}:${formatIsoDate(date)}`;
      if (!seen.has(dedupeKey)) {
        seen.add(dedupeKey);
        entries.push({ name: holiday.name, date });
      }
    }

    for (const holiday of config.calculated_holidays) {
      if (holiday.enabled === false) {
        continue;
      }

      const date =
        holiday.type === "easter"
          ? getEasterSunday(year)
          : getNthWeekday(year, holiday.month, holiday.weekday, holiday.nth);
      if (!isDateInRange(date, startDate, endDate)) {
        continue;
      }

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

export function buildCalendar(entries) {
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
