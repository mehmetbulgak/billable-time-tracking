from dataclasses import dataclass

from apps.billing import selectors
from apps.billing.domain.strategies import strategy_for
from apps.billing.domain.types import BillingModel, BillingResult
from apps.billing.models import Contract, Invoice
from apps.clients.models import Client
from apps.core.exceptions import DomainError
from apps.core.periods import MonthPeriod


@dataclass(frozen=True, slots=True)
class InvoiceCalculation:
    contract: Contract
    result: BillingResult
    entry_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class InvoicePreview:
    result: BillingResult
    replaces_draft_id: int | None


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


def calculate_invoice(
    *, client: Client, period: MonthPeriod, for_update: bool = False
) -> InvoiceCalculation:
    contract = selectors.contract_for_period(client, period)
    if contract is None:
        raise DomainError(
            f"{client.name} has no contract covering {period}.",
            code="no_active_contract",
        )
    queryset = selectors.invoiceable_entries(client, period).only("id", "started_at", "ended_at")
    if for_update:
        queryset = queryset.select_for_update(of=("self",))
    entries = list(queryset)
    result = strategy_for(contract.to_terms()).calculate(
        [entry.duration_seconds for entry in entries],
        rollover_minutes=_rollover_minutes_for(contract, period),
    )
    return InvoiceCalculation(
        contract=contract,
        result=result,
        entry_ids=tuple(entry.pk for entry in entries),
    )
