import ErrorOutline from "@mui/icons-material/ErrorOutlineOutlined";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import { getErrorMessage } from "@/shared/api/errors";

interface ErrorStateProps {
  error: unknown;
  onRetry?: () => void;
  fullPage?: boolean;
}

export function ErrorState({ error, onRetry, fullPage = false }: ErrorStateProps) {
  return (
    <Box sx={{ minHeight: fullPage ? "100vh" : 240, display: "grid", placeItems: "center", p: 3 }}>
      <Stack spacing={1.5} sx={{ alignItems: "center", textAlign: "center", maxWidth: 420 }}>
        <ErrorOutline color="error" sx={{ fontSize: 40 }} />
        <Typography variant="h6">We could not load this page</Typography>
        <Typography variant="body2" color="text.secondary">
          {getErrorMessage(error)}
        </Typography>
        {onRetry ? (
          <Button variant="outlined" onClick={onRetry}>
            Try again
          </Button>
        ) : null}
      </Stack>
    </Box>
  );
}
