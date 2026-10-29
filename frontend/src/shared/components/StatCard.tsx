import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  icon?: ReactNode;
}

export function StatCard({ label, value, hint, icon }: StatCardProps) {
  return (
    <Card sx={{ height: "100%" }}>
      <CardContent>
        <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "flex-start" }}>
          <Stack spacing={0.75}>
            <Typography variant="overline" color="text.secondary">
              {label}
            </Typography>
            <Typography variant="h5" component="div">
              {value}
            </Typography>
            {hint ? (
              <Typography variant="body2" color="text.secondary" component="div">
                {hint}
              </Typography>
            ) : null}
          </Stack>
          {icon ? <Stack sx={{ color: "primary.main" }}>{icon}</Stack> : null}
        </Stack>
      </CardContent>
    </Card>
  );
}
