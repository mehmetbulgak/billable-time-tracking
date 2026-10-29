import AddRounded from "@mui/icons-material/AddRounded";
import ChevronLeft from "@mui/icons-material/ChevronLeft";
import ChevronRight from "@mui/icons-material/ChevronRight";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import IconButton from "@mui/material/IconButton";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableContainer from "@mui/material/TableContainer";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import dayjs from "dayjs";
import { useMemo, useState } from "react";

import { useCurrentUser } from "@/features/auth/useCurrentUser";
import { useListMembersQuery } from "@/features/team/membersApi";
import type { TimeEntry } from "@/shared/api/types";
import { ConfirmDialog } from "@/shared/components/ConfirmDialog";
import { EmptyState } from "@/shared/components/EmptyState";
import { ErrorState } from "@/shared/components/ErrorState";
import { LoadingState } from "@/shared/components/LoadingState";
import { PageHeader } from "@/shared/components/PageHeader";
import { useNotify } from "@/shared/feedback/useNotify";
import { useNow } from "@/shared/hooks/useNow";
import { formatDurationShort } from "@/shared/lib/format";
import {
  isCurrentWeek,
  shiftWeek,
  weekContaining,
  weekDays,
  weekLabel,
  type WeekRange,
} from "@/shared/lib/week";

import { groupEntriesByDay, type DayGroup } from "./groupEntriesByDay";
import { TimeEntryDialog } from "./TimeEntryDialog";
import { TimeEntryRow } from "./TimeEntryRow";
import { useDeleteTimeEntryMutation, useListTimeEntriesQuery } from "./timeEntriesApi";

type DialogState = { mode: "closed" } | { mode: "create" } | { mode: "edit"; entry: TimeEntry };

const ALL_MEMBERS = 0;

function WeekStrip({ week, groups }: { week: WeekRange; groups: DayGroup[] }) {
  const totals = new Map(groups.map((group) => [group.date, group.totalSeconds]));
  const weekTotal = groups.reduce((sum, group) => sum + group.totalSeconds, 0);

  return (
    <Card sx={{ mb: 3 }}>
      <Stack direction="row" sx={{ overflowX: "auto" }}>
        {weekDays(week).map((day) => {
          const seconds = totals.get(day.format("YYYY-MM-DD")) ?? 0;
          const isToday = day.isSame(dayjs(), "day");
          return (
            <Box
              key={day.toISOString()}
              sx={{
                flex: 1,
                minWidth: 96,
                p: 2,
                borderRight: 1,
                borderColor: "divider",
                bgcolor: isToday ? "action.hover" : "transparent",
              }}
            >
              <Typography variant="caption" color="text.secondary">
                {day.format("ddd D")}
              </Typography>
              <Typography variant="subtitle1" sx={{ fontVariantNumeric: "tabular-nums" }}>
                {seconds > 0 ? formatDurationShort(seconds) : "—"}
              </Typography>
            </Box>
          );
        })}
        <Box sx={{ minWidth: 120, p: 2, bgcolor: "primary.main", color: "primary.contrastText" }}>
          <Typography variant="caption">Week total</Typography>
          <Typography variant="subtitle1" sx={{ fontVariantNumeric: "tabular-nums" }}>
            {formatDurationShort(weekTotal)}
          </Typography>
        </Box>
      </Stack>
    </Card>
  );
}

