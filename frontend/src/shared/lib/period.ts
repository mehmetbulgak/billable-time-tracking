import dayjs, { type Dayjs } from "dayjs";

const PERIOD_FORMAT = "YYYY-MM";
const PERIOD_PATTERN = /^\d{4}-(0[1-9]|1[0-2])$/;

export type Period = string;

const firstDay = (period: Period): Dayjs => dayjs(`${period}-01`);

export const isPeriod = (value: string | null | undefined): value is Period =>
  typeof value === "string" && PERIOD_PATTERN.test(value);

export const currentPeriod = (now: Dayjs = dayjs()): Period => now.format(PERIOD_FORMAT);

export const shiftPeriod = (period: Period, months: number): Period =>
  firstDay(period).add(months, "month").format(PERIOD_FORMAT);

export const periodLabel = (period: Period): string => firstDay(period).format("MMMM YYYY");

export const isFuturePeriod = (period: Period, now: Dayjs = dayjs()): boolean =>
  period > currentPeriod(now);

export const recentPeriods = (count: number, now: Dayjs = dayjs()): Period[] =>
  Array.from({ length: count }, (_, index) => shiftPeriod(currentPeriod(now), -index));
