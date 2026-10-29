import ArrowBackRounded from "@mui/icons-material/ArrowBackRounded";
import BlockOutlined from "@mui/icons-material/BlockOutlined";
import DeleteOutline from "@mui/icons-material/DeleteOutlined";
import DownloadOutlined from "@mui/icons-material/DownloadOutlined";
import PaidOutlined from "@mui/icons-material/PaidOutlined";
import SendOutlined from "@mui/icons-material/SendOutlined";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CardHeader from "@mui/material/CardHeader";
import Grid from "@mui/material/Grid";
import Link from "@mui/material/Link";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useState, type ReactNode } from "react";
import { Link as RouterLink, useNavigate, useParams } from "react-router";

import { BILLING_MODEL_LABELS } from "@/features/contracts/contractTerms";
import type { InvoiceDetail } from "@/shared/api/types";
import { ConfirmDialog } from "@/shared/components/ConfirmDialog";
import { ErrorState } from "@/shared/components/ErrorState";
import { LoadingState } from "@/shared/components/LoadingState";
import { PageHeader } from "@/shared/components/PageHeader";
import { useNotify } from "@/shared/feedback/useNotify";
import { formatDate, formatHours, formatPeriodRange, toNumber } from "@/shared/lib/format";

import { downloadText } from "./downloadText";
import { InvoiceLinesTable } from "./InvoiceLinesTable";
import { InvoiceStatusChip } from "./InvoiceStatusChip";
import {
  useDiscardInvoiceMutation,
  useExportInvoiceMutation,
  useGetInvoiceQuery,
  useIssueInvoiceMutation,
  useMarkInvoicePaidMutation,
  useVoidInvoiceMutation,
} from "./invoicesApi";

type PendingAction = "issue" | "pay" | "void" | "discard" | null;

interface ActionCopy {
  title: string;
  description: string;
  confirm: string;
  success: string;
}

const ACTION_COPY: Record<Exclude<PendingAction, null>, ActionCopy> = {
  issue: {
    title: "Issue this invoice?",
    description:
      "An invoice number is assigned, the time entries stay locked and the client receives the invoice by email.",
    confirm: "Issue invoice",
    success: "Invoice issued",
  },
  pay: {
    title: "Mark as paid?",
    description: "Record that the client has paid this invoice in full.",
    confirm: "Mark as paid",
    success: "Invoice marked as paid",
  },
  void: {
    title: "Void this invoice?",
    description:
      "The invoice keeps its number for your records and its time entries become available for a new invoice.",
    confirm: "Void invoice",
    success: "Invoice voided",
  },
  discard: {
    title: "Discard this draft?",
    description: "The draft is deleted and its time entries are unlocked.",
    confirm: "Discard draft",
    success: "Draft discarded",
  },
};

function Fact({ label, value }: { label: string; value: ReactNode }) {
  return (
    <Stack spacing={0.25}>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="body2" component="div">
        {value}
      </Typography>
    </Stack>
  );
}

function UsageSummary({ invoice }: { invoice: InvoiceDetail }) {
  const isRetainer = invoice.billing_model === "retainer";
  return (
    <Card sx={{ height: "100%" }}>
      <CardHeader title="Time summary" subheader={`${invoice.time_entry_count} time entries`} />
      <CardContent sx={{ pt: 0 }}>
        <Grid container spacing={2}>
          <Grid size={6}>
            <Fact label="Tracked" value={formatHours(invoice.tracked_hours)} />
          </Grid>
          <Grid size={6}>
            <Fact label="Billable after rounding" value={formatHours(invoice.billable_hours)} />
          </Grid>
          {isRetainer ? (
            <>
              <Grid size={6}>
                <Fact label="Included" value={formatHours(invoice.included_hours)} />
              </Grid>
              <Grid size={6}>
                <Fact
                  label="Rolled over"
                  value={`${formatHours(invoice.rollover_hours_applied)} of ${formatHours(invoice.rollover_hours_available)}`}
                />
              </Grid>
              <Grid size={6}>
                <Fact label="Overage" value={formatHours(invoice.overage_hours)} />
              </Grid>
              <Grid size={6}>
                <Fact label="Unused included" value={formatHours(invoice.unused_included_hours)} />
              </Grid>
            </>
          ) : null}
        </Grid>
      </CardContent>
    </Card>
  );
}

