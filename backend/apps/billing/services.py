from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from apps.billing import selectors
from apps.billing.domain.strategies import strategy_for
from apps.billing.domain.types import BillingModel, BillingResult, InvalidTermsError
from apps.billing.models import Contract, Invoice, InvoiceLine, InvoiceStatus
from apps.billing.signals import invoice_issued
from apps.clients.models import Client
from apps.core.db import violated_constraint
from apps.core.exceptions import ConflictError, DomainError
from apps.core.money import quantize_money
from apps.core.periods import MonthPeriod
from apps.organizations.models import Organization
from apps.realtime.events import ActivityEvent
from apps.realtime.publisher import publish_on_commit
from apps.timetracking.models import TimeEntry

HUNDRED = Decimal("100")
CONTRACT_OVERLAP_CONSTRAINT = "contracts_no_overlap_per_client"
IMMUTABLE_CONTRACT_FIELDS = frozenset(
    {
        "client",
        "billing_model",
        "starts_on",
        "hourly_rate",
        "monthly_fee",
        "included_hours",
        "overage_rate",
        "rollover_cap_hours",
        "rounding_increment_minutes",
    },
)


@dataclass(frozen=True, slots=True)
class InvoiceCalculation:
    contract: Contract
    result: BillingResult
    entry_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class InvoicePreview:
    result: BillingResult
    replaces_draft_id: int | None


@dataclass(slots=True)
class DraftGenerationSummary:
    created: list[int] = field(default_factory=list)
    skipped: list[tuple[int, str]] = field(default_factory=list)


def _save_contract(contract: Contract) -> Contract:
    try:
        contract.to_terms()
    except InvalidTermsError as error:
        raise DomainError(str(error), code="invalid_terms") from error
    contract.full_clean(validate_constraints=False)
    try:
        with transaction.atomic():
            contract.save()
    except IntegrityError as error:
        if violated_constraint(error) != CONTRACT_OVERLAP_CONSTRAINT:
            raise
        raise ConflictError(
            "This contract overlaps another contract of the same client.",
            code="overlapping_contract",
        ) from error
    return contract


def create_contract(*, organization: Organization, **fields: Any) -> Contract:
    client: Client = fields["client"]
    if client.organization_id != organization.pk:
        raise DomainError("Unknown client.", code="unknown_client")
    return _save_contract(Contract(organization=organization, **fields))


def update_contract(*, contract: Contract, **fields: Any) -> Contract:
    has_issued_invoices = contract.invoices.exclude(status=InvoiceStatus.DRAFT).exists()
    changed = {name for name, value in fields.items() if getattr(contract, name) != value}
    if has_issued_invoices and changed & IMMUTABLE_CONTRACT_FIELDS:
        raise ConflictError(
            "Contracts with issued invoices can only change their end date.",
            code="contract_locked",
        )
    for name, value in fields.items():
        setattr(contract, name, value)
    return _save_contract(contract)


def _rollover_minutes_for(contract: Contract, period: MonthPeriod) -> int:
    if contract.billing_model != BillingModel.RETAINER:
        return 0
    previous = (
        Invoice.objects.active()
        .for_period(period.previous())
        .filter(contract=contract)
        .only("next_rollover_minutes")
        .first()
    )
    return previous.next_rollover_minutes if previous else 0


def calculate_invoice(*, client: Client, period: MonthPeriod) -> InvoiceCalculation:
    contract = selectors.contract_for_period(client, period)
    if contract is None:
        raise DomainError(
            f"{client.name} has no contract covering {period}.",
            code="no_active_contract",
        )
    entries = list(
        selectors.invoiceable_entries(client, period).only("id", "started_at", "ended_at"),
    )
    result = strategy_for(contract.to_terms()).calculate(
        [entry.duration_seconds for entry in entries],
        rollover_minutes=_rollover_minutes_for(contract, period),
    )
    return InvoiceCalculation(
        contract=contract,
        result=result,
        entry_ids=tuple(entry.pk for entry in entries),
    )


def _replaceable_draft(client: Client, period: MonthPeriod) -> Invoice | None:
    existing = selectors.active_invoice_for_period(client, period)
    if existing is not None and not existing.is_draft:
        raise ConflictError(
            f"An invoice for {client.name} in {period} has already been issued.",
            code="invoice_already_issued",
        )
    return existing


def preview_invoice(*, client: Client, period: MonthPeriod) -> InvoicePreview:
    draft = _replaceable_draft(client, period)
    return InvoicePreview(
        result=calculate_invoice(client=client, period=period).result,
        replaces_draft_id=draft.pk if draft else None,
    )


def _publish(invoice: Invoice) -> None:
    publish_on_commit(
        invoice.organization_id,
        ActivityEvent.INVOICE_CHANGED,
        lambda: {"invoice_id": invoice.pk, "status": invoice.status},
    )


def _release_entries(invoice: Invoice) -> None:
    TimeEntry.objects.filter(invoice=invoice).update(invoice=None)


def _lock_period_entries(*, client: Client, period: MonthPeriod) -> None:
    list(
        selectors.invoiceable_entries(client, period)
        .select_for_update(of=("self",))
        .values_list("pk", flat=True),
    )


