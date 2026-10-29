import AccessTimeOutlined from "@mui/icons-material/AccessTimeOutlined";
import HourglassBottomOutlined from "@mui/icons-material/HourglassBottomOutlined";
import PaidOutlined from "@mui/icons-material/PaidOutlined";
import PercentOutlined from "@mui/icons-material/PercentOutlined";
import Grid from "@mui/material/Grid";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import { WorkingNowCard } from "@/features/activity/WorkingNowCard";
import { useCurrentUser } from "@/features/auth/useCurrentUser";
import type { CurrencyRevenue } from "@/shared/api/types";
import { ErrorState } from "@/shared/components/ErrorState";
import { LoadingState } from "@/shared/components/LoadingState";
import { MonthSwitcher } from "@/shared/components/MonthSwitcher";
import { PageHeader } from "@/shared/components/PageHeader";
import { StatCard } from "@/shared/components/StatCard";
import { usePeriodParam } from "@/shared/hooks/usePeriodParam";
import { formatHours, formatMoney, formatPercent } from "@/shared/lib/format";
import { periodLabel, type Period } from "@/shared/lib/period";

import { GroupHoursCard } from "./GroupHoursCard";
import { HoursChart } from "./HoursChart";
import { RetainerUsageCard } from "./RetainerUsageCard";
import { useGetMyTimeQuery, useGetOverviewQuery } from "./reportsApi";

function RevenueValue({ revenue }: { revenue: CurrencyRevenue[] }) {
  if (revenue.length === 0) {
    return <>—</>;
  }
  return (
    <Stack>
      {revenue.map((row) => (
        <span key={row.currency}>{formatMoney(row.invoiced, row.currency)}</span>
      ))}
    </Stack>
  );
}

function OutstandingHint({ revenue }: { revenue: CurrencyRevenue[] }) {
  const parts = revenue
    .filter((row) => Number(row.outstanding) > 0 || Number(row.draft) > 0)
    .map(
      (row) =>
        `${formatMoney(row.outstanding, row.currency)} outstanding, ${formatMoney(row.draft, row.currency)} in drafts`,
    );
  return <>{parts.length > 0 ? parts.join(" · ") : "Nothing outstanding"}</>;
}

function ManagerDashboard({ period }: { period: Period }) {
  const { data, isLoading, error, refetch } = useGetOverviewQuery(period);

  if (isLoading) {
    return <LoadingState />;
  }
  if (error || !data) {
    return <ErrorState error={error} onRetry={() => void refetch()} />;
  }

  return (
    <Grid container spacing={3}>
      <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
        <StatCard
          label="Tracked"
          value={formatHours(data.hours.tracked_hours)}
          hint={`${formatHours(data.hours.billable_hours)} billable`}
          icon={<AccessTimeOutlined />}
        />
      </Grid>
      <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
        <StatCard
          label="Billable ratio"
          value={formatPercent(data.hours.billable_ratio)}
          hint={`${formatHours(data.hours.non_billable_hours)} non-billable`}
          icon={<PercentOutlined />}
        />
      </Grid>
      <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
        <StatCard
          label="Unbilled"
          value={formatHours(data.unbilled_hours)}
          hint="Billable time not on an invoice yet"
          icon={<HourglassBottomOutlined />}
        />
      </Grid>
      <Grid size={{ xs: 12, sm: 6, lg: 3 }}>
        <StatCard
          label="Invoiced"
          value={<RevenueValue revenue={data.revenue} />}
          hint={<OutstandingHint revenue={data.revenue} />}
          icon={<PaidOutlined />}
        />
      </Grid>
      <Grid size={{ xs: 12, lg: 8 }}>
        <HoursChart daily={data.daily} />
      </Grid>
      <Grid size={{ xs: 12, lg: 4 }}>
        <WorkingNowCard />
      </Grid>
      <Grid size={{ xs: 12, lg: 6 }}>
        <RetainerUsageCard period={period} />
      </Grid>
      <Grid size={{ xs: 12, md: 6, lg: 3 }}>
        <GroupHoursCard title="Team" subheader="Billable of tracked hours" groups={data.members} />
      </Grid>
      <Grid size={{ xs: 12, md: 6, lg: 3 }}>
        <GroupHoursCard
          title="Clients"
          subheader="Billable of tracked hours"
          groups={data.clients}
        />
      </Grid>
    </Grid>
  );
}

function MemberDashboard({ period }: { period: Period }) {
  const { data, isLoading, error, refetch } = useGetMyTimeQuery(period);

  if (isLoading) {
    return <LoadingState />;
  }
  if (error || !data) {
    return <ErrorState error={error} onRetry={() => void refetch()} />;
  }

  return (
    <Grid container spacing={3}>
      <Grid size={{ xs: 12, sm: 4 }}>
        <StatCard
          label="Tracked"
          value={formatHours(data.hours.tracked_hours)}
          icon={<AccessTimeOutlined />}
        />
      </Grid>
      <Grid size={{ xs: 12, sm: 4 }}>
        <StatCard
          label="Billable"
          value={formatHours(data.hours.billable_hours)}
          icon={<PaidOutlined />}
        />
      </Grid>
      <Grid size={{ xs: 12, sm: 4 }}>
        <StatCard
          label="Billable ratio"
          value={formatPercent(data.hours.billable_ratio)}
          icon={<PercentOutlined />}
        />
      </Grid>
      <Grid size={{ xs: 12, lg: 8 }}>
        <HoursChart daily={data.daily} title="My daily hours" />
      </Grid>
      <Grid size={{ xs: 12, lg: 4 }}>
        <WorkingNowCard />
      </Grid>
      <Grid size={{ xs: 12, lg: 6 }}>
        <GroupHoursCard
          title="Projects"
          subheader="Billable of tracked hours"
          groups={data.projects}
        />
      </Grid>
    </Grid>
  );
}

export function DashboardPage() {
  const user = useCurrentUser();
  const [period, setPeriod] = usePeriodParam();

  return (
    <>
      <PageHeader
        title={user.is_manager ? "Overview" : "My time"}
        subtitle={
          <Typography variant="body2" color="text.secondary">
            {user.organization.name} · {periodLabel(period)}
          </Typography>
        }
        actions={<MonthSwitcher period={period} onChange={setPeriod} />}
      />
      {user.is_manager ? <ManagerDashboard period={period} /> : <MemberDashboard period={period} />}
    </>
  );
}
