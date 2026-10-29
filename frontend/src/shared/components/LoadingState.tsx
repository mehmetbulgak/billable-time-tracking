import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";

interface LoadingStateProps {
  minHeight?: number;
}

export function LoadingState({ minHeight = 240 }: LoadingStateProps) {
  return (
    <Box sx={{ minHeight, display: "grid", placeItems: "center" }}>
      <CircularProgress size={32} aria-label="Loading" />
    </Box>
  );
}
