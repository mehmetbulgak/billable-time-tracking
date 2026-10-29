import calendar
import re
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Self
from zoneinfo import ZoneInfo

_PERIOD_PATTERN = re.compile(r"^(?P<year>\d{4})-(?P<month>\d{2})$")


@dataclass(frozen=True, slots=True, order=True)
class MonthPeriod:
    year: int
    month: int

    def __post_init__(self) -> None:
        if not 1 <= self.month <= 12:
            raise ValueError(f"Month must be between 1 and 12, got {self.month}.")
        if not 1970 <= self.year <= 9999:
            raise ValueError(f"Year {self.year} is out of range.")

    @classmethod
    def parse(cls, value: str) -> Self:
        match = _PERIOD_PATTERN.match(value)
        if match is None:
            raise ValueError(f"Period must use the YYYY-MM format, got {value!r}.")
        return cls(year=int(match["year"]), month=int(match["month"]))

    @classmethod
    def containing(cls, day: date) -> Self:
        return cls(year=day.year, month=day.month)

    @property
    def first_day(self) -> date:
        return date(self.year, self.month, 1)

    @property
    def last_day(self) -> date:
        return date(self.year, self.month, calendar.monthrange(self.year, self.month)[1])

    def previous(self) -> "MonthPeriod":
        if self.month == 1:
            return MonthPeriod(year=self.year - 1, month=12)
        return MonthPeriod(year=self.year, month=self.month - 1)

    def next(self) -> "MonthPeriod":
        if self.month == 12:
            return MonthPeriod(year=self.year + 1, month=1)
        return MonthPeriod(year=self.year, month=self.month + 1)

    def bounds(self, tz: ZoneInfo) -> tuple[datetime, datetime]:
        start = datetime.combine(self.first_day, time.min, tzinfo=tz)
        end = datetime.combine(self.next().first_day, time.min, tzinfo=tz)
        return start, end

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"
