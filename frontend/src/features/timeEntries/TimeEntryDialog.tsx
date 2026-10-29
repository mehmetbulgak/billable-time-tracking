import { zodResolver } from "@hookform/resolvers/zod";
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import FormControlLabel from "@mui/material/FormControlLabel";
import Stack from "@mui/material/Stack";
import Switch from "@mui/material/Switch";
import TextField from "@mui/material/TextField";
import { DateTimePicker } from "@mui/x-date-pickers/DateTimePicker";
import dayjs from "dayjs";
import { Controller, useForm } from "react-hook-form";

import { ProjectPicker } from "@/features/projects/ProjectPicker";
import { getErrorMessage } from "@/shared/api/errors";
import type { TimeEntry } from "@/shared/api/types";
import { useNotify } from "@/shared/feedback/useNotify";

import { timeEntrySchema, type TimeEntryFormValues } from "./timeEntrySchema";
import { useCreateTimeEntryMutation, useUpdateTimeEntryMutation } from "./timeEntriesApi";

interface TimeEntryDialogProps {
  entry: TimeEntry | null;
  onClose: () => void;
}

const defaultValues = (entry: TimeEntry | null): TimeEntryFormValues => {
  if (entry) {
    return {
      project: entry.project.id,
      description: entry.description,
      started_at: dayjs(entry.started_at),
      ended_at: dayjs(entry.ended_at ?? undefined),
      is_billable: entry.is_billable,
    };
  }
  const end = dayjs().second(0).millisecond(0);
  return {
    project: null,
    description: "",
    started_at: end.subtract(1, "hour"),
    ended_at: end,
    is_billable: true,
  };
};

export function TimeEntryDialog({ entry, onClose }: TimeEntryDialogProps) {
  const notify = useNotify();
  const [createEntry, createState] = useCreateTimeEntryMutation();
  const [updateEntry, updateState] = useUpdateTimeEntryMutation();
  const error = entry ? updateState.error : createState.error;
  const isSaving = createState.isLoading || updateState.isLoading;

  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<TimeEntryFormValues>({
    resolver: zodResolver(timeEntrySchema),
    defaultValues: defaultValues(entry),
  });

  const onSubmit = handleSubmit(async (values) => {
    if (values.project === null) {
      return;
    }
    const payload = {
      project: values.project,
      description: values.description.trim(),
      started_at: values.started_at.toISOString(),
      ended_at: values.ended_at.toISOString(),
      is_billable: values.is_billable,
    };
    const result = entry
      ? await updateEntry({ id: entry.id, ...payload })
      : await createEntry(payload);
    if (!("error" in result)) {
      notify.success(entry ? "Time entry updated" : "Time entry added");
      onClose();
    }
  });

  return (
    <Dialog open onClose={onClose} maxWidth="sm" fullWidth>
      <form onSubmit={(event) => void onSubmit(event)} noValidate>
        <DialogTitle>{entry ? "Edit time entry" : "Add time entry"}</DialogTitle>
        <DialogContent>
          <Stack spacing={2.5} sx={{ pt: 1 }}>
            {error ? <Alert severity="error">{getErrorMessage(error)}</Alert> : null}
            <Controller
              control={control}
              name="project"
              render={({ field }) => (
                <ProjectPicker
                  value={field.value}
                  onChange={(project) => {
                    field.onChange(project);
                  }}
                  error={errors.project?.message}
                  autoFocus={!entry}
                />
              )}
            />
            <TextField
              label="Description"
              multiline
              minRows={2}
              error={Boolean(errors.description)}
              helperText={errors.description?.message}
              {...register("description")}
            />
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <Controller
                control={control}
                name="started_at"
                render={({ field }) => (
                  <DateTimePicker
                    label="Start"
                    ampm={false}
                    value={field.value}
                    onChange={(value) => {
                      field.onChange(value);
                    }}
                    disableFuture
                    slotProps={{
                      textField: {
                        fullWidth: true,
                        error: Boolean(errors.started_at),
                        helperText: errors.started_at?.message,
                      },
                    }}
                  />
                )}
              />
              <Controller
                control={control}
                name="ended_at"
                render={({ field }) => (
                  <DateTimePicker
                    label="End"
                    ampm={false}
                    value={field.value}
                    onChange={(value) => {
                      field.onChange(value);
                    }}
                    disableFuture
                    slotProps={{
                      textField: {
                        fullWidth: true,
                        error: Boolean(errors.ended_at),
                        helperText: errors.ended_at?.message,
                      },
                    }}
                  />
                )}
              />
            </Stack>
            <Controller
              control={control}
              name="is_billable"
              render={({ field }) => (
                <FormControlLabel
                  control={
                    <Switch
                      checked={field.value}
                      onChange={(event) => {
                        field.onChange(event.target.checked);
                      }}
                    />
                  }
                  label="Billable"
                />
              )}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained" loading={isSaving}>
            {entry ? "Save changes" : "Add entry"}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
