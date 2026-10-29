import Autocomplete from "@mui/material/Autocomplete";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useMemo } from "react";

import type { Project } from "@/shared/api/types";
import { ColorDot } from "@/shared/components/ColorDot";

import { useListProjectsQuery } from "./projectsApi";

interface ProjectPickerProps {
  value: number | null;
  onChange: (projectId: number | null) => void;
  label?: string;
  error?: string | undefined;
  size?: "small" | "medium";
  disabled?: boolean;
  autoFocus?: boolean;
}

export function ProjectPicker({
  value,
  onChange,
  label = "Project",
  error,
  size = "medium",
  disabled = false,
  autoFocus = false,
}: ProjectPickerProps) {
  const { data, isLoading } = useListProjectsQuery({ is_archived: false });
  const projects = useMemo(
    () =>
      [...(data?.results ?? [])].sort(
        (left, right) =>
          left.client_name.localeCompare(right.client_name) || left.name.localeCompare(right.name),
      ),
    [data],
  );
  const selected = projects.find((project) => project.id === value) ?? null;

  return (
    <Autocomplete<Project>
      options={projects}
      value={selected}
      loading={isLoading}
      disabled={disabled}
      size={size}
      groupBy={(project) => project.client_name}
      getOptionLabel={(project) => project.name}
      isOptionEqualToValue={(option, current) => option.id === current.id}
      onChange={(_event, project) => {
        onChange(project?.id ?? null);
      }}
      renderOption={({ key, ...props }, project) => (
        <li key={key} {...props}>
          <Stack direction="row" spacing={1.25} sx={{ alignItems: "center", width: "100%" }}>
            <ColorDot color={project.color} />
            <Typography variant="body2" sx={{ flexGrow: 1 }}>
              {project.name}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {project.code}
            </Typography>
          </Stack>
        </li>
      )}
      renderInput={(params) => (
        <TextField
          {...params}
          label={label}
          autoFocus={autoFocus}
          error={Boolean(error)}
          helperText={error}
          slotProps={{
            ...params.slotProps,
            input: {
              ...params.slotProps.input,
              startAdornment: selected ? (
                <ColorDot color={selected.color} />
              ) : (
                params.slotProps.input.startAdornment
              ),
            },
          }}
        />
      )}
      sx={{ minWidth: 220 }}
    />
  );
}
