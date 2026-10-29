import { alpha, createTheme } from "@mui/material/styles";

const borderColor = "#E6E8EF";

export const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#4338CA", light: "#6366F1", dark: "#3730A3" },
    secondary: { main: "#0F766E" },
    success: { main: "#15803D" },
    error: { main: "#DC2626" },
    warning: { main: "#D97706" },
    background: { default: "#F6F7FB", paper: "#FFFFFF" },
    text: { primary: "#111827", secondary: "#5B6475" },
    divider: borderColor,
  },
  shape: { borderRadius: 10 },
  typography: {
    fontFamily: '"Inter Variable", "Inter", system-ui, -apple-system, "Segoe UI", sans-serif',
    h4: { fontWeight: 700, fontSize: "1.75rem", letterSpacing: "-0.02em" },
    h5: { fontWeight: 700, letterSpacing: "-0.01em" },
    h6: { fontWeight: 600 },
    subtitle1: { fontWeight: 600 },
    subtitle2: { fontWeight: 600 },
    overline: { fontWeight: 600, letterSpacing: "0.06em" },
    button: { textTransform: "none", fontWeight: 600 },
  },
  components: {
    MuiButton: {
      defaultProps: { disableElevation: true },
    },
    MuiCard: {
      defaultProps: { variant: "outlined" },
      styleOverrides: { root: { borderColor } },
    },
    MuiCardHeader: {
      defaultProps: {
        slotProps: {
          title: { variant: "subtitle1" },
          subheader: { variant: "body2" },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: ({ theme }) => ({
          fontWeight: 600,
          color: theme.palette.text.secondary,
          backgroundColor: alpha(theme.palette.primary.main, 0.03),
        }),
      },
    },
    MuiChip: {
      styleOverrides: { root: { fontWeight: 600 } },
    },
    MuiAppBar: {
      defaultProps: { elevation: 0, color: "inherit" },
      styleOverrides: { root: { borderBottom: `1px solid ${borderColor}` } },
    },
    MuiDrawer: {
      styleOverrides: { paper: { borderRight: `1px solid ${borderColor}` } },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: ({ theme }) => ({
          borderRadius: theme.shape.borderRadius,
          "&.active": {
            backgroundColor: alpha(theme.palette.primary.main, 0.08),
            color: theme.palette.primary.main,
            "& .MuiListItemIcon-root": { color: theme.palette.primary.main },
          },
        }),
      },
    },
  },
});
