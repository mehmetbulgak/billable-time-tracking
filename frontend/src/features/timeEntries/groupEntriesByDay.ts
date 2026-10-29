import dayjs from "dayjs";

import type { TimeEntry } from "@/shared/api/types";

export interface DayGroup {
  date: string;
  entries: TimeEntry[];
  totalSeconds: number;
  billableSeconds: number;
}

export const entrySeconds = (entry: TimeEntry, now: number = Date.now()): number =>
  entry.ended_at === null
    ? Math.max(0, (now - dayjs(entry.started_at).valueOf()) / 1000)
    : entry.duration_seconds;

export function groupEntriesByDay(
  entries: readonly TimeEntry[],
  now: number = Date.now(),
): DayGroup[] {
  const groups = new Map<string, DayGroup>();
  for (const entry of entries) {
    const date = dayjs(entry.started_at).format("YYYY-MM-DD");
    const group = groups.get(date) ?? { date, entries: [], totalSeconds: 0, billableSeconds: 0 };
    const seconds = entrySeconds(entry, now);
    group.entries.push(entry);
    group.totalSeconds += seconds;
    group.billableSeconds += entry.is_billable ? seconds : 0;
    groups.set(date, group);
  }
  return [...groups.values()]
    .map((group) => ({
      ...group,
      entries: [...group.entries].sort((left, right) =>
        right.started_at.localeCompare(left.started_at),
      ),
    }))
    .sort((left, right) => right.date.localeCompare(left.date));
}
