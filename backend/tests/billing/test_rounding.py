import pytest

from apps.billing.domain.rounding import (
    rounded_minutes,
    total_rounded_minutes,
    total_tracked_minutes,
    tracked_minutes,
)


@pytest.mark.parametrize(
    ("seconds", "increment", "expected"),
    [
        (0, 15, 0),
        (-30, 15, 0),
        (1, 15, 15),
        (900, 15, 15),
        (901, 15, 30),
        (59, 1, 1),
        (60, 1, 1),
        (61, 1, 2),
        (360, 6, 6),
        (361, 6, 12),
        (3600, 60, 60),
        (3601, 60, 120),
    ],
)
def test_rounded_minutes_rounds_up_to_the_increment(
    seconds: int, increment: int, expected: int
) -> None:
    assert rounded_minutes(seconds, increment) == expected


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [(0, 0), (1, 1), (60, 1), (61, 2), (5400, 90)],
)
def test_tracked_minutes_rounds_partial_minutes_up(seconds: int, expected: int) -> None:
    assert tracked_minutes(seconds) == expected


def test_totals_round_each_entry_individually() -> None:
    durations = [50 * 60, 10 * 60, 1]

    assert total_rounded_minutes(durations, 15) == 60 + 15 + 15
    assert total_tracked_minutes(durations) == 50 + 10 + 1
