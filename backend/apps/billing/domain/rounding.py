from collections.abc import Iterable

SECONDS_PER_MINUTE = 60


def ceil_division(numerator: int, denominator: int) -> int:
    return -(-numerator // denominator)


def tracked_minutes(duration_seconds: int) -> int:
    return ceil_division(max(duration_seconds, 0), SECONDS_PER_MINUTE)


def rounded_minutes(duration_seconds: int, increment_minutes: int) -> int:
    if duration_seconds <= 0:
        return 0
    increment_seconds = increment_minutes * SECONDS_PER_MINUTE
    return ceil_division(duration_seconds, increment_seconds) * increment_minutes


def total_rounded_minutes(durations_seconds: Iterable[int], increment_minutes: int) -> int:
    return sum(rounded_minutes(seconds, increment_minutes) for seconds in durations_seconds)


def total_tracked_minutes(durations_seconds: Iterable[int]) -> int:
    return sum(tracked_minutes(seconds) for seconds in durations_seconds)
