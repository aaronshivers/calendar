import yaml from "js-yaml";

import { buildCalendar, buildEntries, getYearCount, validateHolidayConfig } from "./calendar.js";

const CALENDAR_BODY_KEY = "calendar:body";
const CALENDAR_GENERATED_AT_KEY = "calendar:generated_at";

export function createWorker({ bundledHolidayYaml, bundledCalendar, bundledGeneratedAt }) {
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

  function getKvNamespace(env) {
    return env.CALENDAR_CACHE ?? null;
  }

  async function storeCalendar(env, generatedAt = new Date().toISOString()) {
    const namespace = getKvNamespace(env);
    if (!namespace) {
      throw new Error("CALENDAR_CACHE binding is not configured");
    }

    const calendar = generateCalendar(env);
    await namespace.put(CALENDAR_BODY_KEY, calendar);
    await namespace.put(CALENDAR_GENERATED_AT_KEY, generatedAt);
    return { body: calendar, generatedAt, source: "kv" };
  }

  async function loadServedCalendar(env) {
    const namespace = getKvNamespace(env);
    if (namespace) {
      const [body, generatedAt] = await Promise.all([
        namespace.get(CALENDAR_BODY_KEY),
        namespace.get(CALENDAR_GENERATED_AT_KEY),
      ]);
      if (body) {
        return { body, generatedAt, source: "kv" };
      }
    }

    return {
      body: bundledCalendar,
      generatedAt: bundledGeneratedAt.trim() || null,
      source: "bundle",
    };
  }

  function calendarResponse(body, generatedAt, source) {
    const headers = new Headers({
      "content-type": "text/calendar; charset=utf-8",
      "cache-control": "public, max-age=86400",
    });

    if (generatedAt) {
      headers.set("x-calendar-generated-at", generatedAt);
    }

    headers.set("x-calendar-source", source);

    return new Response(body, { headers });
  }

  return {
    async fetch(request, env) {
      const url = new URL(request.url);
      if (request.method !== "GET" && request.method !== "HEAD") {
        return new Response("Method Not Allowed", { status: 405 });
      }

      if (url.pathname === "/healthz") {
        return new Response("ok");
      }

      const { body, generatedAt, source } = await loadServedCalendar(env);

      if (request.method === "HEAD") {
        return calendarResponse("", generatedAt, source);
      }

      return calendarResponse(body, generatedAt, source);
    },

    async scheduled(controller, env, ctx) {
      const namespace = getKvNamespace(env);
      if (!namespace) {
        console.warn(
          `Skipping scheduled refresh for ${controller.cron}: CALENDAR_CACHE is not configured`
        );
        return;
      }

      ctx.waitUntil(storeCalendar(env));
    },
  };
}
