import dayjs from "dayjs";
import { describe, expect, it } from "vitest";

import {
  contractSchema,
  emptyContractForm,
  toContractInput,
  type ContractFormValues,
} from "./contractSchema";

const retainerForm = (overrides: Partial<ContractFormValues> = {}): ContractFormValues => ({
  ...emptyContractForm(),
  starts_on: dayjs("2026-01-01"),
  monthly_fee: "19800",
  included_hours: "180",
  overage_rate: "125.50",
  rollover_cap_hours: "15",
  ...overrides,
});

describe("contractSchema", () => {
  it("requires the terms of the selected billing model", () => {
    const result = contractSchema.safeParse(retainerForm({ overage_rate: "" }));

    expect(result.success).toBe(false);
    expect(result.error?.issues.map((issue) => issue.path.join("."))).toEqual(["overage_rate"]);
  });

  it("ignores fields that the billing model does not use", () => {
    const result = contractSchema.safeParse({
      ...emptyContractForm(),
      billing_model: "hourly",
      hourly_rate: "115",
    });

    expect(result.success).toBe(true);
  });

  it("rejects malformed amounts and inverted dates", () => {
    const result = contractSchema.safeParse(
      retainerForm({ monthly_fee: "12.345", ends_on: dayjs("2025-12-31") }),
    );

    expect(result.error?.issues.map((issue) => issue.path.join(".")).sort()).toEqual([
      "ends_on",
      "monthly_fee",
    ]);
  });
});

describe("toContractInput", () => {
  it("serializes dates and drops terms of other billing models", () => {
    const input = toContractInput(7, { ...retainerForm(), hourly_rate: "999" });

    expect(input).toEqual({
      client: 7,
      billing_model: "retainer",
      starts_on: "2026-01-01",
      ends_on: null,
      hourly_rate: null,
      monthly_fee: "19800",
      included_hours: "180",
      overage_rate: "125.50",
      rollover_cap_hours: "15",
      rounding_increment_minutes: 15,
    });
  });

  it("does not send a rollover cap for non-retainer contracts", () => {
    const input = toContractInput(7, {
      ...emptyContractForm(),
      billing_model: "fixed_fee",
      monthly_fee: "16000",
      rollover_cap_hours: "10",
    });

    expect(input.rollover_cap_hours).toBe("0");
    expect(input.included_hours).toBeNull();
  });
});
