from datetime import datetime, timedelta
from typing import Self

from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeBoundary, RangeOperators
from django.db import models
from django.db.models import F, Func, Q

from apps.core.models import OrganizationOwnedModel


class TsTzRange(Func):
    function = "TSTZRANGE"
    output_field = DateTimeRangeField()


class TimeEntryQuerySet(models.QuerySet["TimeEntry"]):
    def running(self) -> Self:
        return self.filter(ended_at__isnull=True)

    def finished(self) -> Self:
        return self.filter(ended_at__isnull=False)

    def billable(self) -> Self:
        return self.filter(is_billable=True)

    def uninvoiced(self) -> Self:
        return self.filter(invoice__isnull=True)

    def started_between(self, start: datetime, end: datetime) -> Self:
        return self.filter(started_at__gte=start, started_at__lt=end)


class TimeEntry(OrganizationOwnedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="time_entries",
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.PROTECT,
        related_name="time_entries",
    )
    description = models.CharField(max_length=500, blank=True)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    is_billable = models.BooleanField(default=True)
    invoice = models.ForeignKey(
        "billing.Invoice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="time_entries",
    )

    objects = TimeEntryQuerySet.as_manager()

    class Meta:
        ordering = ("-started_at",)
        verbose_name_plural = "time entries"
        indexes = (
            models.Index(fields=("organization", "started_at"), name="time_entries_org_started"),
            models.Index(fields=("user", "started_at"), name="time_entries_user_started"),
            models.Index(fields=("project", "started_at"), name="time_entries_proj_started"),
        )
        constraints = (
            models.CheckConstraint(
                condition=Q(ended_at__isnull=True) | Q(ended_at__gt=F("started_at")),
                name="time_entries_end_after_start",
            ),
            models.UniqueConstraint(
                fields=("user",),
                condition=Q(ended_at__isnull=True),
                name="time_entries_one_running_timer_per_user",
            ),
            ExclusionConstraint(
                name="time_entries_no_overlap_per_user",
                expressions=(
                    (TsTzRange("started_at", "ended_at", RangeBoundary()), RangeOperators.OVERLAPS),
                    ("user", RangeOperators.EQUAL),
                ),
            ),
        )

    def __str__(self) -> str:
        return f"{self.user} · {self.project} · {self.started_at:%Y-%m-%d %H:%M}"

    @property
    def is_running(self) -> bool:
        return self.ended_at is None

    @property
    def is_locked(self) -> bool:
        return self.invoice_id is not None

    def duration_at(self, moment: datetime) -> timedelta:
        end = self.ended_at or moment
        return max(end - self.started_at, timedelta(0))

    @property
    def duration_seconds(self) -> int:
        if self.ended_at is None:
            return 0
        return int((self.ended_at - self.started_at).total_seconds())
