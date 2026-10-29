import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CardHeader from "@mui/material/CardHeader";
import Chip from "@mui/material/Chip";
import LinearProgress from "@mui/material/LinearProgress";
import Link from "@mui/material/Link";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { Link as RouterLink } from "react-router";

import type { RetainerUsage } from "@/shared/api/types";
import { EmptyState } from "@/shared/components/EmptyState";
import { ErrorState } from "@/shared/components/ErrorState";
import { LoadingState } from "@/shared/components/LoadingState";
import { InvoiceStatusChip } from "@/features/invoices/InvoiceStatusChip";
import { formatHours, formatMoney, formatPercent, toNumber } from "@/shared/lib/format";

import { useGetRetainerReportQuery } from "./reportsApi";

const WARNING_THRESHOLD = 85;

const progressColor = (usage: RetainerUsage): "primary" | "warning" | "error" => {
  if (toNumber(usage.overage_hours) > 0) {
    return "error";
  }
  return toNumber(usage.utilization) >= WARNING_THRESHOLD ? "warning" : "primary";
};

function RetainerRow({ usage }: { usage: RetainerUsage }) {
  const allowance = toNumber(usage.included_hours) + toNumber(usage.rollover_hours);
  const overage = toNumber(usage.overage_hours);

  return (
    <Stack spacing={1}>
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", gap: 1 }}>
        <Link
          component={RouterLink}
          to={`/clients/${usage.client_id}`}
          underline="hover"
          variant="subtitle2"
        >
          {usage.client_name}
        </Link>
        <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
          {overage > 0 ? (
            <Chip
              size="small"
              color="error"
              variant="outlined"
              label={`+${formatHours(overage)} overage`}
            />
          ) : null}
          {usage.invoice_status ? <InvoiceStatusChip status={usage.invoice_status} /> : null}
        </Stack>
      </Stack>
      <LinearProgress
        variant="determinate"
        color={progressColor(usage)}
        value={Math.min(100, toNumber(usage.utilization))}
        aria-label={`${usage.client_name} retainer usage`}
        sx={{ height: 8, borderRadius: 4 }}
      />
      <Stack direction="row" sx={{ justifyContent: "space-between", flexWrap: "wrap", gap: 1 }}>
        <Typography variant="caption" color="text.secondary">
          {formatHours(usage.used_hours)} of {formatHours(allowance)} (
          {formatPercent(usage.utilization)})
          {toNumber(usage.rollover_hours) > 0
            ? ` · includes ${formatHours(usage.rollover_hours)} rolled over`
            : ""}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {usage.invoice_id ? "Invoiced" : "Projected"}:{" "}
          {formatMoney(usage.projected_total, usage.currency)}
        </Typography>
      </Stack>
    </Stack>
  );
}

export function RetainerUsageCard({ period }: { period: string }) {
  const { data, isLoading, error, refetch } = useGetRetainerReportQuery(period);

  const renderContent = () => {
    if (isLoading) {
      return <LoadingState minHeight={160} />;
    }
    if (error || !data) {
      return <ErrorState error={error} onRetry={() => void refetch()} />;
    }
    if (data.retainers.length === 0) {
      return <EmptyState title="No retainer contracts in this period" />;
    }
    return (
      <Stack spacing={3}>
        {data.retainers.map((usage) => (
          <RetainerRow key={usage.client_id} usage={usage} />
        ))}
      </Stack>
    );
  };

  return (
    <Card sx={{ height: "100%" }}>
      <CardHeader
        title="Retainer usage"
        subheader="Included hours consumed by each retainer client"
      />
      <CardContent sx={{ pt: 0 }}>{renderContent()}</CardContent>
    </Card>
  );
}
