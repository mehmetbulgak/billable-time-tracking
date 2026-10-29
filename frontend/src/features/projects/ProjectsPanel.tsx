import AddRounded from "@mui/icons-material/AddRounded";
import ArchiveOutlined from "@mui/icons-material/ArchiveOutlined";
import EditOutlined from "@mui/icons-material/EditOutlined";
import UnarchiveOutlined from "@mui/icons-material/UnarchiveOutlined";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import IconButton from "@mui/material/IconButton";
import Stack from "@mui/material/Stack";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { useState } from "react";

import type { Client, Project } from "@/shared/api/types";
import { ColorDot } from "@/shared/components/ColorDot";
import { EmptyState } from "@/shared/components/EmptyState";
import { ErrorState } from "@/shared/components/ErrorState";
import { LoadingState } from "@/shared/components/LoadingState";
import { useNotify } from "@/shared/feedback/useNotify";

import { ProjectDialog } from "./ProjectDialog";
import { useListProjectsQuery, useUpdateProjectMutation } from "./projectsApi";

type DialogState = { mode: "closed" } | { mode: "create" } | { mode: "edit"; project: Project };

export function ProjectsPanel({ client }: { client: Client }) {
  const notify = useNotify();
  const [dialog, setDialog] = useState<DialogState>({ mode: "closed" });
  const { data, isLoading, error, refetch } = useListProjectsQuery({ client: client.id });
  const [updateProject] = useUpdateProjectMutation();

  const toggleArchived = async (project: Project) => {
    const result = await updateProject({ id: project.id, is_archived: !project.is_archived });
    if ("error" in result) {
      notify.error(result.error);
    } else {
      notify.success(project.is_archived ? "Project restored" : "Project archived");
    }
  };

  if (isLoading) {
    return <LoadingState />;
  }
  if (error || !data) {
    return <ErrorState error={error} onRetry={() => void refetch()} />;
  }

  return (
    <Stack spacing={2}>
      <Stack direction="row" sx={{ justifyContent: "flex-end" }}>
        <Button
          variant="contained"
          startIcon={<AddRounded />}
          disabled={client.is_archived}
          onClick={() => {
            setDialog({ mode: "create" });
          }}
        >
          New project
        </Button>
      </Stack>
      <Card>
        {data.results.length === 0 ? (
          <EmptyState
            title="No projects yet"
            description="Projects group the time your team tracks."
          />
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Project</TableCell>
                  <TableCell>Code</TableCell>
                  <TableCell>Billing</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.results.map((project) => (
                  <TableRow key={project.id} hover>
                    <TableCell>
                      <Stack direction="row" spacing={1.25} sx={{ alignItems: "center" }}>
                        <ColorDot color={project.color} />
                        <Typography variant="body2">{project.name}</Typography>
                        {project.is_archived ? <Chip size="small" label="Archived" /> : null}
                      </Stack>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: "monospace" }}>
                        {project.code}
                      </Typography>
                    </TableCell>
                    <TableCell>{project.is_billable ? "Billable" : "Non-billable"}</TableCell>
                    <TableCell align="right">
                      <Tooltip title="Edit">
                        <IconButton
                          size="small"
                          aria-label={`Edit ${project.name}`}
                          onClick={() => {
                            setDialog({ mode: "edit", project });
                          }}
                        >
                          <EditOutlined fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title={project.is_archived ? "Restore" : "Archive"}>
                        <IconButton
                          size="small"
                          aria-label={`${project.is_archived ? "Restore" : "Archive"} ${project.name}`}
                          onClick={() => void toggleArchived(project)}
                        >
                          {project.is_archived ? (
                            <UnarchiveOutlined fontSize="small" />
                          ) : (
                            <ArchiveOutlined fontSize="small" />
                          )}
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Card>
      {dialog.mode === "closed" ? null : (
        <ProjectDialog
          client={client}
          project={dialog.mode === "edit" ? dialog.project : null}
          onClose={() => {
            setDialog({ mode: "closed" });
          }}
        />
      )}
    </Stack>
  );
}
