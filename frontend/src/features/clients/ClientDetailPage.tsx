import ArchiveOutlined from "@mui/icons-material/ArchiveOutlined";
import ArrowBackRounded from "@mui/icons-material/ArrowBackRounded";
import EditOutlined from "@mui/icons-material/EditOutlined";
import UnarchiveOutlined from "@mui/icons-material/UnarchiveOutlined";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import { useState } from "react";
import { Link as RouterLink, useParams } from "react-router";

import { ContractsPanel } from "@/features/contracts/ContractsPanel";
import { InvoiceTable } from "@/features/invoices/InvoiceTable";
import { useListInvoicesQuery } from "@/features/invoices/invoicesApi";
import { ProjectsPanel } from "@/features/projects/ProjectsPanel";
import type { Client } from "@/shared/api/types";
import { EmptyState } from "@/shared/components/EmptyState";
import { ErrorState } from "@/shared/components/ErrorState";
import { LoadingState } from "@/shared/components/LoadingState";
import { PageHeader } from "@/shared/components/PageHeader";
import { useNotify } from "@/shared/feedback/useNotify";

import { ClientDialog } from "./ClientDialog";
import { useGetClientQuery, useUpdateClientMutation } from "./clientsApi";

type ClientTab = "contracts" | "projects" | "invoices";

function ClientInvoices({ client }: { client: Client }) {
  const { data, isLoading, error, refetch } = useListInvoicesQuery({ client: client.id });
  if (isLoading) {
    return <LoadingState />;
  }
  if (error || !data) {
    return <ErrorState error={error} onRetry={() => void refetch()} />;
  }
  return (
    <Card>
      {data.results.length === 0 ? (
        <EmptyState title="No invoices yet" />
      ) : (
        <InvoiceTable invoices={data.results} showClient={false} />
      )}
    </Card>
  );
}

export function ClientDetailPage() {
  const clientId = Number(useParams().clientId);
  const notify = useNotify();
  const [tab, setTab] = useState<ClientTab>("contracts");
  const [editing, setEditing] = useState(false);
  const { data: client, isLoading, error, refetch } = useGetClientQuery(clientId);
  const [updateClient, updateState] = useUpdateClientMutation();

  if (isLoading) {
    return <LoadingState />;
  }
  if (error || !client) {
    return <ErrorState error={error} onRetry={() => void refetch()} />;
  }

  const toggleArchived = async () => {
    const result = await updateClient({ id: client.id, is_archived: !client.is_archived });
    if ("error" in result) {
      notify.error(result.error);
    } else {
      notify.success(client.is_archived ? "Client restored" : "Client archived");
    }
  };

  return (
    <>
      <Button component={RouterLink} to="/clients" startIcon={<ArrowBackRounded />} sx={{ mb: 1 }}>
        Clients
      </Button>
      <PageHeader
        title={client.name}
        subtitle={
          <Stack direction="row" spacing={1} sx={{ mt: 0.5, flexWrap: "wrap" }}>
            <Chip size="small" label={client.currency} />
            <Chip size="small" label={`Tax ${Number(client.tax_rate)}%`} />
            {client.email ? <Chip size="small" variant="outlined" label={client.email} /> : null}
            {client.is_archived ? <Chip size="small" color="warning" label="Archived" /> : null}
          </Stack>
        }
        actions={
          <>
            <Button
              startIcon={client.is_archived ? <UnarchiveOutlined /> : <ArchiveOutlined />}
              loading={updateState.isLoading}
              onClick={() => void toggleArchived()}
            >
              {client.is_archived ? "Restore" : "Archive"}
            </Button>
            <Button
              variant="outlined"
              startIcon={<EditOutlined />}
              onClick={() => {
                setEditing(true);
              }}
            >
              Edit
            </Button>
          </>
        }
      />
      <Box sx={{ borderBottom: 1, borderColor: "divider", mb: 3 }}>
        <Tabs
          value={tab}
          onChange={(_event, value: ClientTab) => {
            setTab(value);
          }}
        >
          <Tab value="contracts" label="Contracts" />
          <Tab value="projects" label="Projects" />
          <Tab value="invoices" label="Invoices" />
        </Tabs>
      </Box>
      {tab === "contracts" ? <ContractsPanel client={client} /> : null}
      {tab === "projects" ? <ProjectsPanel client={client} /> : null}
      {tab === "invoices" ? <ClientInvoices client={client} /> : null}
      {editing ? (
        <ClientDialog
          client={client}
          onClose={() => {
            setEditing(false);
          }}
        />
      ) : null}
    </>
  );
}
