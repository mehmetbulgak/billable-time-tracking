import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import { useNavigate } from "react-router";

import type { Invoice } from "@/shared/api/types";
import { formatDate, formatHours, formatMoney } from "@/shared/lib/format";
import { periodLabel } from "@/shared/lib/period";

import { InvoiceStatusChip } from "./InvoiceStatusChip";

interface InvoiceTableProps {
  invoices: Invoice[];
  showClient?: boolean;
}

export function InvoiceTable({ invoices, showClient = true }: InvoiceTableProps) {
  const navigate = useNavigate();

  return (
    <TableContainer>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Invoice</TableCell>
            {showClient ? <TableCell>Client</TableCell> : null}
            <TableCell>Period</TableCell>
            <TableCell align="right">Hours</TableCell>
            <TableCell align="right">Total</TableCell>
            <TableCell>Due</TableCell>
            <TableCell>Status</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {invoices.map((invoice) => (
            <TableRow
              key={invoice.id}
              hover
              sx={{ cursor: "pointer" }}
              onClick={() => void navigate(`/invoices/${invoice.id}`)}
            >
              <TableCell>
                <Typography
                  variant="subtitle2"
                  color={invoice.number ? "text.primary" : "text.secondary"}
                >
                  {invoice.number || "Draft"}
                </Typography>
              </TableCell>
              {showClient ? <TableCell>{invoice.client.name}</TableCell> : null}
              <TableCell>{periodLabel(invoice.period_start.slice(0, 7))}</TableCell>
              <TableCell align="right">{formatHours(invoice.billable_hours)}</TableCell>
              <TableCell align="right" sx={{ fontVariantNumeric: "tabular-nums" }}>
                {formatMoney(invoice.total, invoice.currency)}
              </TableCell>
              <TableCell>{formatDate(invoice.due_date)}</TableCell>
              <TableCell>
                <InvoiceStatusChip status={invoice.status} />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
