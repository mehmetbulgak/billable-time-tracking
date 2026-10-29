from decimal import Decimal

import pytest

from apps.billing.domain.strategies import (
    FixedFeeBilling,
    HourlyBilling,
    RetainerBilling,
    strategy_for,
)
from apps.billing.domain.types import BillingModel, ContractTerms, InvalidTermsError, LineKind

HOUR = 3600


def retainer_terms(
    *,
    included_hours: Decimal = Decimal("20.00"),
    rollover_cap_hours: Decimal = Decimal("5.00"),
) -> ContractTerms:
    return ContractTerms(
        billing_model=BillingModel.RETAINER,
        rounding_increment_minutes=15,
        monthly_fee=Decimal("2000.00"),
        included_hours=included_hours,
        overage_rate=Decimal("150.00"),
        rollover_cap_hours=rollover_cap_hours,
    )


class TestContractTerms:
    def test_hourly_terms_require_a_rate(self) -> None:
        with pytest.raises(InvalidTermsError, match="hourly_rate"):
            ContractTerms(billing_model=BillingModel.HOURLY)

    def test_retainer_terms_require_all_retainer_fields(self) -> None:
        with pytest.raises(InvalidTermsError, match="overage_rate"):
            ContractTerms(
                billing_model=BillingModel.RETAINER,
                monthly_fee=Decimal("100"),
                included_hours=Decimal("10"),
            )

    def test_negative_amounts_are_rejected(self) -> None:
        with pytest.raises(InvalidTermsError, match="negative"):
            ContractTerms(billing_model=BillingModel.HOURLY, hourly_rate=Decimal("-1"))

    def test_rounding_increment_must_be_positive(self) -> None:
        with pytest.raises(InvalidTermsError, match="rounding"):
            ContractTerms(
                billing_model=BillingModel.HOURLY,
                hourly_rate=Decimal("10"),
                rounding_increment_minutes=0,
            )


class TestHourlyBilling:
    def test_bills_rounded_time_at_the_hourly_rate(self) -> None:
        terms = ContractTerms(
            billing_model=BillingModel.HOURLY,
            hourly_rate=Decimal("100.00"),
            rounding_increment_minutes=15,
        )

        result = HourlyBilling(terms).calculate([50 * 60, 10 * 60])

        assert result.billable_minutes == 75
        assert result.tracked_minutes == 60
        assert len(result.lines) == 1
        line = result.lines[0]
        assert line.kind is LineKind.HOURLY_TIME
        assert line.quantity == Decimal("1.25")
        assert line.amount == Decimal("125.00")
        assert result.subtotal == Decimal("125.00")

    def test_amount_is_computed_from_minutes_to_avoid_rounding_drift(self) -> None:
        terms = ContractTerms(billing_model=BillingModel.HOURLY, hourly_rate=Decimal("100.00"))

        result = HourlyBilling(terms).calculate([7 * 60])

        assert result.lines[0].quantity == Decimal("0.12")
        assert result.lines[0].amount == Decimal("11.67")

    def test_no_time_produces_an_empty_result(self) -> None:
        terms = ContractTerms(billing_model=BillingModel.HOURLY, hourly_rate=Decimal("100.00"))

        result = HourlyBilling(terms).calculate([])

        assert result.is_empty
        assert result.subtotal == Decimal("0.00")


class TestRetainerBilling:
    def test_time_within_the_allowance_is_covered_by_the_fee(self) -> None:
        result = RetainerBilling(retainer_terms()).calculate([10 * HOUR])

        assert [line.kind for line in result.lines] == [
            LineKind.RETAINER_FEE,
            LineKind.INCLUDED_HOURS,
        ]
        assert result.subtotal == Decimal("2000.00")
        assert result.overage_minutes == 0
        assert result.included_minutes_unused == 10 * 60
        assert result.next_rollover_minutes == 5 * 60

    def test_time_beyond_the_allowance_is_billed_as_overage(self) -> None:
        result = RetainerBilling(retainer_terms()).calculate([25 * HOUR])

        overage = result.lines[-1]
        assert overage.kind is LineKind.OVERAGE
        assert overage.quantity == Decimal("5.00")
        assert overage.amount == Decimal("750.00")
        assert result.subtotal == Decimal("2750.00")
        assert result.included_minutes_unused == 0
        assert result.next_rollover_minutes == 0

    def test_rolled_over_hours_are_consumed_before_the_monthly_allowance(self) -> None:
        result = RetainerBilling(retainer_terms()).calculate([22 * HOUR], rollover_minutes=4 * 60)

        assert result.rollover_minutes_available == 4 * 60
        assert result.rollover_minutes_applied == 4 * 60
        assert result.overage_minutes == 0
        assert result.included_minutes_unused == 2 * 60
        assert result.next_rollover_minutes == 2 * 60
        assert "4.00 h rolled over" in result.lines[1].description

    def test_rollover_never_exceeds_the_cap(self) -> None:
        result = RetainerBilling(retainer_terms()).calculate([], rollover_minutes=10 * 60)

        assert result.rollover_minutes_available == 5 * 60
        assert result.rollover_minutes_applied == 0

    def test_unused_rollover_expires_and_only_the_monthly_allowance_rolls(self) -> None:
        terms = retainer_terms(rollover_cap_hours=Decimal("40.00"))

        result = RetainerBilling(terms).calculate([HOUR], rollover_minutes=5 * 60)

        assert result.rollover_minutes_applied == 60
        assert result.next_rollover_minutes == 20 * 60

    def test_overage_respects_the_rounding_increment(self) -> None:
        terms = retainer_terms(included_hours=Decimal("1.00"))

        result = RetainerBilling(terms).calculate([HOUR, 61])

        assert result.overage_minutes == 15
        assert result.lines[-1].amount == Decimal("37.50")


class TestFixedFeeBilling:
    def test_fee_is_billed_regardless_of_hours(self) -> None:
        terms = ContractTerms(
            billing_model=BillingModel.FIXED_FEE,
            monthly_fee=Decimal("5000.00"),
            rounding_increment_minutes=15,
        )

        result = FixedFeeBilling(terms).calculate([100 * HOUR, 61])

        assert result.subtotal == Decimal("5000.00")
        assert result.billable_minutes == 100 * 60 + 15
        assert [line.kind for line in result.lines] == [LineKind.FIXED_FEE]


@pytest.mark.parametrize(
    ("terms", "expected"),
    [
        (ContractTerms(billing_model=BillingModel.HOURLY, hourly_rate=Decimal("1")), HourlyBilling),
        (retainer_terms(), RetainerBilling),
        (
            ContractTerms(billing_model=BillingModel.FIXED_FEE, monthly_fee=Decimal("1")),
            FixedFeeBilling,
        ),
    ],
)
def test_strategy_for_selects_the_matching_strategy(terms: ContractTerms, expected: type) -> None:
    assert isinstance(strategy_for(terms), expected)
