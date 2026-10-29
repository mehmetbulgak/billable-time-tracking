from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest

from apps.core.periods import MonthPeriod


def test_parse_reads_year_and_month() -> None:
    assert MonthPeriod.parse("2026-02") == MonthPeriod(2026, 2)


@pytest.mark.parametrize("value", ["2026-13", "2026-2", "26-02", "february", "2026-00"])
def test_parse_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError, match=r"."):
        MonthPeriod.parse(value)


def test_navigation_wraps_across_years() -> None:
    assert MonthPeriod(2026, 1).previous() == MonthPeriod(2025, 12)
    assert MonthPeriod(2025, 12).next() == MonthPeriod(2026, 1)


def test_first_and_last_day_handle_leap_years() -> None:
    period = MonthPeriod(2028, 2)

    assert period.first_day == date(2028, 2, 1)
    assert period.last_day == date(2028, 2, 29)


def test_bounds_are_expressed_in_the_given_time_zone() -> None:
    start, end = MonthPeriod(2026, 10).bounds(ZoneInfo("Europe/Istanbul"))

    assert start.astimezone(UTC) == datetime(2026, 9, 30, 21, 0, tzinfo=UTC)
    assert end.astimezone(UTC) == datetime(2026, 10, 31, 21, 0, tzinfo=UTC)


def test_periods_are_ordered_chronologically() -> None:
    assert MonthPeriod(2025, 12) < MonthPeriod(2026, 1) < MonthPeriod(2026, 2)
    assert str(MonthPeriod(2026, 3)) == "2026-03"
