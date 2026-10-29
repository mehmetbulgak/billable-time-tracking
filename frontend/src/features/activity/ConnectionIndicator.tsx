import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";

import type { ConnectionStatus } from "./useActivityStream";

const LABELS: Record<ConnectionStatus, string> = {
  online: "Live",
  connecting: "Connecting",
  offline: "Offline",
};

const DESCRIPTIONS: Record<ConnectionStatus, string> = {
  online: "Team activity updates in real time.",
  connecting: "Connecting to live updates…",
  offline: "Live updates paused. Reconnecting automatically.",
};

const COLORS: Record<ConnectionStatus, string> = {
  online: "success.main",
  connecting: "warning.main",
  offline: "text.disabled",
};

export function ConnectionIndicator({ status }: { status: ConnectionStatus }) {
  return (
    <Tooltip title={DESCRIPTIONS[status]}>
      <Stack direction="row" spacing={0.75} sx={{ alignItems: "center", px: 1 }}>
        <Box
          sx={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            bgcolor: COLORS[status],
            boxShadow: status === "online" ? "0 0 0 3px rgba(46, 125, 50, 0.18)" : "none",
          }}
        />
        <Typography variant="caption" color="text.secondary">
          {LABELS[status]}
        </Typography>
      </Stack>
    </Tooltip>
  );
}
