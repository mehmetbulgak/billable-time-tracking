import PlayArrowRounded from "@mui/icons-material/PlayArrowRounded";
import StopRounded from "@mui/icons-material/StopRounded";
import Button from "@mui/material/Button";
import Skeleton from "@mui/material/Skeleton";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useState, type SyntheticEvent } from "react";

import { ProjectPicker } from "@/features/projects/ProjectPicker";
import {
  useGetCurrentTimerQuery,
  useStartTimerMutation,
  useStopTimerMutation,
} from "@/features/timeEntries/timeEntriesApi";
import type { TimeEntry } from "@/shared/api/types";
import { ColorDot } from "@/shared/components/ColorDot";
import { useNotify } from "@/shared/feedback/useNotify";
import { useNow } from "@/shared/hooks/useNow";
import { formatDuration } from "@/shared/lib/format";

function RunningTimer({ entry }: { entry: TimeEntry }) {
  const notify = useNotify();
  const now = useNow(true);
  const [stopTimer, { isLoading }] = useStopTimerMutation();
  const elapsedSeconds = (now - new Date(entry.started_at).getTime()) / 1000;

  const stop = async () => {
    const result = await stopTimer();
    if ("error" in result) {
      notify.error(result.error);
    } else {
      notify.success(
        `Logged ${formatDuration(result.data.duration_seconds)} on ${entry.project.name}`,
      );
    }
  };

  return (
    <Stack direction="row" spacing={2} sx={{ alignItems: "center", flexGrow: 1, minWidth: 0 }}>
      <ColorDot color={entry.project.color} size={12} />
      <Stack sx={{ minWidth: 0, flexGrow: 1 }}>
        <Typography variant="subtitle2" noWrap>
          {entry.description || "No description"}
        </Typography>
        <Typography variant="caption" color="text.secondary" noWrap>
          {entry.project.client_name} · {entry.project.name}
        </Typography>
      </Stack>
      <Typography
        variant="h6"
        component="span"
        aria-label="Elapsed time"
        sx={{ fontVariantNumeric: "tabular-nums", minWidth: 96, textAlign: "right" }}
      >
        {formatDuration(elapsedSeconds)}
      </Typography>
      <Button
        variant="contained"
        color="error"
        onClick={() => void stop()}
        loading={isLoading}
        startIcon={<StopRounded />}
      >
        Stop
      </Button>
    </Stack>
  );
}

function IdleTimer() {
  const notify = useNotify();
  const [projectId, setProjectId] = useState<number | null>(null);
  const [description, setDescription] = useState("");
  const [startTimer, { isLoading }] = useStartTimerMutation();

  const start = async (event: SyntheticEvent) => {
    event.preventDefault();
    if (projectId === null) {
      notify.info("Choose a project to start the timer.");
      return;
    }
    const result = await startTimer({ project: projectId, description: description.trim() });
    if ("error" in result) {
      notify.error(result.error);
      return;
    }
    setDescription("");
  };

  return (
    <Stack
      component="form"
      direction="row"
      spacing={1.5}
      onSubmit={(event) => void start(event)}
      sx={{ alignItems: "center", flexGrow: 1, minWidth: 0 }}
    >
      <TextField
        size="small"
        placeholder="What are you working on?"
        value={description}
        onChange={(event) => {
          setDescription(event.target.value);
        }}
        sx={{ flexGrow: 1, minWidth: 160 }}
        slotProps={{ htmlInput: { "aria-label": "Timer description", maxLength: 500 } }}
      />
      <ProjectPicker value={projectId} onChange={setProjectId} size="small" label="Project" />
      <Button
        type="submit"
        variant="contained"
        color="success"
        loading={isLoading}
        startIcon={<PlayArrowRounded />}
      >
        Start
      </Button>
    </Stack>
  );
}

export function TimerBar() {
  const { data: entry, isLoading } = useGetCurrentTimerQuery();

  if (isLoading) {
    return <Skeleton variant="rounded" height={40} sx={{ flexGrow: 1 }} />;
  }
  return entry ? <RunningTimer entry={entry} /> : <IdleTimer />;
}
