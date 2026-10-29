from django.db.models import QuerySet

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.timetracking.models import TimeEntry


def with_related(queryset: QuerySet[TimeEntry]) -> QuerySet[TimeEntry]:
    return queryset.select_related("user", "project", "project__client")


def running_entry_for(user: User) -> TimeEntry | None:
    return with_related(TimeEntry.objects.running().filter(user=user)).first()


def active_timers(organization: Organization) -> QuerySet[TimeEntry]:
    return with_related(
        TimeEntry.objects.running().filter(organization=organization),
    ).order_by("started_at")
