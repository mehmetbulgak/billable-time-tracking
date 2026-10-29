import { zodResolver } from "@hookform/resolvers/zod";
import LockOutlined from "@mui/icons-material/LockOutlined";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { Navigate, useLocation, useNavigate } from "react-router";
import { z } from "zod";

import { useAppSelector } from "@/app/hooks";
import { getErrorMessage } from "@/shared/api/errors";
import { BrandMark } from "@/shared/components/BrandMark";

import { useLoginMutation } from "./authApi";
import { selectHasSession } from "./authSlice";

const loginSchema = z.object({
  email: z.email("Enter a valid email address."),
  password: z.string().min(1, "Enter your password."),
});

type LoginForm = z.infer<typeof loginSchema>;

const DEMO_ACCOUNTS = [
  { email: "can@northwind.test", label: "Manager" },
  { email: "elif@northwind.test", label: "Team member" },
];

const redirectTarget = (state: unknown): string => {
  if (
    typeof state === "object" &&
    state !== null &&
    "from" in state &&
    typeof state.from === "string"
  ) {
    return state.from;
  }
  return "/";
};

export function LoginPage() {
  const hasSession = useAppSelector(selectHasSession);
  const navigate = useNavigate();
  const location = useLocation();
  const [login, { isLoading, error }] = useLoginMutation();
  const [pendingDemoEmail, setPendingDemoEmail] = useState<string | null>(null);
  const { control, handleSubmit } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  if (hasSession) {
    return <Navigate to="/" replace />;
  }

  const signIn = async (values: LoginForm, demo = false) => {
    if (isLoading) {
      return;
    }
    setPendingDemoEmail(demo ? values.email : null);
    const result = await login(values);
    if (!("error" in result)) {
      await navigate(redirectTarget(location.state), { replace: true });
    }
  };
  const onSubmit = handleSubmit((values) => signIn(values));

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        px: 2,
        background: (theme) =>
          `radial-gradient(circle at top left, ${theme.palette.primary.light}33, transparent 45%), ${theme.palette.background.default}`,
      }}
    >
      <Card sx={{ width: "100%", maxWidth: 420 }}>
        <CardContent sx={{ p: 4 }}>
          <Stack spacing={3} component="form" onSubmit={onSubmit} noValidate>
            <Stack spacing={1} sx={{ alignItems: "center", textAlign: "center" }}>
              <BrandMark size={44} />
              <Typography variant="h5">Sign in to Billable</Typography>
              <Typography variant="body2" color="text.secondary">
                Track time, manage retainers and invoice your clients.
              </Typography>
            </Stack>
            {error ? <Alert severity="error">{getErrorMessage(error)}</Alert> : null}
            <Controller
              name="email"
              control={control}
              render={({ field: { ref, ...field }, fieldState }) => (
                <TextField
                  {...field}
                  inputRef={ref}
                  label="Email"
                  type="email"
                  autoComplete="email"
                  autoFocus
                  disabled={isLoading}
                  error={Boolean(fieldState.error)}
                  helperText={fieldState.error?.message}
                />
              )}
            />
            <Controller
              name="password"
              control={control}
              render={({ field: { ref, ...field }, fieldState }) => (
                <TextField
                  {...field}
                  inputRef={ref}
                  label="Password"
                  type="password"
                  autoComplete="current-password"
                  disabled={isLoading}
                  error={Boolean(fieldState.error)}
                  helperText={fieldState.error?.message}
                />
              )}
            />
            <Button
              type="submit"
              variant="contained"
              size="large"
              disabled={isLoading}
              loading={isLoading && pendingDemoEmail === null}
              startIcon={<LockOutlined />}
            >
              Sign in
            </Button>
            <Stack spacing={1}>
              <Typography variant="caption" color="text.secondary" sx={{ textAlign: "center" }}>
                Try the demo agency
              </Typography>
              <Stack direction="row" spacing={1}>
                {DEMO_ACCOUNTS.map((account) => (
                  <Button
                    key={account.email}
                    type="button"
                    variant="outlined"
                    size="small"
                    fullWidth
                    disabled={isLoading}
                    loading={isLoading && pendingDemoEmail === account.email}
                    onClick={() => {
                      void signIn({ email: account.email, password: "billable-demo" }, true);
                    }}
                  >
                    {account.label}
                  </Button>
                ))}
              </Stack>
            </Stack>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
}
