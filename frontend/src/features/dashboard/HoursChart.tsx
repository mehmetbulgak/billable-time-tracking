import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CardHeader from "@mui/material/CardHeader";
import { useTheme } from "@mui/material/styles";
import { BarChart } from "@mui/x-charts/BarChart";
import dayjs from "dayjs";
import { useMemo } from "react";

import type { DailyHours } from "@/shared/api/types";
import { formatHours, toNumber } from "@/shared/lib/format";

interface HoursChartProps {
  daily: DailyHours[];
  title?: string;
}

const valueFormatter = (value: number | null): string => formatHours(value ?? 0);

export function HoursChart({ daily, title = "Daily hours" }: HoursChartProps) {
  const theme = useTheme();
  const dataset = useMemo(
    () =>
      daily.map((day) => ({
        day: dayjs(day.day).format("D"),
        billable: toNumber(day.billable_hours),
        nonBillable: toNumber(day.non_billable_hours),
      })),
    [daily],
  );

  return (
    <Card sx={{ height: "100%" }}>
      <CardHeader title={title} subheader="Billable and non-billable time per day" />
      <CardContent sx={{ pt: 0 }}>
        <BarChart
          height={300}
          dataset={dataset}
          xAxis={[{ scaleType: "band", dataKey: "day", tickLabelStyle: { fontSize: 11 } }]}
          yAxis={[{ width: 36 }]}
          series={[
            {
              dataKey: "billable",
              label: "Billable",
              stack: "hours",
              color: theme.palette.primary.main,
              valueFormatter,
            },
            {
              dataKey: "nonBillable",
              label: "Non-billable",
              stack: "hours",
              color: "#CBD5E1",
              valueFormatter,
            },
          ]}
          borderRadius={4}
          margin={{ left: 0, right: 8, top: 16, bottom: 0 }}
        />
      </CardContent>
    </Card>
  );
}