export function TimesheetPage() {
  const user = useCurrentUser();
  const notify = useNotify();
  const [week, setWeek] = useState(() => weekContaining(dayjs()));
  const [memberId, setMemberId] = useState<number>(user.id);
  const [dialog, setDialog] = useState<DialogState>({ mode: "closed" });
  const [pendingDelete, setPendingDelete] = useState<TimeEntry | null>(null);
  const [deleteEntry, deleteState] = useDeleteTimeEntryMutation();
  const { data: members } = useListMembersQuery({ is_active: true }, { skip: !user.is_manager });

  const { data, isLoading, error, refetch } = useListTimeEntriesQuery({
    started_after: week.start.toISOString(),
    started_before: week.end.toISOString(),
    user: memberId === ALL_MEMBERS ? undefined : memberId,
    page_size: 200,
    ordering: "-started_at",
  });
  const hasRunningEntry = data?.results.some((entry) => entry.is_running) ?? false;
  const now = useNow(hasRunningEntry, 30_000);
  const groups = useMemo(() => groupEntriesByDay(data?.results ?? [], now), [data, now]);

  const confirmDelete = async () => {
    if (!pendingDelete) {
      return;
    }
    const result = await deleteEntry(pendingDelete.id);
    if ("error" in result) {
      notify.error(result.error);
    } else {
      notify.success("Time entry deleted");
    }
    setPendingDelete(null);
  };

  const renderEntries = () => {
    if (isLoading) {
      return <LoadingState />;
    }
    if (error) {
      return <ErrorState error={error} onRetry={() => void refetch()} />;
    }
    if (groups.length === 0) {
      return (
        <Card>
          <EmptyState
            title="No time tracked this week"
            description="Start the timer at the top of the page or add an entry manually."
            action={
              <Button
                startIcon={<AddRounded />}
                onClick={() => {
                  setDialog({ mode: "create" });
                }}
              >
                Add entry
              </Button>
            }
          />
        </Card>
      );
    }
    return (
      <Stack spacing={2.5}>
        {groups.map((group) => (
          <Card key={group.date}>
            <Stack
              direction="row"
              sx={{
                px: 2,
                py: 1.5,
                justifyContent: "space-between",
                borderBottom: 1,
                borderColor: "divider",
              }}
            >
              <Typography variant="subtitle2">
                {dayjs(group.date).format("dddd, MMMM D")}
              </Typography>
              <Typography variant="subtitle2" sx={{ fontVariantNumeric: "tabular-nums" }}>
                {formatDurationShort(group.totalSeconds)}
              </Typography>
            </Stack>
            <TableContainer>
              <Table size="small" sx={{ tableLayout: "fixed" }}>
                <TableBody>
                  {group.entries.map((entry) => (
                    <TimeEntryRow
                      key={entry.id}
                      entry={entry}
                      now={now}
                      showMember={memberId === ALL_MEMBERS}
                      onEdit={(selected) => {
                        setDialog({ mode: "edit", entry: selected });
                      }}
                      onDelete={setPendingDelete}
                    />
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Card>
        ))}
      </Stack>
    );
  };

  return (
    <>
      <PageHeader
        title="Timesheet"
        subtitle={weekLabel(week)}
        actions={
          <>
            {user.is_manager ? (
              <TextField
                select
                size="small"
                label="Member"
                value={memberId}
                onChange={(event) => {
                  setMemberId(Number(event.target.value));
                }}
                sx={{ minWidth: 180 }}
              >
                <MenuItem value={ALL_MEMBERS}>Whole team</MenuItem>
                {(members?.results ?? []).map((member) => (
                  <MenuItem key={member.id} value={member.id}>
                    {member.full_name}
                  </MenuItem>
                ))}
              </TextField>
            ) : null}
            <Stack direction="row" sx={{ alignItems: "center" }}>
              <IconButton
                aria-label="Previous week"
                onClick={() => {
                  setWeek((current) => shiftWeek(current, -1));
                }}
              >
                <ChevronLeft />
              </IconButton>
              <Button
                variant="text"
                disabled={isCurrentWeek(week)}
                onClick={() => {
                  setWeek(weekContaining(dayjs()));
                }}
              >
                This week
              </Button>
              <IconButton
                aria-label="Next week"
                disabled={isCurrentWeek(week)}
                onClick={() => {
                  setWeek((current) => shiftWeek(current, 1));
                }}
              >
                <ChevronRight />
              </IconButton>
            </Stack>
            <Button
              variant="contained"
              startIcon={<AddRounded />}
              onClick={() => {
                setDialog({ mode: "create" });
              }}
            >
              Add entry
            </Button>
          </>
        }
      />
      <WeekStrip week={week} groups={groups} />
      {renderEntries()}
      {dialog.mode === "closed" ? null : (
        <TimeEntryDialog
          entry={dialog.mode === "edit" ? dialog.entry : null}
          onClose={() => {
            setDialog({ mode: "closed" });
          }}
        />
      )}
      <ConfirmDialog
        open={pendingDelete !== null}
        title="Delete time entry?"
        description="This entry will be removed permanently."
        confirmLabel="Delete"
        destructive
        loading={deleteState.isLoading}
        onConfirm={() => void confirmDelete()}
        onClose={() => {
          setPendingDelete(null);
        }}
      />
    </>
  );
}
