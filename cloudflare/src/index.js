import bundledHolidayYaml from "../../src/generate_calendar/holidays.yaml";
import bundledCalendar from "../generated/us_holidays.ics";
import bundledGeneratedAt from "../generated/generated_at.txt";
import { createWorker } from "./runtime.js";

export default createWorker({
  bundledHolidayYaml,
  bundledCalendar,
  bundledGeneratedAt,
});
