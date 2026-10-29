import csv
import io
from collections.abc import Iterable

from apps.billing.models import Invoice
from apps.core.money import minutes_to_hours
from apps.timetracking.models import TimeEntry


def _write_section(writer: csv.DictWriter[str], rows: Iterable[dict[str, object]]) -> None:
    writer.writeheader()
    writer.writerows(rows)


def invoice_csv(invoice: Invoice, entries: Iterable[TimeEntry]) -> str:
    buffer = io.StringIO()
    summary = csv.writer(buffer)
    summary.writerow(["Invoice", invoice.number or "DRAFT"])
    summary.writerow(["Client", invoice.client.name])
    summary.writerow(["Period", f"{invoice.period_start:%Y-%m-%d} - {invoice.period_end:%Y-%m-%d}"])
    summary.writerow(["Currency", invoice.currency])
    summary.writerow([])

    _write_section(
        csv.DictWriter(buffer, fieldnames=["description", "quantity", "unit_price", "amount"]),
        (
            {
                "description": line.description,
                "quantity": line.quantity,
                "unit_price": line.unit_price,
                "amount": line.amount,
            }
            for line in invoice.lines.all()
        ),
    )
    summary.writerow(["", "", "Subtotal", invoice.subtotal])
    summary.writerow(["", "", f"Tax ({invoice.tax_rate}%)", invoice.tax_amount])
    summary.writerow(["", "", "Total", invoice.total])
    summary.writerow([])

    _write_section(
        csv.DictWriter(
            buffer,
            fieldnames=["date", "member", "project", "description", "hours"],
        ),
        (
            {
                "date": f"{entry.started_at:%Y-%m-%d}",
                "member": entry.user.full_name,
                "project": entry.project.name,
                "description": entry.description,
                "hours": minutes_to_hours(entry.duration_seconds // 60),
            }
            for entry in entries
        ),
    )
    return buffer.getvalue()
