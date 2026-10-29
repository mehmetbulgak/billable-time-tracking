import Avatar from "@mui/material/Avatar";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CardHeader from "@mui/material/CardHeader";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemAvatar from "@mui/material/ListItemAvatar";
import ListItemText from "@mui/material/ListItemText";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import { useGetActiveTimersQuery } from "@/features/timeEntries/timeEntriesApi";
import { ColorDot } from "@/shared/components/ColorDot";
import { EmptyState } from "@/shared/components/EmptyState";
import { ErrorState } from "@/shared/components/ErrorState";
import { LoadingState } from "@/shared/components/LoadingState";
import { useNow } from "@/shared/hooks/useNow";
import { formatDuration } from "@/shared/lib/format";

const initials = (name: string): string =>
  name
    .split(" ")
    .map((part) => part.charAt(0))
    .join("")
    .slice(0, 2)
    .toUpperCase();

export function WorkingNowCard() {
  const { data: timers = [], isLoading, error, refetch } = useGetActiveTimersQuery();
  const now = useNow(timers.length > 0);

  const renderContent = () => {
    if (isLoading) {
      return <LoadingState minHeight={160} />;
    }
    if (error) {
      return <ErrorState error={error} onRetry={() => void refetch()} />;
    }
    if (timers.length === 0) {
      return <EmptyState title="Nobody is tracking right now" />;
    }
    return (
      <List disablePadding>
        {timers.map((timer) => (
          <ListItem key={timer.id} disableGutters>
            <ListItemAvatar>
              <Avatar sx={{ bgcolor: timer.project.color }}>
                {initials(timer.user.full_name)}
              </Avatar>
            </ListItemAvatar>
            <ListItemText
              primary={timer.user.full_name}
              secondary={
                <Stack
                  direction="row"
                  spacing={0.75}
                  component="span"
                  sx={{ alignItems: "center" }}
                >
                  <ColorDot color={timer.project.color} size={8} />
                  <span>
                    {timer.project.client_name} · {timer.project.name}
                  </span>
                </Stack>
              }
            />
            <Typography variant="body2" sx={{ fontVariantNumeric: "tabular-nums" }}>
              {formatDuration((now - new Date(timer.started_at).getTime()) / 1000)}
            </Typography>
          </ListItem>
        ))}
      </List>
    );
  };

  return (
    <Card sx={{ height: "100%" }}>
      <CardHeader
        title="Working now"
        subheader={`${timers.length} active ${timers.length === 1 ? "timer" : "timers"}`}
      />
      <CardContent sx={{ pt: 0 }}>{renderContent()}</CardContent>
    </Card>
  );
}
