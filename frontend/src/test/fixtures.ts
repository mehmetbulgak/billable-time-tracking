import type { BillingPreview, Client, CurrentUser, TimeEntry } from "@/shared/api/types";

export const organization = {
  id: 1,
  name: "Northwind Studio",
  slug: "northwind",
  timezone: "Europe/Istanbul",
  default_currency: "USD" as const,
  default_payment_terms_days: 14,
  invoice_prefix: "NWS",
};

export const managerUser: CurrentUser = {
  id: 2,
  email: "can@northwind.test",
  first_name: "Can",
  last_name: "Demir",
  full_name: "Can Demir",
  role: "manager",
  is_manager: true,
  organization,
};

export const buildEntry = (overrides: Partial<TimeEntry> = {}): TimeEntry => ({
  id: 1,
  user: { id: 2, email: "can@northwind.test", full_name: "Can Demir" },
  project: {
    id: 10,
    name: "Brand Refresh",
    code: "LUM-BR",
    color: "#8D6E63",
    client_id: 5,
    client_name: "Lumen Coffee",
  },
  description: "Packaging mockups",
  started_at: "2026-03-02T09:00:00+03:00",
  ended_at: "2026-03-02T10:30:00+03:00",
  duration_seconds: 5400,
  is_billable: true,
  is_running: false,
  is_locked: false,
  invoice_id: null,
  created_at: "2026-03-02T10:30:00+03:00",
  updated_at: "2026-03-02T10:30:00+03:00",
  ...overrides,
});

export const buildClient = (overrides: Partial<Client> = {}): Client => ({
  id: 5,
  name: "Atlas Fintech",
  contact_name: "Deniz Kaya",
  email: "billing@atlas.test",
  currency: "USD",
  tax_rate: "0.00",
  payment_terms_days: 30,
  is_archived: false,
  created_at: "2026-01-05T09:00:00+03:00",
  ...overrides,
});

export const buildPreview = (overrides: Partial<BillingPreview> = {}): BillingPreview => ({
  lines: [
    {
      kind: "hourly_time",
      description: "Billable time",
      quantity: "12.50",
      unit_price: "115.00",
      amount: "1437.50",
    },
  ],
  subtotal: "1437.50",
  tracked_hours: "12.20",
  billable_hours: "12.50",
  included_hours: "0.00",
  rollover_hours_available: "0.00",
  overage_hours: "0.00",
  is_empty: false,
  replaces_draft: null,
  ...overrides,
});
