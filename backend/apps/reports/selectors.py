from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import DurationField, ExpressionWrapper, F, Q, QuerySet, Sum
from django.db.models.functions import TruncDate

from apps.accounts.models import User
from apps.billing import selectors as billing_selectors
from apps.billing.domain.types import BillingModel
from apps.billing.models import Contract, Invoice, InvoiceStatus
from apps.billing.services.calculations import calculate_invoice
from apps.core.money import minutes_to_hours, quantize_money
from apps.core.periods import MonthPeriod
from apps.organizations.models import Organization
from apps.timetracking.models import TimeEntry

SECONDS_PER_HOUR = Decimal(3600)
HUNDRED = Decimal(100)
ZERO = Decimal("0.00")
DURATION = ExpressionWrapper(F("ended_at") - F("started_at"), output_field=DurationField())


def _hours(duration: timedelta | None) -> Decimal:
    if duration is None:
        return ZERO
    return quantize_money(Decimal(duration.total_seconds()) / SECONDS_PER_HOUR)


def _percentage(part: Decimal, whole: Decimal) -> Decimal:
    if not whole:
        return ZERO
    return quantize_money(part / whole * HUNDRED)


@dataclass(frozen=True, slots=True)
class HoursBreakdown:
    tracked_hours: Decimal
    billable_hours: Decimal
    non_billable_hours: Decimal
    billable_ratio: Decimal


@dataclass(frozen=True, slots=True)
class DailyHours:
    day: date
    billable_hours: Decimal
    non_billable_hours: Decimal


@dataclass(frozen=True, slots=True)
class GroupHours:
    id: int
    name: str
    tracked_hours: Decimal
    billable_hours: Decimal


@dataclass(frozen=True, slots=True)
class CurrencyRevenue:
    currency: str
    draft: Decimal
    invoiced: Decimal
    paid: Decimal
    outstanding: Decimal


@dataclass(frozen=True, slots=True)
class RetainerUsage:
    client_id: int
    client_name: str
    currency: str
    included_hours: Decimal
    rollover_hours: Decimal
    used_hours: Decimal
    remaining_hours: Decimal
    overage_hours: Decimal
    utilization: Decimal
    projected_total: Decimal
    invoice_id: int | None
    invoice_status: str | None


def period_entries(
    organization: Organization,
    period: MonthPeriod,
    user: User | None = None,
) -> QuerySet[TimeEntry]:
    start, end = period.bounds(organization.tzinfo)
    entries = (
        TimeEntry.objects.finished().filter(organization=organization).started_between(start, end)
    )
    return entries.filter(user=user) if user is not None else entries


def hours_breakdown(entries: QuerySet[TimeEntry]) -> HoursBreakdown:
    totals = entries.aggregate(
        tracked=Sum(DURATION),
        billable=Sum(DURATION, filter=Q(is_billable=True)),
    )
    tracked = _hours(totals["tracked"])
    billable = _hours(totals["billable"])
    return HoursBreakdown(
        tracked_hours=tracked,
        billable_hours=billable,
        non_billable_hours=tracked - billable,
        billable_ratio=_percentage(billable, tracked),
    )


def daily_hours(
    entries: QuerySet[TimeEntry],
    organization: Organization,
    period: MonthPeriod,
) -> list[DailyHours]:
    rows = (
        entries.annotate(day=TruncDate("started_at", tzinfo=organization.tzinfo))
        .values("day")
        .annotate(
            billable=Sum(DURATION, filter=Q(is_billable=True)),
            non_billable=Sum(DURATION, filter=Q(is_billable=False)),
        )
    )
    totals: dict[date, tuple[timedelta | None, timedelta | None]] = {
        row["day"]: (row["billable"], row["non_billable"]) for row in rows
    }
    days = (
        period.first_day + timedelta(days=offset)
        for offset in range((period.last_day - period.first_day).days + 1)
    )
    daily = []
    for day in days:
        billable, non_billable = totals.get(day, (None, None))
        daily.append(
            DailyHours(
                day=day,
                billable_hours=_hours(billable),
                non_billable_hours=_hours(non_billable),
            ),
        )
    return daily


def hours_by_member(entries: QuerySet[TimeEntry]) -> list[GroupHours]:
    rows = (
        entries.values("user_id", "user__first_name", "user__last_name")
        .annotate(tracked=Sum(DURATION), billable=Sum(DURATION, filter=Q(is_billable=True)))
        .order_by("-tracked")
    )
    return [
        GroupHours(
            id=row["user_id"],
            name=f"{row['user__first_name']} {row['user__last_name']}".strip(),
            tracked_hours=_hours(row["tracked"]),
            billable_hours=_hours(row["billable"]),
        )
        for row in rows
    ]


