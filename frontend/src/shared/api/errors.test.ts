import { describe, expect, it } from "vitest";

import { getErrorCode, getErrorMessage, getFieldErrors } from "./errors";

describe("API error helpers", () => {
  it("prefers the detail message of domain errors", () => {
    const error = {
      status: 409,
      data: { detail: "This entry overlaps another one.", code: "overlapping_entry" },
    };

    expect(getErrorMessage(error)).toBe("This entry overlaps another one.");
    expect(getErrorCode(error)).toBe("overlapping_entry");
  });

  it("summarizes the first field error", () => {
    const error = {
      status: 400,
      data: { ends_on: ["The end date must be on or after the start date."] },
    };

    expect(getErrorMessage(error)).toBe(
      "Ends on: The end date must be on or after the start date.",
    );
    expect(getFieldErrors(error)).toEqual({
      ends_on: "The end date must be on or after the start date.",
    });
  });

  it("explains network failures", () => {
    expect(getErrorMessage({ status: "FETCH_ERROR", error: "TypeError" })).toMatch(/Cannot reach/);
  });

  it("falls back for unknown errors", () => {
    expect(getErrorMessage(undefined, "Fallback")).toBe("Fallback");
    expect(getErrorCode(new Error("boom"))).toBeNull();
  });
});
