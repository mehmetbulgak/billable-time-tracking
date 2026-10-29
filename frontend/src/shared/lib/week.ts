import dayjs, { type Dayjs } from "dayjs";

export interface WeekRange {
  start: Dayjs;
  end: Dayjs;
}

const DAYS_IN_WEEK = 7;

export const weekContaining = (date: Dayjs): WeekRange => {
  const start = date.startOf("day").subtract((date.day() + 6) % DAYS_IN_WEEK, "day");
  return { start, end: start.add(DAYS_IN_WEEK, "day") };
};

export const shiftWeek = (week: WeekRange, weeks: number): WeekRange =>
  weekContaining(week.start.add(weeks * DAYS_IN_WEEK, "day"));

export const weekDays = (week: WeekRange): Dayjs[] =>
  Array.from({ length: DAYS_IN_WEEK }, (_, index) => week.start.add(index, "day"));

export const weekLabel = (week: WeekRange): string => {
  const last = week.end.subtract(1, "day");
  const sameMonth = week.start.month() === last.month();
  return `${week.start.format("MMM D")} – ${last.format(sameMonth ? "D, YYYY" : "MMM D, YYYY")}`;
};

export const isCurrentWeek = (week: WeekRange, now: Dayjs = dayjs()): boolean =>
  !now.isBefore(week.start) && now.isBefore(week.end);