def _build_invoice(
    *, client: Client, period: MonthPeriod, calculation: InvoiceCalculation
) -> Invoice:
    result = calculation.result
    tax_amount = quantize_money(result.subtotal * client.tax_rate / HUNDRED)
    invoice = Invoice.objects.create(
        organization_id=client.organization_id,
        client=client,
        contract=calculation.contract,
        period_start=period.first_day,
        period_end=period.last_day,
        currency=client.currency,
        subtotal=result.subtotal,
        tax_rate=client.tax_rate,
        tax_amount=tax_amount,
        total=result.subtotal + tax_amount,
        tracked_minutes=result.tracked_minutes,
        billable_minutes=result.billable_minutes,
        included_minutes=result.included_minutes,
        included_minutes_unused=result.included_minutes_unused,
        rollover_minutes_available=result.rollover_minutes_available,
        rollover_minutes_applied=result.rollover_minutes_applied,
        overage_minutes=result.overage_minutes,
        next_rollover_minutes=result.next_rollover_minutes,
    )
    InvoiceLine.objects.bulk_create(
        InvoiceLine(
            invoice=invoice,
            position=position,
            kind=line.kind,
            description=line.description,
            quantity=line.quantity,
            unit_price=line.unit_price,
            amount=line.amount,
        )
        for position, line in enumerate(result.lines, start=1)
    )
    return invoice


@transaction.atomic
def generate_invoice(
    *,
    client: Client,
    period: MonthPeriod,
    replace_draft: bool = True,
) -> Invoice:
    client = Client.objects.select_for_update().select_related("organization").get(pk=client.pk)
    existing = _replaceable_draft(client, period)
    if existing is not None:
        if not replace_draft:
            return existing
        _release_entries(existing)
        existing.delete()

    _lock_period_entries(client=client, period=period)
    calculation = calculate_invoice(client=client, period=period)
    if calculation.result.is_empty:
        raise DomainError(
            f"There is no billable work for {client.name} in {period}.",
            code="nothing_to_invoice",
        )

    invoice = _build_invoice(client=client, period=period, calculation=calculation)
    TimeEntry.objects.filter(pk__in=calculation.entry_ids).update(invoice=invoice)
    _publish(invoice)
    return invoice


def generate_drafts_for_period(
    *,
    organization: Organization,
    period: MonthPeriod,
) -> DraftGenerationSummary:
    summary = DraftGenerationSummary()
    clients = (
        Client.objects.active()
        .filter(
            organization=organization,
            contracts__in=Contract.objects.overlapping(period.first_day, period.last_day),
        )
        .distinct()
    )
    for client in clients:
        if selectors.active_invoice_for_period(client, period) is not None:
            summary.skipped.append((client.pk, "invoice_exists"))
            continue
        try:
            invoice = generate_invoice(client=client, period=period, replace_draft=False)
        except DomainError as error:
            summary.skipped.append((client.pk, error.code))
            continue
        summary.created.append(invoice.pk)
    return summary


def _lock(invoice: Invoice) -> Invoice:
    return (
        Invoice.objects.select_for_update()
        .select_related("client", "organization")
        .get(
            pk=invoice.pk,
        )
    )


def _ensure_status(invoice: Invoice, *allowed: str, action: str) -> None:
    if invoice.status not in allowed:
        raise ConflictError(
            f"A {invoice.status} invoice cannot be {action}.",
            code="invalid_invoice_status",
        )


@transaction.atomic
def discard_draft(*, invoice: Invoice) -> None:
    invoice = _lock(invoice)
    _ensure_status(invoice, InvoiceStatus.DRAFT, action="discarded")
    _release_entries(invoice)
    organization_id, invoice_id = invoice.organization_id, invoice.pk
    invoice.delete()
    publish_on_commit(
        organization_id,
        ActivityEvent.INVOICE_CHANGED,
        lambda: {"invoice_id": invoice_id, "status": "deleted"},
    )


def _next_invoice_number(organization: Organization, issue_date: date) -> str:
    organization = Organization.objects.select_for_update().get(pk=organization.pk)
    sequence = organization.next_invoice_number
    Organization.objects.filter(pk=organization.pk).update(
        next_invoice_number=F("next_invoice_number") + 1,
    )
    return f"{organization.invoice_prefix}-{issue_date.year}-{sequence:04d}"


@transaction.atomic
def issue_invoice(
    *,
    invoice: Invoice,
    issue_date: date | None = None,
    now: datetime | None = None,
) -> Invoice:
    invoice = _lock(invoice)
    _ensure_status(invoice, InvoiceStatus.DRAFT, action="issued")
    now = now or timezone.now()
    issue_date = issue_date or timezone.localdate(now, timezone=invoice.organization.tzinfo)

    invoice.number = _next_invoice_number(invoice.organization, issue_date)
    invoice.status = InvoiceStatus.ISSUED
    invoice.issue_date = issue_date
    invoice.due_date = issue_date + timedelta(days=invoice.client.effective_payment_terms_days)
    invoice.issued_at = now
    invoice.save()

    invoice_issued.send(sender=Invoice, invoice=invoice)
    _publish(invoice)
    return invoice


@transaction.atomic
def mark_invoice_paid(*, invoice: Invoice, paid_at: datetime | None = None) -> Invoice:
    invoice = _lock(invoice)
    _ensure_status(invoice, InvoiceStatus.ISSUED, action="marked as paid")
    invoice.status = InvoiceStatus.PAID
    invoice.paid_at = paid_at or timezone.now()
    invoice.save(update_fields=("status", "paid_at", "updated_at"))
    _publish(invoice)
    return invoice


@transaction.atomic
def void_invoice(*, invoice: Invoice, now: datetime | None = None) -> Invoice:
    invoice = _lock(invoice)
    _ensure_status(invoice, InvoiceStatus.ISSUED, action="voided")
    _release_entries(invoice)
    invoice.status = InvoiceStatus.VOID
    invoice.voided_at = now or timezone.now()
    invoice.save(update_fields=("status", "voided_at", "updated_at"))
    _publish(invoice)
    return invoice