def hours_by_client(entries: QuerySet[TimeEntry]) -> list[GroupHours]:
    rows = (
        entries.values("project__client_id", "project__client__name")
        .annotate(tracked=Sum(DURATION), billable=Sum(DURATION, filter=Q(is_billable=True)))
        .order_by("-tracked")
    )
    return [
        GroupHours(
            id=row["project__client_id"],
            name=row["project__client__name"],
            tracked_hours=_hours(row["tracked"]),
            billable_hours=_hours(row["billable"]),
        )
        for row in rows
    ]


def hours_by_project(entries: QuerySet[TimeEntry]) -> list[GroupHours]:
    rows = (
        entries.values("project_id", "project__name")
        .annotate(tracked=Sum(DURATION), billable=Sum(DURATION, filter=Q(is_billable=True)))
        .order_by("-tracked")
    )
    return [
        GroupHours(
            id=row["project_id"],
            name=row["project__name"],
            tracked_hours=_hours(row["tracked"]),
            billable_hours=_hours(row["billable"]),
        )
        for row in rows
    ]


def unbilled_hours(organization: Organization) -> Decimal:
    total = (
        TimeEntry.objects.finished()
        .billable()
        .uninvoiced()
        .filter(organization=organization)
        .aggregate(total=Sum(DURATION))["total"]
    )
    return _hours(total)


def revenue_by_currency(organization: Organization, period: MonthPeriod) -> list[CurrencyRevenue]:
    rows = (
        Invoice.objects.active()
        .for_period(period)
        .filter(organization=organization)
        .values("currency")
        .annotate(
            draft=Sum("total", filter=Q(status=InvoiceStatus.DRAFT)),
            invoiced=Sum("total", filter=Q(status__in=(InvoiceStatus.ISSUED, InvoiceStatus.PAID))),
            paid=Sum("total", filter=Q(status=InvoiceStatus.PAID)),
            outstanding=Sum("total", filter=Q(status=InvoiceStatus.ISSUED)),
        )
        .order_by("currency")
    )
    return [
        CurrencyRevenue(
            currency=row["currency"],
            draft=row["draft"] or ZERO,
            invoiced=row["invoiced"] or ZERO,
            paid=row["paid"] or ZERO,
            outstanding=row["outstanding"] or ZERO,
        )
        for row in rows
    ]


def _usage(
    *,
    contract: Contract,
    included_minutes: int,
    rollover_minutes: int,
    used_minutes: int,
    overage_minutes: int,
    projected_total: Decimal,
    invoice: Invoice | None,
) -> RetainerUsage:
    allowance = included_minutes + rollover_minutes
    return RetainerUsage(
        client_id=contract.client_id,
        client_name=contract.client.name,
        currency=contract.client.currency,
        included_hours=minutes_to_hours(included_minutes),
        rollover_hours=minutes_to_hours(rollover_minutes),
        used_hours=minutes_to_hours(used_minutes),
        remaining_hours=minutes_to_hours(max(allowance - used_minutes, 0)),
        overage_hours=minutes_to_hours(overage_minutes),
        utilization=_percentage(Decimal(used_minutes), Decimal(allowance)),
        projected_total=projected_total,
        invoice_id=invoice.pk if invoice else None,
        invoice_status=invoice.status if invoice else None,
    )


def retainer_usage(organization: Organization, period: MonthPeriod) -> list[RetainerUsage]:
    contracts = (
        Contract.objects.filter(organization=organization, billing_model=BillingModel.RETAINER)
        .overlapping(period.first_day, period.last_day)
        .select_related("client", "client__organization")
        .order_by("client__name")
    )
    usages = []
    for contract in contracts:
        invoice = billing_selectors.active_invoice_for_period(contract.client, period)
        if invoice is not None:
            usages.append(
                _usage(
                    contract=contract,
                    included_minutes=invoice.included_minutes,
                    rollover_minutes=invoice.rollover_minutes_available,
                    used_minutes=invoice.billable_minutes,
                    overage_minutes=invoice.overage_minutes,
                    projected_total=invoice.subtotal,
                    invoice=invoice,
                ),
            )
            continue
        result = calculate_invoice(client=contract.client, period=period).result
        usages.append(
            _usage(
                contract=contract,
                included_minutes=result.included_minutes,
                rollover_minutes=result.rollover_minutes_available,
                used_minutes=result.billable_minutes,
                overage_minutes=result.overage_minutes,
                projected_total=result.subtotal,
                invoice=None,
            ),
        )
    return usages
