import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { skipToken } from "@reduxjs/toolkit/query";
import { useState } from "react";
import { useNavigate } from "react-router";

import { useListClientsQuery } from "@/features/clients/clientsApi";
import { getErrorMessage } from "@/shared/api/errors";
import { LoadingState } from "@/shared/components/LoadingState";
import { useNotify } from "@/shared/feedback/useNotify";
import { formatHours } from "@/shared/lib/format";
import { currentPeriod, periodLabel, recentPeriods, shiftPeriod } from "@/shared/lib/period";

import { InvoiceLinesTable } from "./InvoiceLinesTable";
import { useGenerateInvoiceMutation, usePreviewInvoiceQuery } from "./invoicesApi";

export function GenerateInvoiceDialog({ onClose }: { onClose: () => void }) {
  const navigate = useNavigate();
  const notify = useNotify();
  const [clientId, setClientId] = useState<number | "">("");
  const [period, setPeriod] = useState(() => shiftPeriod(currentPeriod(), -1));
  const { data: clients } = useListClientsQuery({ is_archived: false });
  const client = clients?.results.find((candidate) => candidate.id === clientId);
  const preview = usePreviewInvoiceQuery(client ? { client: client.id, period } : skipToken);
  const [generateInvoice, generateState] = useGenerateInvoiceMutation();

  const generate = async () => {
    if (!client) {
      return;
    }
    const result = await generateInvoice({ client: client.id, period });
    if ("error" in result) {
      return;
    }
    notify.success(`Draft invoice created for ${client.name}`);
    onClose();
    await navigate(`/invoices/${result.data.id}`);
  };

  const renderPreview = () => {
    if (!client) {
      return (
        <Typography variant="body2" color="text.secondary">
          Choose a client to preview the invoice.
        </Typography>
      );
    }
    if (preview.isFetching) {
      return <LoadingState minHeight={120} />;
    }
    if (preview.error || !preview.currentData) {
      return <Alert severity="warning">{getErrorMessage(preview.error)}</Alert>;
    }
    if (preview.currentData.is_empty) {
      return (
        <Alert severity="info">
          There is no billable work for {client.name} in {periodLabel(period)}.
        </Alert>
      );
    }
    return (
      <Stack spacing={1.5}>
        {preview.currentData.replaces_draft === null ? null : (
          <Alert severity="info">
            A draft for this period already exists. Creating a new one replaces it with the figures
            below.
          </Alert>
        )}
        <Typography variant="body2" color="text.secondary">
          {formatHours(preview.currentData.billable_hours)} billable after rounding (
          {formatHours(preview.currentData.tracked_hours)} tracked)
        </Typography>
        <InvoiceLinesTable
          lines={preview.currentData.lines}
          currency={client.currency}
          totals={[{ label: "Subtotal", amount: preview.currentData.subtotal, emphasize: true }]}
        />
      </Stack>
    );
  };

  const canGenerate = Boolean(
    client &&
    preview.currentData &&
    !preview.currentData.is_empty &&
    !preview.error &&
    !preview.isFetching,
  );
  const replacesDraft = typeof preview.currentData?.replaces_draft === "number";

  return (
    <Dialog open onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Generate invoice</DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ pt: 1 }}>
          {generateState.error ? (
            <Alert severity="error">{getErrorMessage(generateState.error)}</Alert>
          ) : null}
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <TextField
              select
              label="Client"
              value={clientId}
              onChange={(event) => {
                setClientId(Number(event.target.value));
              }}
              fullWidth
            >
              {(clients?.results ?? []).map((option) => (
                <MenuItem key={option.id} value={option.id}>
                  {option.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="Period"
              value={period}
              onChange={(event) => {
                setPeriod(event.target.value);
              }}
              fullWidth
            >
              {recentPeriods(12).map((option) => (
                <MenuItem key={option} value={option}>
                  {periodLabel(option)}
                </MenuItem>
              ))}
            </TextField>
          </Stack>
          {renderPreview()}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          disabled={!canGenerate}
          loading={generateState.isLoading}
          onClick={() => void generate()}
        >
          {replacesDraft ? "Replace draft" : "Create draft"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
