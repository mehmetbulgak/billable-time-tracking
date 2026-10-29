import Chip from "@mui/material/Chip";

import type { InvoiceStatus } from "@/shared/api/types";

const STATUS_COLORS: Record<InvoiceStatus, "default" | "info" | "success" | "warning"> = {
  draft: "default",
  issued: "info",
  paid: "success",
  void: "warning",
};

export function InvoiceStatusChip({ status }: { status: InvoiceStatus }) {
  return (
    <Chip
      size="small"
      label={status}
      color={STATUS_COLORS[status]}
      variant={status === "draft" ? "outlined" : "filled"}
      sx={{ textTransform: "capitalize" }}
    />
  );
}
