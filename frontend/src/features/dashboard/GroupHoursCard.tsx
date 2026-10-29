import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CardHeader from "@mui/material/CardHeader";
import LinearProgress from "@mui/material/LinearProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { GroupHours } from "@/shared/api/types";
import { EmptyState } from "@/shared/components/EmptyState";
import { formatHoursOf, toNumber } from "@/shared/lib/format";

interface GroupHoursCardProps {
  title: string;
  subheader?: string;
  groups: GroupHours[];
}

export function GroupHoursCard({ title, subheader, groups }: GroupHoursCardProps) {
  const maximum = Math.max(1, ...groups.map((group) => toNumber(group.tracked_hours)));

  return (
    <Card sx={{ height: "100%" }}>
      <CardHeader title={title} subheader={subheader} />
      <CardContent sx={{ pt: 0 }}>
        {groups.length === 0 ? (
          <EmptyState title="No time tracked in this period" />
        ) : (
          <Stack spacing={2}>
            {groups.map((group) => {
              const tracked = toNumber(group.tracked_hours);
              const billable = toNumber(group.billable_hours);
              return (
                <Stack key={group.id} spacing={0.75}>
                  <Stack direction="row" sx={{ justifyContent: "space-between", gap: 2 }}>
                    <Typography variant="body2" noWrap>
                      {group.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ flexShrink: 0 }}>
                      {formatHoursOf(billable, tracked)}
                    </Typography>
                  </Stack>
                  <LinearProgress
                    variant="buffer"
                    value={(billable / maximum) * 100}
                    valueBuffer={(tracked / maximum) * 100}
                    aria-label={`${group.name} hours`}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      "& .MuiLinearProgress-dashed": { display: "none" },
                    }}
                  />
                </Stack>
              );
            })}
          </Stack>
        )}
      </CardContent>
    </Card>
  );
}
