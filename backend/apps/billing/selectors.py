from django.db.models import Count, Q, QuerySet

from apps.billing.models import Contract, Invoice, InvoiceStatus
from apps.clients.models import Client
from apps.core.periods import MonthPeriod
from apps.timetracking.models import TimeEntry


def contract_for_period(client: Client, period: MonthPeriod) -> Contract | None:
    return (
        Contract.objects.filter(client=client)
        .overlapping(period.first_day, period.last_day)
        .order_by("-starts_on")
        .first()
    )


def active_invoice_for_period(client: Client, period: MonthPeriod) -> Invoice | None:
    return Invoice.objects.active().for_period(period).filter(client=client).first()


def invoiceable_entries(client: Client, period: MonthPeriod) -> QuerySet[TimeEntry]:
    start, end = period.bounds(client.organization.tzinfo)
    return (
        TimeEntry.objects.finished()
        .billable()
        .started_between(start, end)
        .filter(project__client=client)
        .filter(Q(invoice__isnull=True) | Q(invoice__status=InvoiceStatus.DRAFT))
        .order_by("started_at")
    )


def invoices_with_related(queryset: QuerySet[Invoice]) -> QuerySet[Invoice]:
    return (
        queryset.select_related("client", "contract")
        .annotate(time_entry_count=Count("time_entries", distinct=True))
        .order_by("-period_start", "client__name", "-pk")
    )


def invoice_detail(queryset: QuerySet[Invoice]) -> QuerySet[Invoice]:
    return invoices_with_related(queryset).prefetch_related("lines")
