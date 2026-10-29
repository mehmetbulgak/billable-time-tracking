from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
MINUTES_PER_HOUR = 60


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def minutes_to_hours(minutes: int) -> Decimal:
    return quantize_money(Decimal(minutes) / MINUTES_PER_HOUR)


def hours_to_minutes(hours: Decimal) -> int:
    return int((hours * MINUTES_PER_HOUR).to_integral_value(rounding=ROUND_HALF_UP))


def amount_for_minutes(minutes: int, hourly_rate: Decimal) -> Decimal:
    return quantize_money(Decimal(minutes) * hourly_rate / MINUTES_PER_HOUR)
