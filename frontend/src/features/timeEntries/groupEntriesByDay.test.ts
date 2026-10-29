import dayjs from "dayjs";
import { describe, expect, it } from "vitest";

import { buildEntry } from "@/test/fixtures";

import { entrySeconds, groupEntriesByDay } from "./groupEntriesByDay";

describe("groupEntriesByDay", () => {
  it("groups entries per local day, newest day first", () => {
    const entries = [
      buildEntry({ id: 1, started_at: "2026-03-02T09:00:00", duration_seconds: 3600 }),
      buildEntry({ id: 2, started_at: "2026-03-03T09:00:00", duration_seconds: 1800 }),
      buildEntry({
        id: 3,
        started_at: "2026-03-02T14:00:00",
        duration_seconds: 900,
        is_billable: false,
      }),
    ];

    const groups = groupEntriesByDay(entries);

    expect(groups.map((group) => group.date)).toEqual(["2026-03-03", "2026-03-02"]);
    expect(groups[1]?.entries.map((entry) => entry.id)).toEqual([3, 1]);
    expect(groups[1]?.totalSeconds).toBe(4500);
    expect(groups[1]?.billableSeconds).toBe(3600);
  });

  it("counts running entries up to now", () => {
    const startedAt = "2026-03-02T09:00:00";
    const running = buildEntry({
      started_at: startedAt,
      ended_at: null,
      is_running: true,
      duration_seconds: 0,
    });
    const now = dayjs(startedAt).add(25, "minute").valueOf();

    expect(entrySeconds(running, now)).toBe(25 * 60);
    expect(groupEntriesByDay([running], now)[0]?.totalSeconds).toBe(25 * 60);
  });

  it("returns no groups for no entries", () => {
    expect(groupEntriesByDay([])).toEqual([]);
  });
});
