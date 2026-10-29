from functools import cache
from zoneinfo import available_timezones

from django.core.exceptions import ValidationError


@cache
def _known_timezones() -> frozenset[str]:
    return frozenset(available_timezones())


def validate_timezone(value: str) -> None:
    if value not in _known_timezones():
        raise ValidationError(f"{value!r} is not a valid IANA time zone.", code="invalid_timezone")
