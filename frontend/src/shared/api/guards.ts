import type { FetchBaseQueryError } from "@reduxjs/toolkit/query";

import type { AccessSession } from "./types";

export const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

export const isAccessSession = (value: unknown): value is AccessSession =>
  isRecord(value) && typeof value.access === "string" && typeof value.csrf_token === "string";

export const isFetchBaseQueryError = (error: unknown): error is FetchBaseQueryError =>
  isRecord(error) && "status" in error;
