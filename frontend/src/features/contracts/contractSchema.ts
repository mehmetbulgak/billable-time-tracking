import dayjs, { type Dayjs } from "dayjs";
import { z } from "zod";

import type { BillingModel, RoundingIncrement } from "@/shared/api/types";

import type { ContractInput } from "./contractsApi";

const amount = z
  .string()
  .trim()
  .refine((value) => value === "" || (/^\d+(\.\d{1,2})?$/.test(value) && Number(value) >= 0), {
    message: "Enter a positive amount with up to two decimals.",
  });

const REQUIRED_FIELDS: Record<BillingModel, readonly AmountField[]> = {
  hourly: ["hourly_rate"],
  retainer: ["monthly_fee", "included_hours", "overage_rate"],
  fixed_fee: ["monthly_fee"],
};

type AmountField = "hourly_rate" | "monthly_fee" | "included_hours" | "overage_rate";

export const contractSchema = z
  .object({
    billing_model: z.enum(["hourly", "retainer", "fixed_fee"]),
    starts_on: z.custom<Dayjs>((value) => dayjs.isDayjs(value) && value.isValid(), {
      message: "Choose a start date.",
    }),
    ends_on: z.custom<Dayjs | null>(
      (value) => value === null || (dayjs.isDayjs(value) && value.isValid()),
    ),
    hourly_rate: amount,
    monthly_fee: amount,
    included_hours: amount,
    overage_rate: amount,
    rollover_cap_hours: amount,
    rounding_increment_minutes: z.union([
      z.literal(1),
      z.literal(6),
      z.literal(15),
      z.literal(30),
      z.literal(60),
    ]),
  })
  .superRefine((values, context) => {
    for (const field of REQUIRED_FIELDS[values.billing_model]) {
      if (values[field] === "") {
        context.addIssue({ code: "custom", path: [field], message: "This field is required." });
      }
    }
    if (values.ends_on?.isBefore(values.starts_on, "day")) {
      context.addIssue({
        code: "custom",
        path: ["ends_on"],
        message: "The end date must be on or after the start date.",
      });
    }
  });

export type ContractFormValues = z.infer<typeof contractSchema>;

const DATE_FORMAT = "YYYY-MM-DD";

const decimalOrNull = (value: string): string | null => (value === "" ? null : value);

export function toContractInput(client: number, values: ContractFormValues): ContractInput {
  const uses = (field: AmountField) => REQUIRED_FIELDS[values.billing_model].includes(field);
  return {
    client,
    billing_model: values.billing_model,
    starts_on: values.starts_on.format(DATE_FORMAT),
    ends_on: values.ends_on ? values.ends_on.format(DATE_FORMAT) : null,
    hourly_rate: uses("hourly_rate") ? decimalOrNull(values.hourly_rate) : null,
    monthly_fee: uses("monthly_fee") ? decimalOrNull(values.monthly_fee) : null,
    included_hours: uses("included_hours") ? decimalOrNull(values.included_hours) : null,
    overage_rate: uses("overage_rate") ? decimalOrNull(values.overage_rate) : null,
    rollover_cap_hours:
      values.billing_model === "retainer" ? values.rollover_cap_hours || "0" : "0",
    rounding_increment_minutes: values.rounding_increment_minutes,
  };
}

export const emptyContractForm = (): ContractFormValues => ({
  billing_model: "retainer",
  starts_on: dayjs().startOf("month"),
  ends_on: null,
  hourly_rate: "",
  monthly_fee: "",
  included_hours: "",
  overage_rate: "",
  rollover_cap_hours: "0",
  rounding_increment_minutes: 15 satisfies RoundingIncrement,
});

export const requiredFieldsFor = (model: BillingModel): readonly AmountField[] =>
  REQUIRED_FIELDS[model];
