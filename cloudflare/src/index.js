import yaml from "js-yaml";
import bundledHolidayYaml from "../../src/generate_calendar/holidays.yaml";
import { buildCalendar, buildEntries, getYearCount, validateHolidayConfig } from "./calendar.js";

function loadHolidayConfig() {
  const config = yaml.load(bundledHolidayYaml);
  validateHolidayConfig(config);
  return config;
}

function generateCalendar(env) {
  const config = loadHolidayConfig();
  const currentYear = new Date().getUTCFullYear();
  const endYear = currentYear + getYearCount(env.YEAR_COUNT) - 1;
  return buildCalendar(buildEntries(config, currentYear, endYear));
}

function calendarResponse(body, generatedAt) {
  const headers = new Headers({
    "content-type": "text/calendar; charset=utf-8",
    "cache-control": "public, max-age=3600",
  });

  if (generatedAt) {
    headers.set("x-calendar-generated-at", generatedAt);
  }

  return new Response(body, { headers });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    if (url.pathname === "/healthz") {
      return new Response("ok");
    }

    const generatedAt = new Date().toISOString();
    const calendar = generateCalendar(env);

    if (request.method === "HEAD") {
      return calendarResponse("", generatedAt);
    }

    return calendarResponse(calendar, generatedAt);
  },
};
