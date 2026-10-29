import { baseApi } from "@/shared/api/baseApi";
import type {
  BillingPreview,
  Invoice,
  InvoiceDetail,
  InvoiceStatus,
  Paginated,
} from "@/shared/api/types";

export interface InvoiceFilters {
  status?: InvoiceStatus;
  client?: number;
  page?: number;
}

export interface InvoicePeriodInput {
  client: number;
  period: string;
}

const LIST_TAG = { type: "Invoices", id: "LIST" } as const;

const invoiceChanged = (id: number) => [
  LIST_TAG,
  { type: "Invoices" as const, id },
  "Reports" as const,
  { type: "TimeEntries" as const, id: "LIST" },
];

export const invoicesApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    listInvoices: build.query<Paginated<Invoice>, InvoiceFilters>({
      query: (params) => ({ url: "/invoices/", params }),
      providesTags: [LIST_TAG],
    }),
    getInvoice: build.query<InvoiceDetail, number>({
      query: (id) => `/invoices/${id}/`,
      providesTags: (_result, _error, id) => [{ type: "Invoices", id }],
    }),
    previewInvoice: build.query<BillingPreview, InvoicePeriodInput>({
      query: (params) => ({ url: "/invoices/preview/", params }),
      providesTags: [LIST_TAG],
    }),
    generateInvoice: build.mutation<InvoiceDetail, InvoicePeriodInput>({
      query: (body) => ({ url: "/invoices/generate/", method: "POST", body }),
      invalidatesTags: (result) => (result ? invoiceChanged(result.id) : []),
    }),
    issueInvoice: build.mutation<InvoiceDetail, number>({
      query: (id) => ({ url: `/invoices/${id}/issue/`, method: "POST" }),
      invalidatesTags: (_result, _error, id) => invoiceChanged(id),
    }),
    markInvoicePaid: build.mutation<InvoiceDetail, number>({
      query: (id) => ({ url: `/invoices/${id}/mark-paid/`, method: "POST", body: {} }),
      invalidatesTags: (_result, _error, id) => invoiceChanged(id),
    }),
    voidInvoice: build.mutation<InvoiceDetail, number>({
      query: (id) => ({ url: `/invoices/${id}/void/`, method: "POST" }),
      invalidatesTags: (_result, _error, id) => invoiceChanged(id),
    }),
    discardInvoice: build.mutation<undefined, number>({
      query: (id) => ({ url: `/invoices/${id}/`, method: "DELETE" }),
      invalidatesTags: (_result, _error, id) => invoiceChanged(id),
    }),
    exportInvoice: build.mutation<string, number>({
      query: (id) => ({ url: `/invoices/${id}/export/`, responseHandler: "text" }),
    }),
  }),
});

export const {
  useListInvoicesQuery,
  useGetInvoiceQuery,
  usePreviewInvoiceQuery,
  useGenerateInvoiceMutation,
  useIssueInvoiceMutation,
  useMarkInvoicePaidMutation,
  useVoidInvoiceMutation,
  useDiscardInvoiceMutation,
  useExportInvoiceMutation,
} = invoicesApi;
