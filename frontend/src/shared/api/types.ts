export type Decimal = string;
export type IsoDate = string;
export type IsoDateTime = string;

export type Role = "owner" | "manager" | "member";
export type Currency = "USD" | "EUR" | "GBP" | "TRY";
export type BillingModel = "hourly" | "retainer" | "fixed_fee";
export type InvoiceStatus = "draft" | "issued" | "paid" | "void";
export type LineKind = "hourly_time" | "retainer_fee" | "included_hours" | "overage" | "fixed_fee";
export type RoundingIncrement = 1 | 6 | 15 | 30 | 60;

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface Organization {
  id: number;
  name: string;
  slug: string;
  timezone: string;
  default_currency: Currency;
  default_payment_terms_days: number;
  invoice_prefix: string;
}

export interface CurrentUser {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: Role;
  is_manager: boolean;
  organization: Organization;
}

export interface UserSummary {
  id: number;
  email: string;
  full_name: string;
}

export interface Member {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  date_joined: IsoDateTime;
}

export interface Client {
  id: number;
  name: string;
  contact_name: string;
  email: string;
  currency: Currency;
  tax_rate: Decimal;
  payment_terms_days: number | null;
  is_archived: boolean;
  created_at: IsoDateTime;
}

export interface Project {
  id: number;
  client: number;
  client_name: string;
  name: string;
  code: string;
  color: string;
  is_billable: boolean;
  is_archived: boolean;
  created_at: IsoDateTime;
}

export interface ProjectSummary {
  id: number;
  name: string;
  code: string;
  color: string;
  client_id: number;
  client_name: string;
}

export interface TimeEntry {
  id: number;
  user: UserSummary;
  project: ProjectSummary;
  description: string;
  started_at: IsoDateTime;
  ended_at: IsoDateTime | null;
  duration_seconds: number;
  is_billable: boolean;
  is_running: boolean;
  is_locked: boolean;
  invoice_id: number | null;
  created_at: IsoDateTime;
  updated_at: IsoDateTime;
}

export interface Contract {
  id: number;
  client: number;
  client_name: string;
  billing_model: BillingModel;
  starts_on: IsoDate;
  ends_on: IsoDate | null;
  hourly_rate: Decimal | null;
  monthly_fee: Decimal | null;
  included_hours: Decimal | null;
  overage_rate: Decimal | null;
  rollover_cap_hours: Decimal;
  rounding_increment_minutes: RoundingIncrement;
  has_invoices: boolean;
  created_at: IsoDateTime;
}

export interface ClientSummary {
  id: number;
  name: string;
  currency: Currency;
}

export interface InvoiceLine {
  id: number;
  position: number;
  kind: LineKind;
  description: string;
  quantity: Decimal;
  unit_price: Decimal;
  amount: Decimal;
}

export interface Invoice {
  id: number;
  number: string;
  status: InvoiceStatus;
  client: ClientSummary;
  billing_model: BillingModel;
  period_start: IsoDate;
  period_end: IsoDate;
  currency: Currency;
  subtotal: Decimal;
  tax_amount: Decimal;
  total: Decimal;
  billable_hours: Decimal;
  time_entry_count: number;
  issue_date: IsoDate | null;
  due_date: IsoDate | null;
  created_at: IsoDateTime;
}

export interface InvoiceDetail extends Invoice {
  tax_rate: Decimal;
  lines: InvoiceLine[];
  tracked_hours: Decimal;
  included_hours: Decimal;
  unused_included_hours: Decimal;
  rollover_hours_available: Decimal;
  rollover_hours_applied: Decimal;
  overage_hours: Decimal;
  issued_at: IsoDateTime | null;
  paid_at: IsoDateTime | null;
  voided_at: IsoDateTime | null;
}

export interface BillingPreviewLine {
  kind: LineKind;
  description: string;
  quantity: Decimal;
  unit_price: Decimal;
  amount: Decimal;
}

export interface BillingPreview {
  lines: BillingPreviewLine[];
  subtotal: Decimal;
  tracked_hours: Decimal;
  billable_hours: Decimal;
  included_hours: Decimal;
  rollover_hours_available: Decimal;
  overage_hours: Decimal;
  is_empty: boolean;
  replaces_draft: number | null;
}

export interface HoursBreakdown {
  tracked_hours: Decimal;
  billable_hours: Decimal;
  non_billable_hours: Decimal;
  billable_ratio: Decimal;
}

export interface DailyHours {
  day: IsoDate;
  billable_hours: Decimal;
  non_billable_hours: Decimal;
}

export interface GroupHours {
  id: number;
  name: string;
  tracked_hours: Decimal;
  billable_hours: Decimal;
}

export interface CurrencyRevenue {
  currency: Currency;
  draft: Decimal;
  invoiced: Decimal;
  paid: Decimal;
  outstanding: Decimal;
}

export interface Overview {
  period: string;
  hours: HoursBreakdown;
  unbilled_hours: Decimal;
  active_timers: number;
  revenue: CurrencyRevenue[];
  daily: DailyHours[];
  members: GroupHours[];
  clients: GroupHours[];
}

export interface RetainerUsage {
  client_id: number;
  client_name: string;
  currency: Currency;
  included_hours: Decimal;
  rollover_hours: Decimal;
  used_hours: Decimal;
  remaining_hours: Decimal;
  overage_hours: Decimal;
  utilization: Decimal;
  projected_total: Decimal;
  invoice_id: number | null;
  invoice_status: InvoiceStatus | null;
}

export interface RetainerReport {
  period: string;
  retainers: RetainerUsage[];
}

export interface MyTime {
  period: string;
  hours: HoursBreakdown;
  daily: DailyHours[];
  projects: GroupHours[];
}
