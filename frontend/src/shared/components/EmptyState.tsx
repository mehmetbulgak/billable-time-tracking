import Inbox from "@mui/icons-material/InboxOutlined";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
  icon?: ReactNode;
}

export function EmptyState({ title, description, action, icon }: EmptyStateProps) {
  return (
    <Box sx={{ py: 6, px: 3, display: "grid", placeItems: "center" }}>
      <Stack spacing={1.5} sx={{ alignItems: "center", textAlign: "center", maxWidth: 380 }}>
        <Box sx={{ color: "text.disabled" }}>{icon ?? <Inbox sx={{ fontSize: 40 }} />}</Box>
        <Typography variant="subtitle1">{title}</Typography>
        {description ? (
          <Typography variant="body2" color="text.secondary">
            {description}
          </Typography>
        ) : null}
        {action}
      </Stack>
    </Box>
  );
}
