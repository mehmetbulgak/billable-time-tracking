import DeleteOutline from "@mui/icons-material/DeleteOutlined";
import EditOutlined from "@mui/icons-material/EditOutlined";
import LockOutlined from "@mui/icons-material/LockOutlined";
import Chip from "@mui/material/Chip";
import IconButton from "@mui/material/IconButton";
import Stack from "@mui/material/Stack";
import TableCell from "@mui/material/TableCell";
import TableRow from "@mui/material/TableRow";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";

import type { TimeEntry } from "@/shared/api/types";
import { ColorDot } from "@/shared/components/ColorDot";
import { formatDurationShort, formatTimeRange } from "@/shared/lib/format";

import { entrySeconds } from "./groupEntriesByDay";

interface TimeEntryRowProps {
  entry: TimeEntry;
  showMember: boolean;
  now: number;
  onEdit: (entry: TimeEntry) => void;
  onDelete: (entry: TimeEntry) => void;
}

export function TimeEntryRow({ entry, showMember, now, onEdit, onDelete }: TimeEntryRowProps) {
  const editable = !entry.is_locked && !entry.is_running;

  return (
    <TableRow hover>
      <TableCell sx={{ width: "28%" }}>
        <Stack direction="row" spacing={1.25} sx={{ alignItems: "center" }}>
          <ColorDot color={entry.project.color} />
          <Stack sx={{ minWidth: 0 }}>
            <Typography variant="body2" noWrap>
              {entry.project.name}
            </Typography>
            <Typography variant="caption" color="text.secondary" noWrap>
              {entry.project.client_name}
            </Typography>
          </Stack>
        </Stack>
      </TableCell>
      <TableCell sx={{ overflowWrap: "anywhere" }}>
        <Typography variant="body2" color={entry.description ? "text.primary" : "text.disabled"}>
          {entry.description || "No description"}
        </Typography>
        {showMember ? (
          <Typography variant="caption" color="text.secondary">
            {entry.user.full_name}
          </Typography>
        ) : null}
      </TableCell>
      <TableCell sx={{ width: 130, whiteSpace: "nowrap", color: "text.secondary" }}>
        {formatTimeRange(entry.started_at, entry.ended_at)}
      </TableCell>
      <TableCell
        align="right"
        sx={{ width: 90, whiteSpace: "nowrap", fontVariantNumeric: "tabular-nums" }}
      >
        {formatDurationShort(entrySeconds(entry, now))}
      </TableCell>
      <TableCell sx={{ width: 220, whiteSpace: "nowrap" }}>
        <Stack
          direction="row"
          spacing={0.5}
          sx={{ alignItems: "center", justifyContent: "flex-end" }}
        >
          {entry.is_running ? <Chip size="small" color="success" label="Running" /> : null}
          {entry.is_billable ? null : <Chip size="small" variant="outlined" label="Non-billable" />}
          {entry.is_locked ? (
            <Tooltip title="On an invoice — locked">
              <LockOutlined fontSize="small" color="disabled" />
            </Tooltip>
          ) : null}
          <Tooltip title={editable ? "Edit" : "Locked or running entries cannot be edited"}>
            <span>
              <IconButton
                size="small"
                aria-label="Edit entry"
                disabled={!editable}
                onClick={() => {
                  onEdit(entry);
                }}
              >
                <EditOutlined fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
          <Tooltip title={editable ? "Delete" : "Locked or running entries cannot be deleted"}>
            <span>
              <IconButton
                size="small"
                aria-label="Delete entry"
                disabled={!editable}
                onClick={() => {
                  onDelete(entry);
                }}
              >
                <DeleteOutline fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
        </Stack>
      </TableCell>
    </TableRow>
  );
}
