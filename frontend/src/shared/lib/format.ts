import dayjs from "dayjs";

import type { Currency, Decimal } from "@/shared/api/types";

type NumericLike = Decimal | number | null | undefined;

const SECONDS_PER_MINUTE = 60;
const SECONDS_PER_HOUR = 3600;

const hoursFormatter = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
const compactHoursFormatter = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });
const percentFormatter = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });
const moneyFormatters = new Map<string, Intl.NumberFormat>();

export const toNumber = (value: NumericLike): number => {
  if (value === null || value === undefined || value === "") {
    return 0;
  }
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
};

export const formatHours = (value: NumericLike): string =>
  `${hoursFormatter.format(toNumber(value))} h`;

export const formatHoursOf = (part: NumericLike, whole: NumericLike): string =>
  `${compactHoursFormatter.format(toNumber(part))} / ${compactHoursFormatter.format(toNumber(whole))} h`;

export const formatPercent = (value: NumericLike): string =>
  `${percentFormatter.format(toNumber(value))}%`;

export const formatMoney = (value: NumericLike, currency: Currency): string => {
  let formatter = moneyFormatters.get(currency);
  if (!formatter) {
    formatter = new Intl.NumberFormat("en-US", { style: "currency", currency });
    moneyFormatters.set(currency, formatter);
  }
  return formatter.format(toNumber(value));
};

const pad = (value: number): string => value.toString().padStart(2, "0");

export const formatDuration = (totalSeconds: number): string => {
  const seconds = Math.max(0, Math.floor(totalSeconds));
  const hours = Math.floor(seconds / SECONDS_PER_HOUR);
  const minutes = Math.floor((seconds % SECONDS_PER_HOUR) / SECONDS_PER_MINUTE);
  return `${hours}:${pad(minutes)}:${pad(seconds % SECONDS_PER_MINUTE)}`;
};

export const formatDurationShort = (totalSeconds: number): string => {
  const minutes = Math.max(0, Math.round(totalSeconds / SECONDS_PER_MINUTE));
  const hours = Math.floor(minutes / 60);
  return hours > 0 ? `${hours}h ${pad(minutes % 60)}m` : `${minutes}m`;
};

export const formatDate = (value: string | null | undefined): string =>
  value ? dayjs(value).format("MMM D, YYYY") : "—";

export const formatTime = (value: string): string => dayjs(value).format("HH:mm");

export const formatTimeRange = (start: string, end: string | null): string =>
  `${formatTime(start)} – ${end ? formatTime(end) : "now"}`;

export const formatPeriodRange = (start: string, end: string): string =>
  `${dayjs(start).format("MMM D")} – ${dayjs(end).format("MMM D, YYYY")}`;
