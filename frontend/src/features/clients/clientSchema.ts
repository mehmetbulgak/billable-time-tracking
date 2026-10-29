import { z } from "zod";

import type { Client, Currency } from "@/shared/api/types";

import type { ClientInput } from "./clientsApi";

export const CURRENCIES: Currency[] = ["USD", "EUR", "GBP", "TRY"];

export const clientSchema = z.object({
  name: z.string().trim().min(1, "Enter the client name.").max(160),
  contact_name: z.string().trim().max(120),
  email: z.union([z.literal(""), z.email("Enter a valid email address.")]),
  currency: z.enum(["USD", "EUR", "GBP", "TRY"]),
  tax_rate: z
    .string()
    .trim()
    .refine((value) => /^\d{1,3}(\.\d{1,2})?$/.test(value) && Number(value) <= 100, {
      message: "Enter a percentage between 0 and 100.",
    }),
  payment_terms_days: z
    .string()
    .trim()
    .refine((value) => value === "" || (/^\d+$/.test(value) && Number(value) <= 365), {
      message: "Enter a number of days up to 365.",
    }),
});

export type ClientFormValues = z.infer<typeof clientSchema>;

export const clientFormValues = (
  client: Client | null,
  defaultCurrency: Currency,
): ClientFormValues => ({
  name: client?.name ?? "",
  contact_name: client?.contact_name ?? "",
  email: client?.email ?? "",
  currency: client?.currency ?? defaultCurrency,
  tax_rate: client?.tax_rate ?? "0",
  payment_terms_days: client?.payment_terms_days?.toString() ?? "",
});

export const toClientInput = (values: ClientFormValues): ClientInput => ({
  name: values.name,
  contact_name: values.contact_name,
  email: values.email,
  currency: values.currency,
  tax_rate: values.tax_rate,
  payment_terms_days: values.payment_terms_days === "" ? null : Number(values.payment_terms_days),
});
