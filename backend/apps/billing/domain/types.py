from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum

from apps.core.money import quantize_money


class BillingModel(StrEnum):
    HOURLY = "hourly"
    RETAINER = "retainer"
    FIXED_FEE = "fixed_fee"

    @property
    def label(self) -> str:
        return self.value.replace("_", " ").capitalize()


class LineKind(StrEnum):
    HOURLY_TIME = "hourly_time"
    RETAINER_FEE = "retainer_fee"
    INCLUDED_HOURS = "included_hours"
    OVERAGE = "overage"
    FIXED_FEE = "fixed_fee"

    @property
    def label(self) -> str:
        return self.value.replace("_", " ").capitalize()


class InvalidTermsError(ValueError):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class ContractTerms:
    billing_model: BillingModel
    rounding_increment_minutes: int = 1
    hourly_rate: Decimal | None = None
    monthly_fee: Decimal | None = None
    included_hours: Decimal | None = None
    overage_rate: Decimal | None = None
    rollover_cap_hours: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if self.rounding_increment_minutes < 1:
            raise InvalidTermsError("The rounding increment must be at least one minute.")
        if self.rollover_cap_hours < 0:
            raise InvalidTermsError("The rollover cap cannot be negative.")
        for name in self._required_fields():
            value = getattr(self, name)
            if value is None:
                raise InvalidTermsError(f"{self.billing_model.label} contracts require {name}.")
            if value < 0:
                raise InvalidTermsError(f"{name} cannot be negative.")

    def _required_fields(self) -> tuple[str, ...]:
        match self.billing_model:
            case BillingModel.HOURLY:
                return ("hourly_rate",)
            case BillingModel.RETAINER:
                return ("monthly_fee", "included_hours", "overage_rate")
            case BillingModel.FIXED_FEE:
                return ("monthly_fee",)


@dataclass(frozen=True, slots=True, kw_only=True)
class LineItem:
    kind: LineKind
    description: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal


@dataclass(frozen=True, slots=True, kw_only=True)
class BillingResult:
    lines: tuple[LineItem, ...]
    tracked_minutes: int
    billable_minutes: int
    included_minutes: int = 0
    included_minutes_unused: int = 0
    rollover_minutes_available: int = 0
    rollover_minutes_applied: int = 0
    overage_minutes: int = 0
    next_rollover_minutes: int = 0
    subtotal: Decimal = field(init=False)

    def __post_init__(self) -> None:
        total = sum((line.amount for line in self.lines), start=Decimal("0"))
        object.__setattr__(self, "subtotal", quantize_money(total))

    @property
    def is_empty(self) -> bool:
        return not self.lines
