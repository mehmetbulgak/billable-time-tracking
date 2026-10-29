from datetime import datetime, timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.core.db import violated_constraint
from apps.core.exceptions import ConflictError, DomainError, ForbiddenError, NotFoundError
from apps.projects.models import Project
from apps.realtime.events import ActivityEvent
from apps.realtime.publisher import publish_on_commit
from apps.timetracking.models import TimeEntry
from apps.timetracking.serializers import TimeEntrySerializer

_CONSTRAINT_VIOLATIONS: dict[str, tuple[str, str]] = {
    "time_entries_no_overlap_per_user": (
        "This time entry overlaps another one of your entries.",
        "overlapping_entry",
    ),
    "time_entries_one_running_timer_per_user": (
        "You already have a running timer.",
        "timer_already_running",
    ),
    "time_entries_end_after_start": (
        "The end time must be after the start time.",
        "invalid_range",
    ),
}


def _persist(entry: TimeEntry) -> TimeEntry:
    try:
        with transaction.atomic():
            entry.save()
    except IntegrityError as error:
        violation = _CONSTRAINT_VIOLATIONS.get(violated_constraint(error) or "")
        if violation is None:
            raise
        message, code = violation
        raise ConflictError(message, code=code) from error
    return entry


def _publish(entry: TimeEntry, event: ActivityEvent) -> None:
    publish_on_commit(
        entry.organization_id,
        event,
        lambda: {"entry": TimeEntrySerializer(entry).data},
    )


def _ensure_trackable(*, user: User, project: Project) -> None:
    if project.organization_id != user.organization_id:
        raise NotFoundError("Project not found.")
    if project.is_archived or project.client.is_archived:
        raise DomainError("Time cannot be tracked on archived projects.", code="project_archived")


def _ensure_editable(*, entry: TimeEntry, actor: User) -> None:
    if entry.organization_id != actor.organization_id:
        raise NotFoundError("Time entry not found.")
    if entry.user_id != actor.pk and not actor.is_manager:
        raise ForbiddenError("You can only change your own time entries.", code="not_entry_owner")
    if entry.is_locked:
        raise ConflictError(
            "This entry is on an invoice and can no longer be changed.",
            code="entry_locked",
        )


def _ensure_valid_range(*, started_at: datetime, ended_at: datetime | None, now: datetime) -> None:
    if started_at > now:
        raise DomainError("Time entries cannot start in the future.", code="future_entry")
    if ended_at is None:
        return
    if ended_at <= started_at:
        raise DomainError("The end time must be after the start time.", code="invalid_range")
    if ended_at > now:
        raise DomainError("Time entries cannot end in the future.", code="future_entry")


def _resolve_billable(project: Project, is_billable: bool | None) -> bool:
    return project.is_billable if is_billable is None else is_billable


def _lock_entry(entry: TimeEntry) -> TimeEntry:
    locked = (
        TimeEntry.objects.select_for_update(of=("self",))
        .select_related("project", "project__client", "user")
        .filter(pk=entry.pk)
        .first()
    )
    if locked is None:
        raise NotFoundError("Time entry not found.")
    return locked


@transaction.atomic
def start_timer(
    *,
    user: User,
    project: Project,
    description: str = "",
    is_billable: bool | None = None,
    now: datetime | None = None,
) -> TimeEntry:
    now = now or timezone.now()
    _ensure_trackable(user=user, project=project)

    running = (
        TimeEntry.objects.select_for_update(of=("self",))
        .select_related("project", "project__client", "user")
        .running()
        .filter(user=user)
        .first()
    )
    if running is not None:
        running.ended_at = max(now, running.started_at + timedelta(seconds=1))
        _persist(running)
        _publish(running, ActivityEvent.TIMER_STOPPED)
        now = running.ended_at

    entry = TimeEntry(
        organization_id=project.organization_id,
        user=user,
        project=project,
        description=description,
        started_at=now,
        is_billable=_resolve_billable(project, is_billable),
    )
    _persist(entry)
    _publish(entry, ActivityEvent.TIMER_STARTED)
    return entry


@transaction.atomic
def stop_timer(*, user: User, now: datetime | None = None) -> TimeEntry:
    now = now or timezone.now()
    entry = (
        TimeEntry.objects.select_for_update(of=("self",))
        .select_related("project", "project__client", "user")
        .running()
        .filter(user=user)
        .first()
    )
    if entry is None:
        raise NotFoundError("There is no running timer to stop.", code="no_running_timer")
    entry.ended_at = max(now, entry.started_at + timedelta(seconds=1))
    _persist(entry)
    _publish(entry, ActivityEvent.TIMER_STOPPED)
    return entry


@transaction.atomic
def create_entry(
    *,
    user: User,
    project: Project,
    started_at: datetime,
    ended_at: datetime,
    description: str = "",
    is_billable: bool | None = None,
    now: datetime | None = None,
) -> TimeEntry:
    _ensure_trackable(user=user, project=project)
    _ensure_valid_range(started_at=started_at, ended_at=ended_at, now=now or timezone.now())
    entry = TimeEntry(
        organization_id=project.organization_id,
        user=user,
        project=project,
        description=description,
        started_at=started_at,
        ended_at=ended_at,
        is_billable=_resolve_billable(project, is_billable),
    )
    _persist(entry)
    _publish(entry, ActivityEvent.ENTRY_CHANGED)
    return entry


@transaction.atomic
def update_entry(
    *,
    entry: TimeEntry,
    actor: User,
    project: Project | None = None,
    description: str | None = None,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    is_billable: bool | None = None,
    now: datetime | None = None,
) -> TimeEntry:
    entry = _lock_entry(entry)
    _ensure_editable(entry=entry, actor=actor)
    was_running = entry.is_running

    if project is not None and project.pk != entry.project_id:
        _ensure_trackable(user=entry.user, project=project)
        entry.project = project
    if description is not None:
        entry.description = description
    if started_at is not None:
        entry.started_at = started_at
    if ended_at is not None:
        entry.ended_at = ended_at
    if is_billable is not None:
        entry.is_billable = is_billable

    _ensure_valid_range(
        started_at=entry.started_at,
        ended_at=entry.ended_at,
        now=now or timezone.now(),
    )
    _persist(entry)
    stopped = was_running and not entry.is_running
    _publish(entry, ActivityEvent.TIMER_STOPPED if stopped else ActivityEvent.ENTRY_CHANGED)
    return entry


@transaction.atomic
def delete_entry(*, entry: TimeEntry, actor: User) -> None:
    entry = _lock_entry(entry)
    _ensure_editable(entry=entry, actor=actor)
    organization_id, entry_id, user_id = entry.organization_id, entry.pk, entry.user_id
    entry.delete()
    publish_on_commit(
        organization_id,
        ActivityEvent.ENTRY_DELETED,
        lambda: {"entry_id": entry_id, "user_id": user_id},
    )


def stop_stale_timers(
    *,
    now: datetime | None = None,
    max_duration: timedelta | None = None,
) -> int:
    now = now or timezone.now()
    max_duration = max_duration or settings.TIMER_AUTO_STOP_AFTER
    stopped = 0
    with transaction.atomic():
        stale_entries = (
            TimeEntry.objects.select_for_update(skip_locked=True, of=("self",))
            .select_related("project", "project__client", "user")
            .running()
            .filter(started_at__lte=now - max_duration)
        )
        for entry in stale_entries:
            entry.ended_at = entry.started_at + max_duration
            _persist(entry)
            _publish(entry, ActivityEvent.TIMER_STOPPED)
            stopped += 1
    return stopped
