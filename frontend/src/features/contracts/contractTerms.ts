import type { BillingModel, Contract, Currency, RoundingIncrement } from "@/shared/api/types";
import { formatHours, formatMoney } from "@/shared/lib/format";

export const BILLING_MODEL_LABELS: Record<BillingModel, string> = {
  hourly: "Hourly",
  retainer: "Retainer",
  fixed_fee: "Fixed fee",
};

export const ROUNDING_OPTIONS: { value: RoundingIncrement; label: string }[] = [
  { value: 1, label: "1 minute" },
  { value: 6, label: "6 minutes" },
  { value: 15, label: "15 minutes" },
  { value: 30, label: "30 minutes" },
  { value: 60, label: "1 hour" },
];

export function describeContract(contract: Contract, currency: Currency): string {
  switch (contract.billing_model) {
    case "hourly":
      return `${formatMoney(contract.hourly_rate, currency)} per hour`;
    case "retainer":
      return [
        `${formatMoney(contract.monthly_fee, currency)} / month`,
        `${formatHours(contract.included_hours)} included`,
        `${formatMoney(contract.overage_rate, currency)} / h overage`,
      ].join(" · ");
    case "fixed_fee":
      return `${formatMoney(contract.monthly_fee, currency)} / month`;
  }
}

export function isContractActive(contract: Contract, today: string): boolean {
  return contract.starts_on <= today && (contract.ends_on === null || contract.ends_on >= today);
}
