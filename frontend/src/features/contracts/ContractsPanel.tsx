import AddRounded from "@mui/icons-material/AddRounded";
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import Stack from "@mui/material/Stack";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import dayjs, { type Dayjs } from "dayjs";
import { useState } from "react";

import { getErrorMessage } from "@/shared/api/errors";
import type { Client, Contract } from "@/shared/api/types";
import { ConfirmDialog } from "@/shared/components/ConfirmDialog";
import { EmptyState } from "@/shared/components/EmptyState";
import { ErrorState } from "@/shared/components/ErrorState";
import { LoadingState } from "@/shared/components/LoadingState";
import { useNotify } from "@/shared/feedback/useNotify";
import { formatDate, formatHours } from "@/shared/lib/format";

import { ContractDialog } from "./ContractDialog";
import {
  useDeleteContractMutation,
  useListContractsQuery,
  useUpdateContractMutation,
} from "./contractsApi";
import { BILLING_MODEL_LABELS, describeContract, isContractActive } from "./contractTerms";

function EndContractDialog({ contract, onClose }: { contract: Contract; onClose: () => void }) {
  const notify = useNotify();
  const [endsOn, setEndsOn] = useState<Dayjs | null>(
    contract.ends_on ? dayjs(contract.ends_on) : dayjs().endOf("month"),
  );
  const [updateContract, { isLoading, error }] = useUpdateContractMutation();

  const save = async () => {
    const result = await updateContract({
      id: contract.id,
      ends_on: endsOn ? endsOn.format("YYYY-MM-DD") : null,
    });
    if (!("error" in result)) {
      notify.success("Contract end date saved");
      onClose();
    }
  };

  return (
    <Dialog open onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle>Contract end date</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          {error ? <Alert severity="error">{getErrorMessage(error)}</Alert> : null}
          <DatePicker
            label="Ends on"
            value={endsOn}
            minDate={dayjs(contract.starts_on)}
            onChange={setEndsOn}
            slotProps={{ field: { clearable: true }, textField: { fullWidth: true } }}
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" loading={isLoading} onClick={() => void save()}>
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function ContractCard({
  contract,
  client,
  onEnd,
  onDelete,
}: {
  contract: Contract;
  client: Client;
  onEnd: () => void;
  onDelete: () => void;
}) {
  const active = isContractActive(contract, dayjs().format("YYYY-MM-DD"));

  return (
    <Card>
      <CardContent>
        <Stack
          direction={{ xs: "column", md: "row" }}
          spacing={2}
          sx={{ justifyContent: "space-between" }}
        >
          <Stack spacing={1}>
            <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
              <Typography variant="subtitle1">
                {BILLING_MODEL_LABELS[contract.billing_model]}
              </Typography>
              <Chip
                size="small"
                color={active ? "success" : "default"}
                label={active ? "Active" : "Inactive"}
                variant={active ? "filled" : "outlined"}
              />
            </Stack>
            <Typography variant="body2">{describeContract(contract, client.currency)}</Typography>
            <Typography variant="body2" color="text.secondary">
              {formatDate(contract.starts_on)} –{" "}
              {contract.ends_on ? formatDate(contract.ends_on) : "open-ended"}
              {" · "}rounded up to {contract.rounding_increment_minutes} min
              {contract.billing_model === "retainer"
                ? ` · rollover up to ${formatHours(contract.rollover_cap_hours)}`
                : ""}
            </Typography>
          </Stack>
          <Stack direction="row" spacing={1} sx={{ alignItems: "flex-start" }}>
            <Button size="small" onClick={onEnd}>
              {contract.ends_on ? "Change end date" : "Set end date"}
            </Button>
            <Tooltip
              title={
                contract.has_invoices
                  ? "Invoiced contracts are kept for the record. Set an end date instead."
                  : ""
              }
            >
              <span>
                <Button
                  size="small"
                  color="error"
                  disabled={contract.has_invoices}
                  onClick={onDelete}
                >
                  Delete
                </Button>
              </span>
            </Tooltip>
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
}

export function ContractsPanel({ client }: { client: Client }) {
  const notify = useNotify();
  const [creating, setCreating] = useState(false);
  const [ending, setEnding] = useState<Contract | null>(null);
  const [deleting, setDeleting] = useState<Contract | null>(null);
  const { data, isLoading, error, refetch } = useListContractsQuery({ client: client.id });
  const [deleteContract, deleteState] = useDeleteContractMutation();

  const confirmDelete = async () => {
    if (!deleting) {
      return;
    }
    const result = await deleteContract(deleting.id);
    if ("error" in result) {
      notify.error(result.error);
    } else {
      notify.success("Contract deleted");
    }
    setDeleting(null);
  };

  if (isLoading) {
    return <LoadingState />;
  }
  if (error || !data) {
    return <ErrorState error={error} onRetry={() => void refetch()} />;
  }

  return (
    <Stack spacing={2}>
      <Stack direction="row" sx={{ justifyContent: "flex-end" }}>
        <Button
          variant="contained"
          startIcon={<AddRounded />}
          onClick={() => {
            setCreating(true);
          }}
        >
          New contract
        </Button>
      </Stack>
      {data.results.length === 0 ? (
        <Card>
          <EmptyState
            title="No contracts yet"
            description="Add a contract to decide how this client's time turns into invoices."
          />
        </Card>
      ) : (
        data.results.map((contract) => (
          <ContractCard
            key={contract.id}
            contract={contract}
            client={client}
            onEnd={() => {
              setEnding(contract);
            }}
            onDelete={() => {
              setDeleting(contract);
            }}
          />
        ))
      )}
      {creating ? (
        <ContractDialog
          client={client}
          onClose={() => {
            setCreating(false);
          }}
        />
      ) : null}
      {ending ? (
        <EndContractDialog
          contract={ending}
          onClose={() => {
            setEnding(null);
          }}
        />
      ) : null}
      <ConfirmDialog
        open={deleting !== null}
        title="Delete contract?"
        description="Contracts that already have invoices cannot be deleted. Set an end date instead."
        confirmLabel="Delete"
        destructive
        loading={deleteState.isLoading}
        onConfirm={() => void confirmDelete()}
        onClose={() => {
          setDeleting(null);
        }}
      />
    </Stack>
  );
}
