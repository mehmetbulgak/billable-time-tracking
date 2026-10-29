import dayjs from "dayjs";
import { describe, expect, it } from "vitest";

import { isCurrentWeek, shiftWeek, weekContaining, weekDays, weekLabel } from "./week";

describe("week helpers", () => {
  it("starts weeks on Monday", () => {
    const week = weekContaining(dayjs("2026-10-29T15:00:00"));

    expect(week.start.format("YYYY-MM-DD ddd")).toBe("2026-10-26 Mon");
    expect(week.end.format("YYYY-MM-DD")).toBe("2026-11-02");
  });

  it("treats Sunday as the last day of the week", () => {
    expect(weekContaining(dayjs("2026-11-01T10:00:00")).start.format("YYYY-MM-DD")).toBe(
      "2026-10-26",
    );
  });

  it("lists seven days and shifts by whole weeks", () => {
    const week = weekContaining(dayjs("2026-10-29"));

    expect(weekDays(week)).toHaveLength(7);
    expect(shiftWeek(week, -1).start.format("YYYY-MM-DD")).toBe("2026-10-19");
  });

  it("labels weeks spanning two months", () => {
    expect(weekLabel(weekContaining(dayjs("2026-10-29")))).toBe("Oct 26 – Nov 1, 2026");
    expect(weekLabel(weekContaining(dayjs("2026-10-14")))).toBe("Oct 12 – 18, 2026");
  });

  it("detects the current week", () => {
    const now = dayjs("2026-10-29T09:00:00");

    expect(isCurrentWeek(weekContaining(now), now)).toBe(true);
    expect(isCurrentWeek(shiftWeek(weekContaining(now), -1), now)).toBe(false);
  });
});
