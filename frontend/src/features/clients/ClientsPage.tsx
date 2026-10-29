import AddRounded from "@mui/icons-material/AddRounded";
import SearchRounded from "@mui/icons-material/SearchRounded";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import FormControlLabel from "@mui/material/FormControlLabel";
import InputAdornment from "@mui/material/InputAdornment";
import Stack from "@mui/material/Stack";
import Switch from "@mui/material/Switch";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import dayjs from "dayjs";
import { useDeferredValue, useMemo, useState } from "react";
import { useNavigate } from "react-router";

import { useListContractsQuery } from "@/features/contracts/contractsApi";
import {
  BILLING_MODEL_LABELS,
  describeContract,
  isContractActive,
} from "@/features/contracts/contractTerms";
import type { Contract } from "@/shared/api/types";
import { EmptyState } from "@/shared/components/EmptyState";
import { ErrorState } from "@/shared/components/ErrorState";
import { LoadingState } from "@/shared/components/LoadingState";
import { PageHeader } from "@/shared/components/PageHeader";

import { ClientDialog } from "./ClientDialog";
import { useListClientsQuery } from "./clientsApi";

export function ClientsPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [showArchived, setShowArchived] = useState(false);
  const [creating, setCreating] = useState(false);
  const deferredSearch = useDeferredValue(search.trim());
  const { data, isLoading, error, refetch } = useListClientsQuery({
    search: deferredSearch || undefined,
    is_archived: showArchived ? undefined : false,
  });
  const { data: contracts } = useListContractsQuery({});

  const activeContracts = useMemo(() => {
    const today = dayjs().format("YYYY-MM-DD");
    const byClient = new Map<number, Contract>();
    for (const contract of contracts?.results ?? []) {
      if (isContractActive(contract, today)) {
        byClient.set(contract.client, contract);
      }
    }
    return byClient;
  }, [contracts]);

  const clients = data?.results ?? [];

  const renderTable = () => {
    if (isLoading) {
      return <LoadingState />;
    }
    if (error) {
      return <ErrorState error={error} onRetry={() => void refetch()} />;
    }
    if (clients.length === 0) {
      return (
        <EmptyState
          title={deferredSearch ? "No clients match your search" : "No clients yet"}
          description="Add your first client to start tracking billable work."
        />
      );
    }
    return (
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Client</TableCell>
              <TableCell>Contract</TableCell>
              <TableCell>Currency</TableCell>
              <TableCell align="right">Tax</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {clients.map((client) => {
              const contract = activeContracts.get(client.id);
              return (
                <TableRow
                  key={client.id}
                  hover
                  sx={{ cursor: "pointer" }}
                  onClick={() => void navigate(`/clients/${client.id}`)}
                >
                  <TableCell>
                    <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                      <Stack>
                        <Typography variant="subtitle2">{client.name}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {client.contact_name || client.email || "No contact details"}
                        </Typography>
                      </Stack>
                      {client.is_archived ? <Chip size="small" label="Archived" /> : null}
                    </Stack>
                  </TableCell>
                  <TableCell>
                    {contract ? (
                      <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                        <Chip
                          size="small"
                          color="primary"
                          variant="outlined"
                          label={BILLING_MODEL_LABELS[contract.billing_model]}
                        />
                        <Typography variant="body2" color="text.secondary">
                          {describeContract(contract, client.currency)}
                        </Typography>
                      </Stack>
                    ) : (
                      <Typography variant="body2" color="text.disabled">
                        No active contract
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>{client.currency}</TableCell>
                  <TableCell align="right">{Number(client.tax_rate)}%</TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  return (
    <>
      <PageHeader
        title="Clients"
        subtitle="Contracts define how each client's time is billed."
        actions={
          <Button
            variant="contained"
            startIcon={<AddRounded />}
            onClick={() => {
              setCreating(true);
            }}
          >
            New client
          </Button>
        }
      />
      <Card>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={2}
          sx={{ p: 2, alignItems: "center" }}
        >
          <TextField
            size="small"
            placeholder="Search clients"
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
            }}
            sx={{ flexGrow: 1 }}
            slotProps={{
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchRounded fontSize="small" />
                  </InputAdornment>
                ),
              },
            }}
          />
          <FormControlLabel
            control={
              <Switch
                checked={showArchived}
                onChange={(event) => {
                  setShowArchived(event.target.checked);
                }}
              />
            }
            label="Show archived"
          />
        </Stack>
        {renderTable()}
      </Card>
      {creating ? (
        <ClientDialog
          client={null}
          onClose={() => {
            setCreating(false);
          }}
          onCreated={(client) => void navigate(`/clients/${client.id}`)}
        />
      ) : null}
    </>
  );
}
