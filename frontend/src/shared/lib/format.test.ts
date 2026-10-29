import { describe, expect, it } from "vitest";

import {
  formatDuration,
  formatDurationShort,
  formatHours,
  formatHoursOf,
  formatMoney,
  formatPercent,
  toNumber,
} from "./format";

describe("toNumber", () => {
  it.each([
    ["12.50", 12.5],
    [7, 7],
    [null, 0],
    [undefined, 0],
    ["", 0],
    ["not-a-number", 0],
  ])("converts %s to %s", (input, expected) => {
    expect(toNumber(input)).toBe(expected);
  });
});

describe("formatters", () => {
  it("formats hours with up to two decimals", () => {
    expect(formatHours("12.50")).toBe("12.5 h");
    expect(formatHours("180.00")).toBe("180 h");
    expect(formatHours("0.33")).toBe("0.33 h");
  });

  it("formats a share of hours compactly", () => {
    expect(formatHoursOf("124.51", "137.14")).toBe("124.5 / 137.1 h");
    expect(formatHoursOf(0, "51.51")).toBe("0 / 51.5 h");
  });

  it("formats money in the invoice currency", () => {
    expect(formatMoney("19800.00", "USD")).toBe("$19,800.00");
    expect(formatMoney("16000", "EUR")).toBe("€16,000.00");
  });

  it("formats percentages", () => {
    expect(formatPercent("80.00")).toBe("80%");
    expect(formatPercent("96.034")).toBe("96%");
  });

  it("formats running durations as a clock", () => {
    expect(formatDuration(0)).toBe("0:00:00");
    expect(formatDuration(3909)).toBe("1:05:09");
    expect(formatDuration(-5)).toBe("0:00:00");
  });

  it("formats compact durations", () => {
    expect(formatDurationShort(45 * 60)).toBe("45m");
    expect(formatDurationShort(5400)).toBe("1h 30m");
    expect(formatDurationShort(8 * 3600 + 5 * 60)).toBe("8h 05m");
  });
});
