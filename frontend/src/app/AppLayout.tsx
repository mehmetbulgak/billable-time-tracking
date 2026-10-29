import AccessTimeOutlined from "@mui/icons-material/AccessTimeOutlined";
import BusinessOutlined from "@mui/icons-material/BusinessOutlined";
import DashboardOutlined from "@mui/icons-material/DashboardOutlined";
import GroupOutlined from "@mui/icons-material/GroupOutlined";
import LogoutOutlined from "@mui/icons-material/LogoutOutlined";
import MenuIcon from "@mui/icons-material/Menu";
import ReceiptLongOutlined from "@mui/icons-material/ReceiptLongOutlined";
import AppBar from "@mui/material/AppBar";
import Alert from "@mui/material/Alert";
import Avatar from "@mui/material/Avatar";
import Box from "@mui/material/Box";
import Divider from "@mui/material/Divider";
import Drawer from "@mui/material/Drawer";
import IconButton from "@mui/material/IconButton";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import Stack from "@mui/material/Stack";
import Toolbar from "@mui/material/Toolbar";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import useMediaQuery from "@mui/material/useMediaQuery";
import { useTheme } from "@mui/material/styles";
import { useState, type ReactNode } from "react";
import { NavLink, Outlet, useNavigate } from "react-router";

import { ConnectionIndicator } from "@/features/activity/ConnectionIndicator";
import { useActivityStream } from "@/features/activity/useActivityStream";
import { useLogoutMutation } from "@/features/auth/authApi";
import { useCurrentUser } from "@/features/auth/useCurrentUser";
import { TimerBar } from "@/features/timer/TimerBar";
import { BrandMark } from "@/shared/components/BrandMark";

const DRAWER_WIDTH = 248;

interface NavItem {
  to: string;
  label: string;
  icon: ReactNode;
  managerOnly?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Dashboard", icon: <DashboardOutlined /> },
  { to: "/timesheet", label: "Timesheet", icon: <AccessTimeOutlined /> },
  { to: "/clients", label: "Clients", icon: <BusinessOutlined />, managerOnly: true },
  { to: "/invoices", label: "Invoices", icon: <ReceiptLongOutlined />, managerOnly: true },
  { to: "/team", label: "Team", icon: <GroupOutlined /> },
];

function Navigation({ onNavigate }: { onNavigate: () => void }) {
  const user = useCurrentUser();
  const [logout, { isLoading: signingOut, isError: signOutFailed }] = useLogoutMutation();
  const navigate = useNavigate();
  const items = NAV_ITEMS.filter((item) => !item.managerOnly || user.is_manager);

  return (
    <Stack sx={{ height: "100%" }}>
      <Stack direction="row" spacing={1.5} sx={{ alignItems: "center", px: 2.5, height: 64 }}>
        <BrandMark size={32} />
        <Stack>
          <Typography variant="subtitle1" sx={{ lineHeight: 1.2 }}>
            Billable
          </Typography>
          <Typography variant="caption" color="text.secondary" noWrap>
            {user.organization.name}
          </Typography>
        </Stack>
      </Stack>
      <Divider />
      <List sx={{ px: 1.5, py: 2, flexGrow: 1 }}>
        {items.map((item) => (
          <ListItemButton
            key={item.to}
            component={NavLink}
            to={item.to}
            end={item.to === "/"}
            onClick={onNavigate}
            sx={{ mb: 0.5 }}
          >
            <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
      </List>
      <Divider />
      {signOutFailed ? <Alert severity="error">Sign out failed. Please try again.</Alert> : null}
      <Stack direction="row" spacing={1.5} sx={{ alignItems: "center", p: 2 }}>
        <Avatar sx={{ width: 36, height: 36, bgcolor: "primary.main", fontSize: 14 }}>
          {user.first_name.charAt(0)}
          {user.last_name.charAt(0)}
        </Avatar>
        <Stack sx={{ minWidth: 0, flexGrow: 1 }}>
          <Typography variant="subtitle2" noWrap>
            {user.full_name}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ textTransform: "capitalize" }}>
            {user.role}
          </Typography>
        </Stack>
        <Tooltip title="Sign out">
          <IconButton
            aria-label="Sign out"
            disabled={signingOut}
            onClick={async () => {
              try {
                await logout().unwrap();
                await navigate("/login");
              } catch {
                return;
              }
            }}
          >
            <LogoutOutlined fontSize="small" />
          </IconButton>
        </Tooltip>
      </Stack>
    </Stack>
  );
}

export function AppLayout() {
  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up("md"));
  const [mobileOpen, setMobileOpen] = useState(false);
  const connection = useActivityStream();

  const closeMobile = () => {
    setMobileOpen(false);
  };

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <Drawer
        variant={isDesktop ? "permanent" : "temporary"}
        open={isDesktop || mobileOpen}
        onClose={closeMobile}
        sx={{
          width: DRAWER_WIDTH,
          flexShrink: 0,
          "& .MuiDrawer-paper": { width: DRAWER_WIDTH, boxSizing: "border-box" },
        }}
      >
        <Navigation onNavigate={closeMobile} />
      </Drawer>
      <Box sx={{ flexGrow: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
        <AppBar position="sticky">
          <Toolbar sx={{ gap: 2, minHeight: 64 }}>
            {isDesktop ? null : (
              <IconButton
                edge="start"
                aria-label="Open navigation"
                onClick={() => {
                  setMobileOpen(true);
                }}
              >
                <MenuIcon />
              </IconButton>
            )}
            <TimerBar />
            <ConnectionIndicator status={connection} />
          </Toolbar>
        </AppBar>
        {import.meta.env.VITE_DEMO_MODE === "true" ? (
          <Alert severity="info" sx={{ borderRadius: 0 }}>
            Interactive demo · Shared sample data resets when the server restarts.
          </Alert>
        ) : null}
        <Box
          component="main"
          sx={{ flexGrow: 1, p: { xs: 2, md: 4 }, maxWidth: 1440, width: "100%" }}
        >
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}