export function InvoiceDetailPage() {
  const invoiceId = Number(useParams().invoiceId);
  const navigate = useNavigate();
  const notify = useNotify();
  const [pending, setPending] = useState<PendingAction>(null);
  const { data: invoice, isLoading, error, refetch } = useGetInvoiceQuery(invoiceId);
  const [issueInvoice, issueState] = useIssueInvoiceMutation();
  const [markPaid, payState] = useMarkInvoicePaidMutation();
  const [voidInvoice, voidState] = useVoidInvoiceMutation();
  const [discardInvoice, discardState] = useDiscardInvoiceMutation();
  const [exportInvoice, exportState] = useExportInvoiceMutation();
  const isWorking =
    issueState.isLoading || payState.isLoading || voidState.isLoading || discardState.isLoading;

  if (isLoading) {
    return <LoadingState />;
  }
  if (error || !invoice) {
    return <ErrorState error={error} onRetry={() => void refetch()} />;
  }

  const runPendingAction = async () => {
    const actions = {
      issue: () => issueInvoice(invoice.id),
      pay: () => markPaid(invoice.id),
      void: () => voidInvoice(invoice.id),
      discard: () => discardInvoice(invoice.id),
    };
    if (pending === null) {
      return;
    }
    const result = await actions[pending]();
    const action = pending;
    setPending(null);
    if ("error" in result) {
      notify.error(result.error);
      return;
    }
    notify.success(ACTION_COPY[action].success);
    if (action === "discard") {
      await navigate("/invoices");
    }
  };

  const exportCsv = async () => {
    const result = await exportInvoice(invoice.id);
    if ("error" in result) {
      notify.error(result.error);
      return;
    }
    downloadText(result.data, `${invoice.number || `draft-${invoice.id}`}.csv`);
  };

  const subtotal = toNumber(invoice.subtotal);
  const totals = [
    { label: "Subtotal", amount: invoice.subtotal },
    ...(toNumber(invoice.tax_amount) > 0 || toNumber(invoice.tax_rate) > 0
      ? [{ label: `Tax (${toNumber(invoice.tax_rate)}%)`, amount: invoice.tax_amount }]
      : []),
    { label: "Total", amount: invoice.total, emphasize: true },
  ];

  return (
    <>
      <Button component={RouterLink} to="/invoices" startIcon={<ArrowBackRounded />} sx={{ mb: 1 }}>
        Invoices
      </Button>
      <PageHeader
        title={
          <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
            <span>{invoice.number || "Draft invoice"}</span>
            <InvoiceStatusChip status={invoice.status} />
          </Stack>
        }
        subtitle={
          <>
            <Link component={RouterLink} to={`/clients/${invoice.client.id}`} underline="hover">
              {invoice.client.name}
            </Link>
            {` · ${formatPeriodRange(invoice.period_start, invoice.period_end)} · ${BILLING_MODEL_LABELS[invoice.billing_model]}`}
          </>
        }
        actions={
          <>
            <Button
              startIcon={<DownloadOutlined />}
              loading={exportState.isLoading}
              onClick={() => void exportCsv()}
            >
              Export CSV
            </Button>
            {invoice.status === "draft" ? (
              <>
                <Button
                  color="error"
                  startIcon={<DeleteOutline />}
                  onClick={() => {
                    setPending("discard");
                  }}
                >
                  Discard
                </Button>
                <Button
                  variant="contained"
                  startIcon={<SendOutlined />}
                  disabled={subtotal === 0}
                  onClick={() => {
                    setPending("issue");
                  }}
                >
                  Issue
                </Button>
              </>
            ) : null}
            {invoice.status === "issued" ? (
              <>
                <Button
                  color="warning"
                  startIcon={<BlockOutlined />}
                  onClick={() => {
                    setPending("void");
                  }}
                >
                  Void
                </Button>
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<PaidOutlined />}
                  onClick={() => {
                    setPending("pay");
                  }}
                >
                  Mark as paid
                </Button>
              </>
            ) : null}
          </>
        }
      />
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 8 }}>
          <Card>
            <CardHeader title="Line items" />
            <InvoiceLinesTable lines={invoice.lines} currency={invoice.currency} totals={totals} />
          </Card>
        </Grid>
        <Grid size={{ xs: 12, lg: 4 }}>
          <Stack spacing={3}>
            <Card>
              <CardHeader title="Details" />
              <CardContent sx={{ pt: 0 }}>
                <Grid container spacing={2}>
                  <Grid size={6}>
                    <Fact label="Issue date" value={formatDate(invoice.issue_date)} />
                  </Grid>
                  <Grid size={6}>
                    <Fact label="Due date" value={formatDate(invoice.due_date)} />
                  </Grid>
                  <Grid size={6}>
                    <Fact label="Paid" value={formatDate(invoice.paid_at)} />
                  </Grid>
                  <Grid size={6}>
                    <Fact label="Currency" value={invoice.currency} />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
            <UsageSummary invoice={invoice} />
          </Stack>
        </Grid>
      </Grid>
      {pending ? (
        <ConfirmDialog
          open
          title={ACTION_COPY[pending].title}
          description={ACTION_COPY[pending].description}
          confirmLabel={ACTION_COPY[pending].confirm}
          destructive={pending === "void" || pending === "discard"}
          loading={isWorking}
          onConfirm={() => void runPendingAction()}
          onClose={() => {
            setPending(null);
          }}
        />
      ) : null}
    </>
  );
}
