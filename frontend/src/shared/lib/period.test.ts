import dayjs from "dayjs";
import { describe, expect, it } from "vitest";

import {
  currentPeriod,
  isFuturePeriod,
  isPeriod,
  periodLabel,
  recentPeriods,
  shiftPeriod,
} from "./period";

const now = dayjs("2026-10-29T12:00:00");

describe("period helpers", () => {
  it("validates YYYY-MM periods", () => {
    expect(isPeriod("2026-10")).toBe(true);
    expect(isPeriod("2026-13")).toBe(false);
    expect(isPeriod("2026-1")).toBe(false);
    expect(isPeriod(null)).toBe(false);
  });

  it("shifts across year boundaries", () => {
    expect(shiftPeriod("2026-01", -1)).toBe("2025-12");
    expect(shiftPeriod("2025-12", 1)).toBe("2026-01");
  });

  it("knows the current and future periods", () => {
    expect(currentPeriod(now)).toBe("2026-10");
    expect(isFuturePeriod("2026-11", now)).toBe(true);
    expect(isFuturePeriod("2026-10", now)).toBe(false);
  });

  it("lists recent periods newest first", () => {
    expect(recentPeriods(3, now)).toEqual(["2026-10", "2026-09", "2026-08"]);
  });

  it("renders a readable label", () => {
    expect(periodLabel("2026-03")).toBe("March 2026");
  });
});
