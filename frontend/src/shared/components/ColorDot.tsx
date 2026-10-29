import Box from "@mui/material/Box";

interface ColorDotProps {
  color: string;
  size?: number;
}

export function ColorDot({ color, size = 10 }: ColorDotProps) {
  return (
    <Box
      component="span"
      aria-hidden
      sx={{
        display: "inline-block",
        width: size,
        height: size,
        borderRadius: "50%",
        bgcolor: color,
        flexShrink: 0,
      }}
    />
  );
}
