import type { TimeEntry } from "@/shared/api/types";

const byStartTime = (left: TimeEntry, right: TimeEntry): number =>
  left.started_at.localeCompare(right.started_at);

export function mergeActiveTimer(timers: readonly TimeEntry[], entry: TimeEntry): TimeEntry[] {
  const others = timers.filter((timer) => timer.id !== entry.id && timer.user.id !== entry.user.id);
  return entry.is_running ? [...others, entry].sort(byStartTime) : others;
}
