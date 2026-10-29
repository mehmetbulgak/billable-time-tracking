import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import type { ReactNode } from "react";

import type { BillingPreviewLine, Currency } from "@/shared/api/types";
import { formatMoney, toNumber } from "@/shared/lib/format";

interface TotalRow {
  label: ReactNode;
  amount: string;
  emphasize?: boolean;
}

interface InvoiceLinesTableProps {
  lines: BillingPreviewLine[];
  currency: Currency;
  totals: TotalRow[];
}

export function InvoiceLinesTable({ lines, currency, totals }: InvoiceLinesTableProps) {
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell>Description</TableCell>
          <TableCell align="right">Quantity</TableCell>
          <TableCell align="right">Unit price</TableCell>
          <TableCell align="right">Amount</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {lines.map((line) => (
          <TableRow key={`${line.kind}-${line.description}`}>
            <TableCell>
              <Typography
                variant="body2"
                color={toNumber(line.amount) === 0 ? "text.secondary" : "text.primary"}
              >
                {line.description}
              </Typography>
            </TableCell>
            <TableCell align="right">{toNumber(line.quantity)}</TableCell>
            <TableCell align="right">{formatMoney(line.unit_price, currency)}</TableCell>
            <TableCell align="right" sx={{ fontVariantNumeric: "tabular-nums" }}>
              {formatMoney(line.amount, currency)}
            </TableCell>
          </TableRow>
        ))}
        {totals.map((row, index) => (
          <TableRow key={index}>
            <TableCell colSpan={3} align="right" sx={{ borderBottom: "none" }}>
              <Typography variant={row.emphasize ? "subtitle1" : "body2"}>{row.label}</Typography>
            </TableCell>
            <TableCell
              align="right"
              sx={{ borderBottom: "none", fontVariantNumeric: "tabular-nums" }}
            >
              <Typography variant={row.emphasize ? "subtitle1" : "body2"}>
                {formatMoney(row.amount, currency)}
              </Typography>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
