from collections.abc import Sequence
from decimal import Decimal
from typing import Protocol

from apps.billing.domain.rounding import total_rounded_minutes, total_tracked_minutes
from apps.billing.domain.types import (
    BillingModel,
    BillingResult,
    ContractTerms,
    InvalidTermsError,
    LineItem,
    LineKind,
)
from apps.core.money import amount_for_minutes, hours_to_minutes, minutes_to_hours

ONE = Decimal("1")
ZERO = Decimal("0")


def _required(value: Decimal | None, name: str) -> Decimal:
    if value is None:
        raise InvalidTermsError(f"Missing contract term: {name}.")
    return value


class BillingStrategy(Protocol):
    def calculate(
        self,
        durations_seconds: Sequence[int],
        *,
        rollover_minutes: int = 0,
    ) -> BillingResult: ...


class HourlyBilling:
    def __init__(self, terms: ContractTerms) -> None:
        self._increment = terms.rounding_increment_minutes
        self._rate = _required(terms.hourly_rate, "hourly_rate")

    def calculate(
        self,
        durations_seconds: Sequence[int],
        *,
        rollover_minutes: int = 0,
    ) -> BillingResult:
        billable = total_rounded_minutes(durations_seconds, self._increment)
        lines: tuple[LineItem, ...] = ()
        if billable:
            lines = (
                LineItem(
                    kind=LineKind.HOURLY_TIME,
                    description="Billable time",
                    quantity=minutes_to_hours(billable),
                    unit_price=self._rate,
                    amount=amount_for_minutes(billable, self._rate),
                ),
            )
        return BillingResult(
            lines=lines,
            tracked_minutes=total_tracked_minutes(durations_seconds),
            billable_minutes=billable,
        )


class RetainerBilling:
    def __init__(self, terms: ContractTerms) -> None:
        self._increment = terms.rounding_increment_minutes
        self._fee = _required(terms.monthly_fee, "monthly_fee")
        self._included_minutes = hours_to_minutes(_required(terms.included_hours, "included_hours"))
        self._overage_rate = _required(terms.overage_rate, "overage_rate")
        self._rollover_cap_minutes = hours_to_minutes(terms.rollover_cap_hours)

    def calculate(
        self,
        durations_seconds: Sequence[int],
        *,
        rollover_minutes: int = 0,
    ) -> BillingResult:
        billable = total_rounded_minutes(durations_seconds, self._increment)
        rollover_available = max(0, min(rollover_minutes, self._rollover_cap_minutes))

        from_rollover = min(billable, rollover_available)
        from_included = min(billable - from_rollover, self._included_minutes)
        overage = billable - from_rollover - from_included
        included_unused = self._included_minutes - from_included

        lines = [
            LineItem(
                kind=LineKind.RETAINER_FEE,
                description="Monthly retainer",
                quantity=ONE,
                unit_price=self._fee,
                amount=self._fee,
            ),
            LineItem(
                kind=LineKind.INCLUDED_HOURS,
                description=self._included_description(
                    used_minutes=from_rollover + from_included,
                    rollover_available=rollover_available,
                ),
                quantity=minutes_to_hours(from_rollover + from_included),
                unit_price=ZERO,
                amount=ZERO,
            ),
        ]
        if overage:
            lines.append(
                LineItem(
                    kind=LineKind.OVERAGE,
                    description="Hours beyond the retainer",
                    quantity=minutes_to_hours(overage),
                    unit_price=self._overage_rate,
                    amount=amount_for_minutes(overage, self._overage_rate),
                ),
            )

        return BillingResult(
            lines=tuple(lines),
            tracked_minutes=total_tracked_minutes(durations_seconds),
            billable_minutes=billable,
            included_minutes=self._included_minutes,
            included_minutes_unused=included_unused,
            rollover_minutes_available=rollover_available,
            rollover_minutes_applied=from_rollover,
            overage_minutes=overage,
            next_rollover_minutes=min(included_unused, self._rollover_cap_minutes),
        )

    def _included_description(self, *, used_minutes: int, rollover_available: int) -> str:
        allowance = minutes_to_hours(self._included_minutes + rollover_available)
        description = f"Included hours used ({minutes_to_hours(used_minutes)} of {allowance} h"
        if rollover_available:
            description += f", incl. {minutes_to_hours(rollover_available)} h rolled over"
        return f"{description})"


class FixedFeeBilling:
    def __init__(self, terms: ContractTerms) -> None:
        self._increment = terms.rounding_increment_minutes
        self._fee = _required(terms.monthly_fee, "monthly_fee")

    def calculate(
        self,
        durations_seconds: Sequence[int],
        *,
        rollover_minutes: int = 0,
    ) -> BillingResult:
        return BillingResult(
            lines=(
                LineItem(
                    kind=LineKind.FIXED_FEE,
                    description="Fixed monthly fee",
                    quantity=ONE,
                    unit_price=self._fee,
                    amount=self._fee,
                ),
            ),
            tracked_minutes=total_tracked_minutes(durations_seconds),
            billable_minutes=total_rounded_minutes(durations_seconds, self._increment),
        )


_STRATEGIES: dict[BillingModel, type[HourlyBilling | RetainerBilling | FixedFeeBilling]] = {
    BillingModel.HOURLY: HourlyBilling,
    BillingModel.RETAINER: RetainerBilling,
    BillingModel.FIXED_FEE: FixedFeeBilling,
}


def strategy_for(terms: ContractTerms) -> BillingStrategy:
    return _STRATEGIES[terms.billing_model](terms)
