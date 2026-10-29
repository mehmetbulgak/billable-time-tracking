import TimerOutlined from "@mui/icons-material/TimerOutlined";
import Box from "@mui/material/Box";

interface BrandMarkProps {
  size?: number;
}

export function BrandMark({ size = 36 }: BrandMarkProps) {
  return (
    <Box
      aria-hidden
      sx={{
        width: size,
        height: size,
        borderRadius: 2.5,
        display: "grid",
        placeItems: "center",
        bgcolor: "primary.main",
        color: "primary.contrastText",
        flexShrink: 0,
      }}
    >
      <TimerOutlined sx={{ fontSize: size * 0.62 }} />
    </Box>
  );
}
