import AddRounded from "@mui/icons-material/AddRounded";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Pagination from "@mui/material/Pagination";
import Stack from "@mui/material/Stack";
import Tab from "@mui/material/Tab";
import Tabs from "@mui/material/Tabs";
import { useState } from "react";

import type { InvoiceStatus } from "@/shared/api/types";
import { EmptyState } from "@/shared/components/EmptyState";
import { ErrorState } from "@/shared/components/ErrorState";
import { LoadingState } from "@/shared/components/LoadingState";
import { PageHeader } from "@/shared/components/PageHeader";

import { GenerateInvoiceDialog } from "./GenerateInvoiceDialog";
import { InvoiceTable } from "./InvoiceTable";
import { useListInvoicesQuery } from "./invoicesApi";

type StatusFilter = InvoiceStatus | "all";

const PAGE_SIZE = 25;

const STATUS_TABS: { value: StatusFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "draft", label: "Drafts" },
  { value: "issued", label: "Issued" },
  { value: "paid", label: "Paid" },
  { value: "void", label: "Void" },
];

export function InvoicesPage() {
  const [status, setStatus] = useState<StatusFilter>("all");
  const [page, setPage] = useState(1);
  const [generating, setGenerating] = useState(false);
  const { data, isLoading, isFetching, error, refetch } = useListInvoicesQuery({
    status: status === "all" ? undefined : status,
    page,
  });
  const pageCount = data ? Math.ceil(data.count / PAGE_SIZE) : 0;

  const renderContent = () => {
    if (isLoading) {
      return <LoadingState />;
    }
    if (error || !data) {
      return <ErrorState error={error} onRetry={() => void refetch()} />;
    }
    if (data.results.length === 0) {
      return (
        <EmptyState
          title="No invoices here"
          description="Drafts are created automatically on the first day of each month, or you can generate one now."
        />
      );
    }
    return (
      <Box sx={{ opacity: isFetching ? 0.6 : 1, transition: "opacity 150ms" }}>
        <InvoiceTable invoices={data.results} />
      </Box>
    );
  };

  return (
    <>
      <PageHeader
        title="Invoices"
        subtitle="Review drafts, issue invoices and track payments."
        actions={
          <Button
            variant="contained"
            startIcon={<AddRounded />}
            onClick={() => {
              setGenerating(true);
            }}
          >
            Generate invoice
          </Button>
        }
      />
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: "divider", px: 2 }}>
          <Tabs
            value={status}
            onChange={(_event, value: StatusFilter) => {
              setStatus(value);
              setPage(1);
            }}
          >
            {STATUS_TABS.map((tab) => (
              <Tab key={tab.value} value={tab.value} label={tab.label} />
            ))}
          </Tabs>
        </Box>
        {renderContent()}
        {pageCount > 1 ? (
          <Stack sx={{ p: 2, alignItems: "center" }}>
            <Pagination
              count={pageCount}
              page={page}
              onChange={(_event, value) => {
                setPage(value);
              }}
            />
          </Stack>
        ) : null}
      </Card>
      {generating ? (
        <GenerateInvoiceDialog
          onClose={() => {
            setGenerating(false);
          }}
        />
      ) : null}
    </>
  );
}
