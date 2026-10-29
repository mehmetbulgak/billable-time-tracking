import { zodResolver } from "@hookform/resolvers/zod";
import CheckRounded from "@mui/icons-material/CheckRounded";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import ButtonBase from "@mui/material/ButtonBase";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import FormControlLabel from "@mui/material/FormControlLabel";
import Stack from "@mui/material/Stack";
import Switch from "@mui/material/Switch";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import { getErrorMessage } from "@/shared/api/errors";
import type { Client, Project } from "@/shared/api/types";
import { useNotify } from "@/shared/feedback/useNotify";

import { useCreateProjectMutation, useUpdateProjectMutation } from "./projectsApi";

const DEFAULT_COLOR = "#4338CA";

const PROJECT_COLORS = [
  DEFAULT_COLOR,
  "#1E88E5",
  "#0F766E",
  "#43A047",
  "#F4511E",
  "#FF7043",
  "#8D6E63",
  "#8E24AA",
  "#D81B60",
  "#78909C",
];

const projectSchema = z.object({
  name: z.string().trim().min(1, "Enter a project name.").max(160),
  code: z
    .string()
    .trim()
    .toUpperCase()
    .regex(/^[A-Z0-9][A-Z0-9-]{1,11}$/, "Use 2–12 letters, digits or dashes."),
  color: z.string().regex(/^#[0-9A-Fa-f]{6}$/),
  is_billable: z.boolean(),
});

type ProjectFormValues = z.infer<typeof projectSchema>;

interface ProjectDialogProps {
  client: Client;
  project: Project | null;
  onClose: () => void;
}

export function ProjectDialog({ client, project, onClose }: ProjectDialogProps) {
  const notify = useNotify();
  const [createProject, createState] = useCreateProjectMutation();
  const [updateProject, updateState] = useUpdateProjectMutation();
  const error = project ? updateState.error : createState.error;
  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ProjectFormValues>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      name: project?.name ?? "",
      code: project?.code ?? "",
      color: project?.color ?? DEFAULT_COLOR,
      is_billable: project?.is_billable ?? true,
    },
  });

  const onSubmit = handleSubmit(async (values) => {
    const result = project
      ? await updateProject({ id: project.id, ...values })
      : await createProject({ client: client.id, ...values });
    if (!("error" in result)) {
      notify.success(project ? "Project updated" : "Project created");
      onClose();
    }
  });

  return (
    <Dialog open onClose={onClose} maxWidth="xs" fullWidth>
      <form onSubmit={(event) => void onSubmit(event)} noValidate>
        <DialogTitle>{project ? "Edit project" : `New project for ${client.name}`}</DialogTitle>
        <DialogContent>
          <Stack spacing={2.5} sx={{ pt: 1 }}>
            {error ? <Alert severity="error">{getErrorMessage(error)}</Alert> : null}
            <TextField
              label="Project name"
              autoFocus
              error={Boolean(errors.name)}
              helperText={errors.name?.message}
              {...register("name")}
            />
            <TextField
              label="Code"
              placeholder="LUM-WEB"
              error={Boolean(errors.code)}
              helperText={errors.code?.message ?? "Short unique code shown in reports."}
              slotProps={{ htmlInput: { style: { textTransform: "uppercase" } } }}
              {...register("code")}
            />
            <Controller
              control={control}
              name="color"
              render={({ field }) => (
                <Stack spacing={1}>
                  <Typography variant="body2" color="text.secondary">
                    Color
                  </Typography>
                  <Stack direction="row" sx={{ flexWrap: "wrap", gap: 1 }}>
                    {PROJECT_COLORS.map((color) => (
                      <ButtonBase
                        key={color}
                        aria-label={`Use color ${color}`}
                        onClick={() => {
                          field.onChange(color);
                        }}
                        sx={{ borderRadius: "50%" }}
                      >
                        <Box
                          sx={{
                            width: 32,
                            height: 32,
                            borderRadius: "50%",
                            bgcolor: color,
                            display: "grid",
                            placeItems: "center",
                            color: "common.white",
                          }}
                        >
                          {field.value === color ? <CheckRounded fontSize="small" /> : null}
                        </Box>
                      </ButtonBase>
                    ))}
                  </Stack>
                </Stack>
              )}
            />
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
                  label="Time is billable by default"
                />
              )}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button
            type="submit"
            variant="contained"
            loading={createState.isLoading || updateState.isLoading}
          >
            {project ? "Save changes" : "Create project"}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
