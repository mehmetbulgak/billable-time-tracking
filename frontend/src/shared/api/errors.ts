import { isFetchBaseQueryError, isRecord } from "./guards";

const DEFAULT_MESSAGE = "Something went wrong. Please try again.";

const humanize = (field: string): string => {
  const words = field.replaceAll("_", " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
};

const firstMessage = (value: unknown): string | null => {
  if (typeof value === "string") {
    return value;
  }
  if (Array.isArray(value)) {
    const [first] = value as unknown[];
    return firstMessage(first);
  }
  return null;
};

export function getFieldErrors(error: unknown): Record<string, string> {
  if (!isFetchBaseQueryError(error) || !isRecord(error.data)) {
    return {};
  }
  const fieldErrors: Record<string, string> = {};
  for (const [field, value] of Object.entries(error.data)) {
    const message = firstMessage(value);
    if (message && field !== "detail" && field !== "code") {
      fieldErrors[field] = message;
    }
  }
  return fieldErrors;
}

export function getErrorMessage(error: unknown, fallback = DEFAULT_MESSAGE): string {
  if (isFetchBaseQueryError(error)) {
    if (error.status === "FETCH_ERROR") {
      return "Cannot reach the server. Check your connection.";
    }
    if (isRecord(error.data)) {
      if (typeof error.data.detail === "string") {
        return error.data.detail;
      }
      const [field, message] = Object.entries(getFieldErrors(error))[0] ?? [];
      if (field && message) {
        return field === "non_field_errors" ? message : `${humanize(field)}: ${message}`;
      }
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return fallback;
}

export function getErrorCode(error: unknown): string | null {
  if (isFetchBaseQueryError(error) && isRecord(error.data) && typeof error.data.code === "string") {
    return error.data.code;
  }
  return null;
}
