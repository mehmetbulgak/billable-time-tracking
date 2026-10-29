import type { FetchBaseQueryError } from "@reduxjs/toolkit/query";

import type { TokenPair } from "./types";

export const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

export const isTokenPair = (value: unknown): value is TokenPair =>
  isRecord(value) && typeof value.access === "string" && typeof value.refresh === "string";

export const isFetchBaseQueryError = (error: unknown): error is FetchBaseQueryError =>
  isRecord(error) && "status" in error;
